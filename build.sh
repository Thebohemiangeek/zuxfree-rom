#!/usr/bin/env bash
# ZUXFree ROM - reproducible build.
# Produces a debloated, testkey-signed, flashable EDL package from a clean stock
# base, by PURE file-level removal (never touches framework.jar / services.jar).
#
# Proven on: TB322FC ZUXOS 1.5.10.259 (A16), 2026-11-01. Static-validated (V1-V12).
# Re-base to A17: synthesise a clean A17 base with `dynobox apply <OTA> ...` and
# point BASE at it; the manifest + pipeline carry over (re-run validate_manifest.py).
#
# Usage: ./build.sh [vanilla|gapps|optional]
set -euo pipefail
VARIANT="${1:-vanilla}"

# ---- paths (override via env) ----
ROOT="${ZX_ROOT:-/c/Users/thebo/Y700-root}"
DYNOBOX="${ZX_DYNOBOX:-$ROOT/dynobox/dynobox.exe}"
BASE="${ZX_BASE:-$ROOT/stock/extracted/image}"      # clean stock EDL dir (A16 259; swap for clean A17)
ABL="${ZX_ABL:-$ROOT/untrusted/korean-rev11/abl.elf}" # testkey abl (trusts AVB key 2597c218)
REPO="${ZX_REPO:-/c/Users/thebo/projects/zuxfree-rom}"
OUT="${ZX_OUT:-$ROOT/build/out_zuxfree}"
PKG="${ZX_PKG:-$ROOT/build/zuxfree_259_$VARIANT}"
KEY="${ZX_KEY:-testkey_rsa4096}"   # DynoBox embedded testkey; pubkey sha1 == 2597c218 == abl-trusted

# ---- manifest (vanilla + optional variant overlays) ----
DEBLOAT="$REPO/manifest/debloat.txt"
TMP_DEBLOAT="$OUT.debloat.txt"
mkdir -p "$(dirname "$TMP_DEBLOAT")"
cat "$DEBLOAT" > "$TMP_DEBLOAT"
[ "$VARIANT" = "gapps" ]    && cat "$REPO/manifest/variants/gapps.txt"    >> "$TMP_DEBLOAT"
[ "$VARIANT" = "optional" ] && cat "$REPO/manifest/variants/optional.txt" >> "$TMP_DEBLOAT"

echo "== 0. validate manifest against the base's blobs.txt =="
python -I "$REPO/tools/validate_manifest.py" "$ROOT/build/inv/blobs.txt" "$TMP_DEBLOAT"

echo "== 1. unpack -> debloat -> testkey resign -> repack =="
# NOTE: no --fuck-lgsi / --system-spl / --vendor-spl : code stays byte-identical to stock.
# No --rollback here (skipped on non-interactive stdin anyway); rollback_index_location=0
# is produced by DynoBox automatically. Set the rollback VALUE at flash-prep if desired.
rm -rf "${OUT:?}"
MSYS_NO_PATHCONV=1 "$DYNOBOX" unpack -i "$BASE" -o "$OUT" \
  --resign --repack -k "$KEY" -a SHA256_RSA4096 \
  --debloat "$TMP_DEBLOAT" < /dev/null

echo "== 2. assemble flashable package =="
rm -rf "${PKG:?}"; mkdir -p "${PKG:?}"
LINK="cp -l"; cp -l "$OUT/vbmeta.img" "$PKG/_t" 2>/dev/null && rm -f "${PKG:?}/_t" || LINK="cp"
# baseline: stock firmware (QC bootloaders/modem, GPT, metadata, userdata, lenovo*, loader, patch, rawprogram1-5)
$LINK "$BASE"/*.img "$BASE"/*.mbn "$BASE"/*.elf "$BASE"/*.bin "$BASE"/*.melf "$BASE"/*.fv "$BASE"/*.xml "$PKG"/ 2>/dev/null || true
# overwrite with our resigned/debloated images
for f in boot.img dtbo.img init_boot.img pvmfw.img recovery.img vendor_boot.img \
         vbmeta.img vbmeta_system.img super_1.img super_2.img super_3.img super_4.img \
         super_5.img super_6.img super_7.img super_8.img; do
  rm -f "${PKG:?}/${f:?}"; $LINK "$OUT/$f" "$PKG/$f"
done
# testkey abl (the piece that boots testkey vbmeta on a locked bootloader)
rm -f "${PKG:?}/abl.elf"; $LINK "$ABL" "$PKG/abl.elf"
# LUN0 rawprogram: persist-preserve variant (skips persist/proinfo/lock/frp/keystore/ssd)
rm -f "${PKG:?}/rawprogram_unsparse0.xml" "${PKG:?}/rawprogram_save_persist_unsparse0.xml"
cp "$OUT/rawprogram_save_persist_unsparse0.xml" "$PKG/rawprogram_unsparse0.xml"
# persist.img is left on disk but is NOT referenced by the active rawprogram (filename="")
rm -f "${PKG:?}/persist.img"

echo "== 3. checksums =="
( cd "$PKG" && sha256sum * > SHA256SUMS.txt )

echo "== 4. validate =="
python -I "$REPO/tools/validate.py" "$OUT" "$PKG" "$BASE" "$ABL"

echo "DONE: $PKG  ($(du -sh "$PKG" | cut -f1))"
