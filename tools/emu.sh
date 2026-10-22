#!/usr/bin/env bash
# Emulator helpers.  tools/emu.sh install <apk> | shot <name> | keys <keycode...> | home
set -e
E="adb -s ${EMU:-emulator-5554}"
PKG="${PKG:-local.guangying.tv}"
SHOTS="$(dirname "$0")/../shots"
case "$1" in
  install) $E install -r "$2" | tail -1 ;;
  home) $E shell am force-stop $PKG
        $E shell am start -n $PKG/com.fongmi.android.tv.ui.activity.HomeActivity >/dev/null
        sleep "${2:-8}" ;;
  keys) shift; for k in "$@"; do $E shell input keyevent "$k"; sleep 0.35; done ;;
  shot) sleep "${3:-1.5}"; mkdir -p "$SHOTS/$(dirname "$2")"; $E exec-out screencap -p > "$SHOTS/$2.png"; echo "$SHOTS/$2.png" ;;
  crash) $E logcat -d -b crash | tail -40 ;;
esac
