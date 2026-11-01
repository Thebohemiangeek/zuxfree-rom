# Lessons (why ZUXFree ROM is built the way it is)

## Don't edit code — the framework.jar trap
On the TB322FC (locked bootloader, AVB testkey), two earlier builds that used DynoBox `--fuck-lgsi` (which rewrites LGSI feature registrations inside `system.img/framework/framework.jar`) **bootlooped** — both an aggressive 94-flag edit and a conservative 35-flag one. Device State stayed *locked / secure-boot / no corruption warning*, i.e. **AVB verified fine** — the failure was the OS not completing boot because core framework code had been altered.

A Korean community build ("rev11", A17) on the **same** testkey approach **boots**, because it debloats purely by **removing ext4 directory entries** and keeps `framework.jar`/`services.jar`/APK bytes **100% stock**. That is the rule ZUXFree ROM enforces:

> **Debloat by deleting files. Never patch code.** Validation **V8** fails the build if `framework.jar`/`services.jar` differ from stock by a single byte.

Note: the DeZUXposed/ZUXFree Xposed module toggles the *same* LGSI flags safely — because it does it **at runtime** (app stays, flag flips in memory), not by baking edits into the image. Runtime flag-toggling and firmware flag-patching are **not** the same thing; only the former is safe here.

## Never remove core services
The Xposed `DISABLED_FEATURES` list (67 entries) is a *runtime flag* list and includes core services (`ZuiCore`, `ZuiServiceEngine`, `ZuiOMS`, `ZuiSecurity`, `ZuiFileManager`). Turning a *flag* off is survivable; **deleting the service APK is not** — it bricks boot the same way code edits do. So the ROM manifest removes only genuinely-removable **bloat** apps and guards the core services in `keep.txt`.

## The AVB rollback-index-location fix is free
rev11 documents reverting `vbmeta_system.img`'s own-header `rollback_index_location` to **0** (stock standard) so LTBox EDL doesn't fail its ARB precheck (`err_flash_xiaoxin_arb_floor_unreadable`), while the parent `vbmeta` keeps the `vbmeta_system` chain descriptor at location 2. We confirmed **DynoBox v0.3.4 already produces `rollback_index_location = 0`** (it uses avbtool 1.3.0 internally), with all three hashtree descriptors (system/product/system_ext) + pvmfw and the testkey — so no manual avbtool rebuild is needed. Validation **V3/V4** assert this exact structure.

## Preserve persist
`persist` holds per-device calibration (sensors, Wi-Fi/BT MAC, Widevine keybox). **Never flash a foreign persist.** The rawprogram skips it (`filename=""`). Keeping the device's own persist is also why Netflix L1/HD survived on a testkey build (the keybox lives in persist/TEE, untouched by the AVB re-sign).

## The testkey abl is mandatory
Our images are signed with the AOSP `testkey_rsa4096` (pubkey `2597c218`). A locked bootloader only boots them if the `abl.elf` trusts that key. We ship the community testkey abl (`ff6a3d5b`, keeps Lenovo secure-boot so it runs on the locked BL, but trusts the AOSP testkey for vbmeta). Validation **V6** proves our signing key == the abl-trusted key; **V13** proves the shipped abl is that abl.
