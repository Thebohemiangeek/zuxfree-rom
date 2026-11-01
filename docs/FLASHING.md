# Flashing (EDL)

> ⚠️ **Not yet boot-tested on a device.** The build passes full static validation, but has **not** been proven to boot on real hardware. Flashing an unproven image can **brick** your tablet. Do not flash your only/daily device until an independent clean boot has been reported. Always stage the stock-259 recovery first ([RECOVERY.md](RECOVERY.md)).

> ⚠️ **A full flash ERASES all user data.** Back up everything. Your device **persist** (calibration/DRM) is preserved (not flashed).

## Prerequisites
- Windows PC with the Qualcomm **HS-USB QDLoader 9008** driver installed.
- **LTBox v3.3.5** (or QFIL) for EDL flashing.
- The built package dir (`dist/zuxfree_<ver>_<variant>/`) + its `SHA256SUMS.txt` — verify the hashes first.
- Loader/programmer: `xbl_s_devprg_ns.melf` (in the package).

## Steps
1. **Back up** your data; keep the stock-259 EDL package + stock `abl.elf` ready for recovery.
2. Enter **EDL** (9008): power the tablet off, then hold the right keys / use the side USB-C port until `Qualcomm HS-USB QDLoader 9008` appears as a COM port. (If the tablet is bootlooping, force it off with Power+Vol-Down ~20 s first.)
3. In LTBox → **Flash Firmware** (full ROM): Region **PRC**, Target **matching-region**, Country **do-not-change**, Folder = the package dir. It reads `rawprogram_unsparse0.xml` (persist-skip) + `rawprogram1..5.xml` + `patch0..5.xml`.
4. Confirm the plan writes **super / vbmeta / vbmeta_system / boot / abl / userdata / metadata / lenovoraw / lenovocust / GPT** and **skips persist / proinfo / lenovolock / frp / keystore / ssd**.
5. Flash. First boot of a fresh build can take **5–10 minutes** (userdata format). Don't assume a bootloop before then.

## After first boot
- vanilla: install **Aurora Store** (anonymous or your Google account) for apps.
- gapps: flash the `zuxfree-addon` module; expect Play Store to work for installs but **Play Integrity strong/device to fail** (see README).
- Disable Lenovo OTA (an OTA can break the modified build), or use the `optional` variant which removes it.

## GApps / fingerprint note
The GApps variant may spoof the TB323FU ROW fingerprint to improve Play check-in. This presents a China device as a global model — a deliberate trade-off for Google compatibility, documented so you can choose the vanilla variant instead.
