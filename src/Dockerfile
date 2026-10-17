# Container Image
FROM ubuntu:24.04

# Set as noninteractive
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install packages
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    ca-certificates \
    xvfb \
    x11vnc \
    xdotool \
    wmctrl \
    scrot \
    novnc \
    websockify \
    xfce4 \
    xfce4-terminal \
    thunar \
    mousepad \
    dbus-x11 \
    fonts-dejavu \
    xdg-utils \
    libmagic1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download Firefox
RUN install -d -m 0755 /etc/apt/keyrings \
&& wget -q https://packages.mozilla.org/apt/repo-signing-key.gpg -O /etc/apt/keyrings/packages.mozilla.org.asc \
&& echo "deb [signed-by=/etc/apt/keyrings/packages.mozilla.org.asc] https://packages.mozilla.org/apt mozilla main" > /etc/apt/sources.list.d/mozilla.list \
&& printf 'Package: *\nPin: origin packages.mozilla.org\nPin-Priority: 1000\n' > /etc/apt/preferences.d/mozilla \
&& apt-get update \
&& apt-get install -y --allow-downgrades firefox \
&& apt-get clean && rm -rf /var/lib/apt/lists/*

# Set working directory for code
WORKDIR /opt/ai-task-agent

# Create virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/ai-task-agent"

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Download Playwright browsers and OS dependencies
RUN playwright install --with-deps chromium

# Copy over code
COPY src/ /opt/ai-task-agent/src/
COPY src/start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh

COPY src/assets/wallpaper.png /usr/share/backgrounds/ata-wallpaper.png

# Shared directory
RUN mkdir -p /app/transfer

# Scratch directory
RUN mkdir -p /app/scratch

# Brain directory
RUN mkdir -p /root/brain

# Where Agent spawns
WORKDIR /app

# Ports
EXPOSE 6574 6575

# Initialization
CMD ["/start.sh"]