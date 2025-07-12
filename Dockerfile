FROM python:3.9-slim

# Install required packages
RUN apt-get update && \
    apt-get install -y curl cron gnupg ca-certificates && \
    apt-get clean

# Install speedtest-cli from Ookla repo
RUN curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash && \
    apt-get install -y speedtest

# Accept Ookla license and GDPR to prevent blocking
RUN speedtest --accept-license --accept-gdpr > /dev/null || true

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY speedtest_to_mqtt_ha.py /app/speedtest_to_mqtt_ha.py
COPY crontab.txt /app/crontab.txt

WORKDIR /app

ENTRYPOINT ["python3", "/app/speedtest_to_mqtt_ha.py"]
