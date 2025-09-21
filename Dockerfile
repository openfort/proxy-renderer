# Use Python slim base for smaller image size
FROM python:3.12-slim

# Set environment variables to reduce Python output
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install FFmpeg and required packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        build-essential \
        libssl-dev \
        libffi-dev \
        python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install va media driver for intel
RUN apt-get update && \
    apt-get install -y \
        intel-media-va-driver \
        vainfo && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app
RUN mkdir -p /app/RAW_Data

# Copy your app
COPY proxy_renderer.py .

# Default command (replace with your script)
CMD ["python", "proxy_renderer.py"]