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

# Set working directory for code
WORKDIR /opt/ai-task-agent

# Create virtual environment
RUN python3.12 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/opt/ai-task-agent"

# Use the virtual environment by default
ENV PATH="/opt/venv/bin:$PATH"

# Install Python packages
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Copy over code
COPY src/ /opt/ai-task-agent/src/
COPY src/start.sh /start.sh
RUN sed -i 's/\r$//' /start.sh && chmod +x /start.sh

# Shared directory
RUN mkdir -p /app/transfer

# Where Agent spawns
WORKDIR /app

# Ports
EXPOSE 6574 6575

# Initialization
CMD ["/start.sh"]