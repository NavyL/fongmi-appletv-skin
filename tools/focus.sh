#!/usr/bin/env bash
# tools/focus.sh <text> <keycode>: press <keycode> until the view with <text> has focus (max 14 presses).
E="adb -s ${EMU:-emulator-5554}"; export MSYS_NO_PATHCONV=1
for i in $(seq 1 14); do
  $E shell uiautomator dump /sdcard/ui.xml >/dev/null 2>&1
  if $E shell cat /sdcard/ui.xml | tr '>' '\n' | grep "text=\"$1\"" | grep -q 'focused="true"'; then exit 0; fi
  $E shell input keyevent $2; sleep 0.4
done
echo "focus: miss $1"
