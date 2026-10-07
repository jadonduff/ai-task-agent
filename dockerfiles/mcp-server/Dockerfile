# Container Image
FROM ubuntu:24.04

# Set as noninteractive
ENV DEBIAN_FRONTEND=noninteractive

# Install packages
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    build-essential \
    cmake \
    git \
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

# Ports
EXPOSE 6574

# Initialization
CMD ["fastmcp", "run", "src/backend/mcp_server.py", "--transport", "http", "--host", "0.0.0.0", "--port", "6574"]
