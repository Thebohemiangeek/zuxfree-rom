# ZUXFree ROM

A clean-room, open-source **debloated firmware** for the **Lenovo Legion Y700 Gen 4 (TB322FC)** — the China-only ZUXOS tablet that has no official global ROM.

It removes the Chinese bloatware **at the firmware level** (not just disabling it), keeps the system **English-friendly**, and — unlike a runtime root module — needs no root once flashed. It is built by **pure file removal + testkey re-sign**, so it boots on the **locked bootloader**.

> **Status:** the pipeline is **static-validated** (see [Validation](#validation)) on ZUXOS 1.5.10.259. It has **NOT yet been boot-tested on a device.** Flashing can brick your tablet. See [docs/FLASHING.md](docs/FLASHING.md) and [docs/RECOVERY.md](docs/RECOVERY.md) first.

## Why this works (and the last attempt didn't)

The trap on this device is **editing code**. Patching `framework.jar` (e.g. toggling Lenovo's LGSI feature flags inside the image) **bootloops** a locked/testkey device. ZUXFree ROM therefore debloats **only by deleting APK files/folders in the ext4 images** and never touches `framework.jar` / `services.jar` / any APK bytes — they stay **byte-identical to stock** (enforced by validation check **V8**). Full story in [docs/LESSONS.md](docs/LESSONS.md).

## How CN bloat is removed

Chinese apps ship two ways, both handled at the file level:
- **System service apps** in `/system/priv-app` and `/product` (Baidu location, ZUI Browser, Lenovo Store, Xiaotian, DataMonitor, …)
- **Preinstalled apps** in `/system/preinstall/<App>/` + trigger configs in `/system/etc` (Sogou, Douyin, iQIYI, Youku, Weibo, Kuaishou, NetEase, Bilibili, CapCut-CN, Canva-CN, Migu/Moffice, education, Vantage, LegionZone-CN, …)

The removal list is [`manifest/debloat.txt`](manifest/debloat.txt) (every line validated present in the base), with a [`keep.txt`](manifest/keep.txt) guard that **never** lets a core service (`ZuiCore`, `ZuiServiceEngine`, `ZuiOMS`, `ZuiSecurity`, …) or `TabletUE`/`UDSEngine` be removed.

## Variants
- **vanilla** — debloat only. Get apps from **Aurora Store** / F-Droid. Highest boot confidence, zero Google dependency.
- **gapps** — vanilla + Google (via the companion [`zuxfree-addon`](../zuxfree-addon) module: 7 Google-signed apps from official TB323FU ROW firmware, plus ROW GmsCore/Play), and removes the ZUI installer/DocumentsUI it replaces.
- **optional** — aggressive strip of ZUI stock utilities (Gallery/Notes/Recorder/Weather/Clock/Calendar) for users who prefer Google/Fossify equivalents, plus blocking Lenovo OTA.

### Google / Play — the honest ceiling
On a **testkey-signed, locked-bootloader** build, Play Store sign-in and app install/update **can work**, but **Play Integrity "strong/device" will always fail** (AVB is signed by the AOSP testkey, not an OEM/Google key). So banking / DRM / Integrity-gated apps will not work, and no amount of configuration changes that. We do **not** ship keybox or Integrity-Fix spoofing. If you don't need those apps, **vanilla + Aurora Store** is the cleanest choice.

## Building

Requires: Windows + python 3, `7z`, openssl, and [DynoBox](https://github.com/) v0.3.4; AOSP `avbtool.py` + `testkey_rsa4096.pem` vendored in `tools/`. Point the env vars in `build.sh` at a clean stock base.

```sh
./build.sh vanilla      # or: gapps | optional
```

This runs: validate manifest → `dynobox unpack --resign --repack --debloat` (no code flags) → assemble the flashable EDL package (our debloated `super`/`vbmeta` + the testkey `abl.elf` + stock QC firmware + persist-skip rawprogram) → `SHA256SUMS` → `validate.py`. Images are build artifacts (in `dist/`, git-ignored); only manifests, scripts and docs are versioned.

### Base version
Developed/validated on **1.5.10.259 (Android 16)**. The final target is **A17 (2.5.02.086)**; synthesise a clean A17 base with `dynobox apply <official-OTA> --unpack --resign --repack` onto the 259 base, then re-run with `ZX_BASE` pointed at it (re-validate the manifest — paths can shift between versions).

## Validation

`tools/validate.py` gates any flash. On the 259 build, **all pass**:

| Check | What it proves |
|---|---|
| V1 | DynoBox verify: AVB chain + super layout consistent |
| V3 | `vbmeta_system`: rollback-index-location **0**, SHA256_RSA4096, flags 0, testkey |
| V4 | root `vbmeta` chains `vbmeta_system` at location 2 with the testkey |
| V6 | AOSP `testkey_rsa4096` pubkey == `2597c218` == the key the abl trusts |
| V7 | debloat removed exactly the manifest targets (0 missing) |
| **V8** | **`framework.jar` / `services.jar` byte-identical to stock** (the boot-safety guard) |
| V12 | rawprogram skips `persist`/`proinfo`/`lenovolock`/`frp`/`keystore`/`ssd` |
| V13 | shipped `abl.elf` == the known testkey abl |

## ⚠️ Flashing wipes userdata
A full flash **erases all user data** (the rawprogram writes a fresh `userdata`). Your device **persist** (sensor/Wi-Fi-BT-MAC/DRM calibration) is **preserved** (not flashed). Always have the stock-259 EDL recovery package and your data backed up first.

## Related projects
- [`zuxfree`](../zuxfree) — the no-flash root module alternative (systemless debloat)
- [`DeZUXposed`](../DeZUXposed) — ZUXFree Xposed; its `HookConstants.kt` is the feature-selection source
- [`zuxfree-addon`](../zuxfree-addon) — the Google apps add-on used by the GApps variant

## License
MIT. ZUXFree ROM bundles **no** proprietary firmware in this repo — only manifests, scripts and docs. Built images are produced locally from your own stock firmware.
