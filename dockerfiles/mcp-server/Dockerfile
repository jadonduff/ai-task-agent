# Container Image
FROM ubuntu:24.04

# Set as noninteractive
ENV DEBIAN_FRONTEND=noninteractive
ENV DISPLAY=:99

# Install packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    build-essential \
    cmake \
    git \
    xvfb \
    x11vnc \
    openbox \
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create virtual environment
RUN python3.12 -m venv /opt/venv

# Use the virtual environment by default
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir fastmcp==4.0.10

# Copy over code
COPY src ./src
COPY dockerfiles/mcp-server/start.sh /start.sh
RUN chmod +x /start.sh
# Ports
EXPOSE 6574 6576

# Initialization
CMD ["/start.sh"]