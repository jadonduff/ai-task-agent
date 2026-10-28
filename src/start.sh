#!/bin/bash

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99
export DISPLAY=:99   # a11y: moved out of the subshell so the MCP server inherits it

# a11y: start the D-Bus session OUTSIDE the subshell so the desktop AND the MCP server share it
# (env -u DISPLAY: dbus-launch shouldn't try to talk to X before Xvfb is up)
eval "$(env -u DISPLAY dbus-launch --sh-syntax)"
export DBUS_SESSION_BUS_ADDRESS
# a11y: for `docker exec` debugging: source /tmp/dbus.env
echo "export DISPLAY=:99 DBUS_SESSION_BUS_ADDRESS='$DBUS_SESSION_BUS_ADDRESS'" > /tmp/dbus.env

# a11y: turn accessibility on directly on the a11y bus (no dconf needed)
dbus-send --session --print-reply --dest=org.a11y.Bus /org/a11y/bus \
org.freedesktop.DBus.Properties.Set \
string:org.a11y.Status string:IsEnabled variant:boolean:true >/dev/null

# Desktop stack in the background, so it doesn't block the MCP server
(
Xvfb :99 -screen 0 1280x800x24 &

# Wait for the X socket
for i in $(seq 1 50); do
[ -e /tmp/.X11-unix/X99 ] && break
sleep 0.1
done

# XFCE (a11y: dbus-launch now happens above)
startxfce4 &

# ---- Custom Wallpaper ------------------------------------------
WALLPAPER="/usr/share/backgrounds/ata-wallpaper.png"

# Wait for XFCE's desktop manager
for i in $(seq 1 50); do
pgrep -x xfdesktop >/dev/null && break
sleep 0.1
done

if [ -f "$WALLPAPER" ] && pgrep -x xfdesktop >/dev/null; then
xfconf-query -c xfce4-desktop \
-p /backdrop/screen0/monitorscreen/workspace0/last-image \
-t string -s "$WALLPAPER" --create

xfconf-query -c xfce4-desktop \
-p /backdrop/screen0/monitorscreen/workspace0/image-style \
-t int -s 3 --create

# Restart the desktop manager to apply the wallpaper
pkill -x xfdesktop || true
xfdesktop >/tmp/xfdesktop.log 2>&1 &
else
echo "Wallpaper unavailable or XFCE not ready: $WALLPAPER" >&2
fi

# ---- Remote Desktop --------------------------------------------
x11vnc -display :99 -forever -shared -nopw \
-localhost -rfbport 5900 -noxdamage &

websockify --web /usr/share/novnc 6575 localhost:5900 &

wait
) &

cd /app
exec fastmcp run /opt/ai-task-agent/src/main.py \
--transport http --host 0.0.0.0 --port 6574