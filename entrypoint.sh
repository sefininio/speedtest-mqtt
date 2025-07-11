#!/bin/sh

: "${CRON_SCHEDULE:?CRON_SCHEDULE is not set. Please define it in the .env file}"

if [ "$TEST_MODE" = "1" ]; then
    echo "🧪 Running in test mode..."
    python3 /app/speedtest_to_mqtt_ha.py
else
    echo "⏱️ Setting up cron schedule: $CRON_SCHEDULE"
    # Write cron job with explicit PATH
    {
        echo "PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"
        echo "$CRON_SCHEDULE python3 /app/speedtest_to_mqtt_ha.py >> /var/log/cron.log 2>&1"
    } > /etc/cron.d/speedtest
    
    chmod 0644 /etc/cron.d/speedtest
    crontab /etc/cron.d/speedtest

    echo "🔁 Starting cron..."
    touch /var/log/cron.log
    cron && tail -f /var/log/cron.log
fi
