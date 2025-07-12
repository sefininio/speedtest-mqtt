#!/bin/sh

: "${CRON_SCHEDULE:?CRON_SCHEDULE is not set. Please define it in the .env file}"

if [ "$TEST_MODE" = "1" ]; then
    echo "🧪 Running in test mode..."
    python3 /app/speedtest_to_mqtt_ha.py
else
    echo "⏱️ Setting up cron schedule: $CRON_SCHEDULE"

    # Dump current env to a file for cron to use
    printenv | grep -v "^\(HOME\|PWD\|PATH\)=" > /env-vars.sh
    echo "" >> /env-vars.sh
    echo "python3 /app/speedtest_to_mqtt_ha.py >> /var/log/cron.log 2>&1" >> /env-vars.sh
    chmod +x /env-vars.sh

    # Write cron job with explicit PATH
    {
        echo "SHELL=/bin/sh"
        echo "PATH=/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin"
        echo "$CRON_SCHEDULE . /env-vars.sh"
    } > /etc/cron.d/speedtest
    
    chmod 0644 /etc/cron.d/speedtest
    crontab /etc/cron.d/speedtest

    echo "🔁 Starting cron..."
    touch /var/log/cron.log
    cron && tail -f /var/log/cron.log
fi
