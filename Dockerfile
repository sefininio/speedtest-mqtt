FROM alpine:latest

# ✅ Replace with appropriate architecture URL if needed
ENV SPEEDTEST_URL=https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz

RUN apk add --no-cache python3 py3-pip curl tar \
 && pip install --no-cache-dir paho-mqtt \
 && curl -Lo speedtest.tgz $SPEEDTEST_URL \
 && tar -xzf speedtest.tgz -C /usr/local/bin --strip-components=1 \
 && chmod +x /usr/local/bin/speedtest \
 && rm speedtest.tgz

COPY speedtest_to_mqtt_ha.py /app/
WORKDIR /app

ENTRYPOINT ["python3", "/app/speedtest_to_mqtt_ha.py"]
