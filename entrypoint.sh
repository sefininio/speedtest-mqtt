#!/bin/sh

CRON_SCHEDULE="${CRON_SCHEDULE:-0 */3 * * *}"  # every 3 hours by default

if [ "$TEST_MODE" = "1" ]; then
    echo "🧪 Running in test mode..."
    python3 /app/speedtest_to_mqtt_ha.py
else
    echo "⏱️ Setting up cron schedule: $CRON_SCHEDULE"
    echo "$CRON_SCHEDULE root python3 /app/speedtest_to_mqtt_ha.py >> /var/log/cron.log 2>&1" > /etc/cron.d/speedtest
    chmod 0644 /etc/cron.d/speedtest
    crontab /etc/cron.d/speedtest

    echo "🔁 Starting cron..."
    touch /var/log/cron.log
    cron && tail -f /var/log/cron.log
fi
