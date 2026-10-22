# fongmi-skin → 光影

tvOS-style skin for FongMi TV, applied to the official release APK and shipped as its own app:
**光影** (`local.guangying.tv`), installable next to the official 影视 (`com.fongmi.android.tv`).
Only resources change, plus one patched string: tools/patch_dex.py points the self-update URL at an
unresolvable host (update check off). Native libs and assets are copied untouched.

    python -I tools/build.py --version 5.8.0 --abi armeabi_v7a   # -> out/guangying-5.8.0-armeabi_v7a.apk
    python -I tools/build.py --version 5.8.0 --plain             # round-trip without the skin

- `skin/res/` — the overlay. `values/*.xml` merge by resource name; other folders replace files by name.
- `tools/check_ids.py` — a replaced layout must keep every upstream view id with the same class (ViewBinding).
- `tools/gen_wallpapers.py` — draws `wallpaper_1..4.webp` (1 = dusk dunes, the default).
- `tools/gen_rows.py` — generates the settings/dialog layouts from upstream's (marked GENERATED); re-run it after a version bump.
- `skin/res/font/` — Inter Text/Display (OFL, `FONT-LICENSE-OFL.txt`), Latin subset ~1.2 MB; theme default weight 500 like tvOS, CJK falls back to the system font.
- `skin/brand.json` — app identity applied by build.py: package, provider authorities, signature permission,
  label (`strings_brand.xml`), FFalcon cyberui card (`beidouui_icon` meta-data → `skin/assets/card_guangying.png`).
- `tools/gen_brand.py` — draws icon layers, banner, card, in-app logo (needs `work/fonts/NotoSansSC.ttf`, OFL, from google/fonts).
- `tools/gen_icons.py` — UI glyphs → Material Symbols Rounded (Apache 2.0, `NOTICE-material-symbols.txt`); run by hand, output committed.
- `tools/gen_type.py` — Material 3 type scale → Inter; `build.py` runs it and `gen_rows.py` on every build.
- `tools/unclip.py` — containers don't clip growing focused controls, except direct parents of scrolling lists.
- Screen open = in-app content fade (`anim/tvos_screen_enter`): Android 12+ TV builds ignore app window animations.
- `tools/gen_selectors.py` — five-state selectors (disabled/pressed/focused/current/rest) and press animators.
- Dialogs/sheets blur what is behind them on Android 12+ (`windowBlurBehind`); older TVs get a near-opaque panel.
- `keys/skin.jks` — signing key (backup in `E:\tv\backup\skin-key\`). Same key = in-place upgrades.

Upgrade: `build.py --version <new>` (decodes upstream and regenerates derived layouts/styles);
if check_ids fails, sync that hand-written layout with upstream.
Move data from the official app with FongMi's own 设置 → 备份 / 恢复 (`/sdcard/TV/backup`, shared by both).
Signed with our own key, so FongMi's runtime modules (`com.fongmi.runtime.*`) can't be installed.
