# fongmi-skin

tvOS-style skin for FongMi TV (影视, `com.fongmi.android.tv`), applied to the official release APK.
Only resources change; FongMi's code (`classes*.dex`), native libs and assets are copied untouched.

    python -I tools/build.py --version 5.8.0 --abi armeabi_v7a   # -> out/fongmi-skin-5.8.0-armeabi_v7a.apk
    python -I tools/build.py --version 5.8.0 --plain             # round-trip without the skin

- `skin/res/` — the overlay. `values/*.xml` merge by resource name; other folders replace files by name.
- `tools/check_ids.py` — a replaced layout must keep every upstream view id with the same class (ViewBinding).
- `tools/gen_wallpapers.py` — draws `wallpaper_1..4.webp` (1 = dusk dunes, the default).
- `tools/gen_rows.py` — generates the settings/dialog layouts from upstream's (marked GENERATED); re-run it after a version bump.
- `skin/res/font/` — Inter Text/Display (OFL, `FONT-LICENSE-OFL.txt`), Latin subset ~1.2 MB; theme default weight 500 like tvOS, CJK falls back to the system font.
- `tools/gen_selectors.py` — five-state selectors (disabled/pressed/focused/current/rest) and press animators.
- Dialogs/sheets blur what is behind them on Android 12+ (`windowBlurBehind`); older TVs get a near-opaque panel.
- `keys/skin.jks` — signing key (backup in `E:\tv\backup\skin-key\`). Same key = in-place upgrades.

Upgrade: `build.py --version <new>` once (decodes upstream), `gen_rows.py --base work/<new>-<abi>/base/res`, then `build.py` again;
if check_ids fails, sync that hand-written layout with upstream.
Signed with our own key, so FongMi's runtime modules (`com.fongmi.runtime.*`) can't be installed.
