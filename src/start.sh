#!/bin/bash

rm -f /tmp/.X99-lock /tmp/.X11-unix/X99

# Desktop stack in the background, so it doesn't block the MCP server
(
    export DISPLAY=:99

    Xvfb :99 -screen 0 1280x800x24 &

    # Wait for the X socket
    for i in $(seq 1 50); do
        [ -e /tmp/.X11-unix/X99 ] && break
        sleep 0.1
    done

    # Start a shared D-Bus session and XFCE
    eval "$(dbus-launch --sh-syntax)"
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