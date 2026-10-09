#!/bin/bash
rm -f /tmp/.X99-lock /tmp/.X11-unix/X99

# Desktop stack in the background, so it doesn't block the MCP server
(
  Xvfb :99 -screen 0 1280x800x24 &

  # Wait for the X socket (no extra packages needed)
  for i in $(seq 1 50); do
    [ -e /tmp/.X11-unix/X99 ] && break
    sleep 0.1
  done

  dbus-launch startxfce4 &
  x11vnc -display :99 -forever -shared -nopw -localhost -rfbport 5900 -noxdamage &
  websockify --web /usr/share/novnc 6575 localhost:5900 &
  wait
) &

cd /app
exec fastmcp run /opt/ai-task-agent/src/main.py \
  --transport http --host 0.0.0.0 --port 6574