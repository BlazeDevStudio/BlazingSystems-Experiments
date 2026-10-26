#!/bin/sh
# Runs only on this R281's CP. No flash writes; signal LED service is resumed on restore.
set -eu
S=/tmp/blaze-led-state
restore(){
 [ -d "$S" ] || return 0
 for i in 1 2 3;do
  D=/sys/class/leds/led_signal$i
  echo none >"$D/trigger"
  cat "$S/b$i" >"$D/brightness"
  cat "$S/t$i" >"$D/trigger"
 done
 for p in $(cat "$S/pids");do
  [ "$(cat /proc/$p/comm 2>/dev/null || true)" != led_module ] || kill -CONT "$p"
 done
 rm -rf /tmp/blaze-led-state
}
for i in 1 2 3;do test -f /sys/class/leds/led_signal$i/brightness;done
case "${1:-}" in
 native) restore;echo BLAZELED:native;exit 0;;
 expire) [ "$(cat "$S/token" 2>/dev/null || true)" != "$2" ] || restore;exit 0;;
 signal|dance) ;;
 *) exit 2;;
esac
case "$2:$3" in *[!0-9:]*|:) exit 2;;esac
[ "$2" -le 3 ] && [ "$3" -le 86400 ]
case "$4" in ''|*[!a-f0-9-]*) exit 2;;esac
umask 077
if [ ! -d "$S" ];then
 mkdir "$S"
 for i in 1 2 3;do D=/sys/class/leds/led_signal$i;cat "$D/brightness" >"$S/b$i";sed -n 's/.*\[\([^]]*\)\].*/\1/p' "$D/trigger" >"$S/t$i";done
 pidof led_module >"$S/pids" || true
fi
for p in $(cat "$S/pids");do [ "$(cat /proc/$p/comm 2>/dev/null || true)" != led_module ] || kill -STOP "$p";done
printf '%s' "$4" >"$S/token"
if [ "$3" -gt 0 ];then (sleep "$3";sh "$0" expire "$4") </dev/null >/dev/null 2>&1 & fi
for i in 1 2 3;do
 D=/sys/class/leds/led_signal$i
 echo none >"$D/trigger"
 if [ "$1" = dance ];then
  echo timer >"$D/trigger";echo $((71+i*47)) >"$D/delay_on";echo $((101+i*61)) >"$D/delay_off"
 else
  if [ "$i" -le "$2" ];then echo 1 >"$D/brightness";else echo 0 >"$D/brightness";fi
 fi
done
echo BLAZELED:$1
