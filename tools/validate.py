#!/usr/bin/env python3
"""ZUXFree ROM static validator.

Runs the offline checks that gate whether a build may ever be flashed. Exits
non-zero on any failure. Run with python -I.

Usage:
  python -I validate.py <out_dir> <pkg_dir> <base_dir> <abl_path> \
         [--our-system system.img --stock-system system.img]

<out_dir>  DynoBox resign/repack output (vbmeta.img, vbmeta_system.img, super_*)
<pkg_dir>  assembled flashable package (rawprogram*.xml, abl.elf, SHA256SUMS.txt)
<base_dir> clean stock base (for reference)
<abl_path> the testkey abl that will be shipped

V1  super/AVB consistency ...... via DynoBox verify during repack (build-time)
V3  vbmeta_system own-header .... location 0, SHA256_RSA4096, flags 0, key 2597c218
V4  vbmeta chain ............... vbmeta_system descriptor at location 2, key 2597c218
V6  key identity ............... AOSP testkey_rsa4096 pubkey == 2597c218 (abl-trusted)
V8  code byte-identity ......... framework.jar/services.jar == stock (needs --our/--stock-system)
V12 rawprogram destructive audit  persist/proinfo/lenovolock/frp/keystore skipped
V13 abl identity ............... shipped abl sha256 == expected testkey abl
Completeness ................... every rawprogram-referenced file exists in pkg
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AVBTOOL = os.path.join(HERE, "avbtool.py")
TESTKEY = os.path.join(HERE, "testkey_rsa4096.pem")
EXPECT_KEY_SHA1 = "2597c218aae470a130f61162feaae70afd97f011"
EXPECT_ABL_SHA256 = "ff6a3d5b0a365881c3a187ea45c6a1c8785194dbd39488e9485f2255c35a7dbd"
SKIP_PARTITIONS = ["persist", "proinfo", "lenovolock", "frp", "keystore", "ssd"]

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}  {detail}")


def avb_info(img):
    return subprocess.run([sys.executable, "-I", AVBTOOL, "info_image", "--image", img],
                          capture_output=True, text=True).stdout


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(argv):
    if len(argv) < 5:
        print(__doc__)
        return 2
    out_dir, pkg_dir, base_dir, abl = argv[1:5]
    our_sys = stock_sys = None
    if "--our-system" in argv:
        our_sys = argv[argv.index("--our-system") + 1]
    if "--stock-system" in argv:
        stock_sys = argv[argv.index("--stock-system") + 1]

    # V3 - vbmeta_system own header
    info = avb_info(os.path.join(out_dir, "vbmeta_system.img"))
    loc = re.search(r"Rollback Index Location:\s*(\d+)", info)
    key = re.search(r"Public key \(sha1\):\s*([0-9a-f]+)", info)
    algo = "SHA256_RSA4096" in info
    flags0 = re.search(r"Flags:\s*0\b", info)
    check("V3 vbmeta_system rollback_index_location==0", bool(loc and loc.group(1) == "0"),
          f"(got {loc.group(1) if loc else '?'})")
    check("V3 vbmeta_system algorithm SHA256_RSA4096", algo)
    check("V3 vbmeta_system flags==0", bool(flags0))
    check("V3 vbmeta_system key==testkey", bool(key and key.group(1) == EXPECT_KEY_SHA1))

    # V4 - root vbmeta chain
    vinfo = avb_info(os.path.join(out_dir, "vbmeta.img"))
    m = re.search(r"Partition Name:\s*vbmeta_system\s*\n\s*Rollback Index Location:\s*(\d+)\s*\n\s*Public key \(sha1\):\s*([0-9a-f]+)", vinfo)
    check("V4 vbmeta chains vbmeta_system @loc2 w/ testkey",
          bool(m and m.group(1) == "2" and m.group(2) == EXPECT_KEY_SHA1),
          f"(loc={m.group(1) if m else '?'})")

    # V6 - key identity
    tkbin = os.path.join(out_dir, "_tk.bin")
    subprocess.run([sys.executable, "-I", AVBTOOL, "extract_public_key", "--key", TESTKEY,
                    "--output", tkbin], capture_output=True)
    tk = sha256_sha1 = ""
    if os.path.exists(tkbin):
        with open(tkbin, "rb") as f:
            sha256_sha1 = hashlib.sha1(f.read()).hexdigest()
        os.remove(tkbin)
    check("V6 AOSP testkey pubkey == 2597c218 (abl-trusted)", sha256_sha1 == EXPECT_KEY_SHA1,
          f"(got {sha256_sha1[:16]}...)")

    # V12 - rawprogram destructive-write audit (active LUN0 rawprogram)
    rp = os.path.join(pkg_dir, "rawprogram_unsparse0.xml")
    txt = open(rp, encoding="utf-8", errors="replace").read() if os.path.exists(rp) else ""
    for lb in SKIP_PARTITIONS:
        m = re.search(r'<program[^>]*label="%s"[^>]*/?>' % lb, txt)
        fn = re.search(r'filename="([^"]*)"', m.group(0)) if m else None
        skipped = (fn is None) or (fn.group(1) == "")
        if m:  # only assert for partitions actually present in this rawprogram
            check(f"V12 {lb} skipped (filename empty)", skipped,
                  f'(filename="{fn.group(1) if fn else ""}")')

    # V13 - abl identity
    check("V13 shipped abl == rev11 testkey abl", sha256(abl) == EXPECT_ABL_SHA256,
          f"({sha256(abl)[:16]}...)")

    # Completeness - every rawprogram-referenced file exists in pkg
    missing = []
    for xml in os.listdir(pkg_dir):
        if xml.startswith("rawprogram") and xml.endswith(".xml"):
            body = open(os.path.join(pkg_dir, xml), encoding="utf-8", errors="replace").read()
            for fn in set(re.findall(r'filename="([^"]+)"', body)):
                if not os.path.exists(os.path.join(pkg_dir, fn)):
                    missing.append(f"{fn} ({xml})")
    check("Completeness: all rawprogram files present", not missing,
          f"(missing {len(missing)})")
    for m in missing:
        print("      missing:", m)

    # V8 - code byte-identity (optional, needs extracted system images + 7z)
    if our_sys and stock_sys:
        sz = next((p for p in [r"C:\Program Files\7-Zip\7z.exe", "7z", "7za"] if p), "7z")
        for jar in ("framework.jar", "services.jar"):
            ok = True
            hashes = {}
            for tag, img in (("ours", our_sys), ("stock", stock_sys)):
                d = os.path.join(out_dir, f"_v8_{tag}")
                os.makedirs(d, exist_ok=True)
                subprocess.run([sz, "e", img, f"-o{d}", f"system/framework/{jar}", "-y"],
                               capture_output=True)
                fp = os.path.join(d, jar)
                hashes[tag] = sha256(fp) if os.path.exists(fp) else None
            ok = hashes.get("ours") and hashes["ours"] == hashes.get("stock")
            check(f"V8 {jar} byte-identical to stock", bool(ok),
                  f"({(hashes.get('ours') or '?')[:16]}...)")
    else:
        print("  [SKIP] V8 code byte-identity (pass --our-system/--stock-system to run)")

    failed = [n for n, ok, _ in results if not ok]
    print(f"\n{'ALL CHECKS PASSED' if not failed else 'FAILURES: ' + ', '.join(failed)}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
