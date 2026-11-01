# Recovery (restore to stock)

If a ZUXFree build fails to boot, you restore the tablet to **official stock** over EDL. This is always possible as long as the bootloader is intact — which it is, because we never flash untrusted bootloader/XBL (only `abl.elf` is swapped, and recovery re-flashes the stock one).

## You need
- The **official stock EDL package** for your device (e.g. `TB322FC_CN ... 1.5.10.259`), with its own `rawprogram*.xml` / `patch*.xml`, QC firmware, and the **stock `abl.elf`**.
- The loader `xbl_s_devprg_ns.melf`.
- LTBox v3.3.5 / QFIL + the QDLoader 9008 driver.

## Steps
1. Force the tablet off (Power+Vol-Down ~20 s if it's bootlooping) and enter **EDL (9008)**.
2. In LTBox → **Flash Firmware**, point it at the **stock** package folder (not ZUXFree). This re-flashes the stock `abl.elf`, boot, vbmeta(_system) and super, returning the device to a fully signed stock state.
3. Use the stock `rawprogram_save_persist_unsparse0.xml` variant if you want to keep your persist; either way **persist is never overwritten** by the stock recovery flow we recommend.
4. Reboot. First boot after a full stock flash may take several minutes.

## Notes
- Keep a **second copy** of your `persist.img` backup off-device. We never flash it, but having it means a foreign-persist mistake is recoverable.
- Device-unique partitions (`proinfo`, `lenovolock`, `frp`, `keystore`, `sec`, `sn`, `devinfo`) are not written by ZUXFree or by a persist-safe stock restore, so your device identity/calibration is retained.
- If EDL isn't detected: reinstall the Qualcomm QDLoader 9008 driver (kernel/COM mode), try the side USB-C port, and re-enter EDL fresh.
