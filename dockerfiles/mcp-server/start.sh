#!/bin/bash
rm -f /tmp/.X99-lock

Xvfb :99 -screen 0 1280x800x24 &
sleep 2
dbus-launch startxfce4 &
sleep 3
x11vnc -display :99 -forever -shared -nopw -localhost -rfbport 5900 -noxdamage &
websockify --web /usr/share/novnc 6576 localhost:5900 &

exec fastmcp run src/backend/mcp_server.py --transport http --host 0.0.0.0 --port 6574