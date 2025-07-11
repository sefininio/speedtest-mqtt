FROM debian:bullseye-slim

# Speedtest repository installer
ENV DEBIAN_FRONTEND=noninteractive

# Install system and Python dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    ca-certificates \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install Speedtest CLI from Ookla repo
RUN curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash \
 && apt-get update && apt-get install -y speedtest \
 && speedtest --accept-license --accept-gdpr > /dev/null

# Install Python dependencies
RUN pip3 install --no-cache-dir paho-mqtt requests

# Copy your script
COPY speedtest_to_mqtt_ha.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/speedtest_to_mqtt_ha.py"]