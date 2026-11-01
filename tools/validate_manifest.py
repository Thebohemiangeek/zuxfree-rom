#!/usr/bin/env python3
"""Validate a ZUXFree debloat manifest against a DynoBox blobs.txt.

DynoBox's --debloat silently ignores paths that don't exist, so an unvalidated
manifest can be a no-op. This turns that into a hard check: every manifest line
must exist in blobs.txt (as an exact path or a folder prefix of real entries).

Usage:
  python -I validate_manifest.py <blobs.txt> <manifest.txt> [more_manifests...]
Exit code 0 only if every line of every manifest matched.
"""
import sys


def load_blobs(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return [ln.strip() for ln in f if ln.strip()]


def manifest_lines(path):
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for ln in f:
            s = ln.strip()
            if not s or s.startswith("#"):
                continue
            out.append(s)
    return out


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    blobs = load_blobs(argv[1])
    blob_set = set(blobs)
    ok_total = bad_total = 0
    for mf in argv[2:]:
        lines = manifest_lines(mf)
        matched = unmatched = 0
        print(f"\n== {mf} ({len(lines)} entries) ==")
        for ln in lines:
            hit = ln in blob_set or any(b.startswith(ln) for b in blobs)
            if hit:
                matched += 1
            else:
                unmatched += 1
                print(f"  MISSING: {ln}")
        print(f"  matched={matched} missing={unmatched}")
        ok_total += matched
        bad_total += unmatched
    print(f"\nTOTAL matched={ok_total} missing={bad_total}")
    return 0 if bad_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
