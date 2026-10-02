# Container Image
FROM python:3.12

# Set working directory
WORKDIR /app

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
