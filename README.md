# fongmi-skin

tvOS-style skin for FongMi TV (影视, `com.fongmi.android.tv`), applied to the official release APK.
Only resources change; FongMi's code (`classes*.dex`), native libs and assets are copied untouched.

    python -I tools/build.py --version 5.8.0 --abi armeabi_v7a   # -> out/fongmi-skin-5.8.0-armeabi_v7a.apk
    python -I tools/build.py --version 5.8.0 --plain             # round-trip without the skin

- `skin/res/` — the overlay. `values/*.xml` merge by resource name; other folders replace files by name.
- `tools/check_ids.py` — a replaced layout must keep every upstream view id with the same class (ViewBinding).
- `tools/gen_wallpapers.py` — draws `wallpaper_1..4.webp`.
- `keys/skin.jks` — signing key (backup in `E:\tv\backup\skin-key\`). Same key = in-place upgrades.

Upgrade: run build.py with the new `--version`; if check_ids fails, sync that layout with upstream.
Signed with our own key, so FongMi's runtime modules (`com.fongmi.runtime.*`) can't be installed.
