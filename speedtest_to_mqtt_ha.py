#!/usr/bin/env python3
import subprocess
import json
import paho.mqtt.client as mqtt
import os
import time
from paho.mqtt.client import CallbackAPIVersion

# Config from environment (with defaults)
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

DISCOVERY_PREFIX = os.getenv("DISCOVERY_PREFIX", "homeassistant")
SENSOR_PREFIX = os.getenv("SENSOR_PREFIX", "home/internet/speedtest")
DEVICE_MANUFACTURER = os.getenv("DEVICE_MANUFACTURER", "Ookla + MQTT")
DEVICE_MODEL = os.getenv("DEVICE_MODEL", "Speedtest CLI")
DEVICE_NAME = os.getenv("DEVICE_NAME", "speedtest_sensor")

def bytes_to_mbps(bytes_per_sec):
    return round((bytes_per_sec * 8) / 1_000_000, 2)

def run_speedtest():
    try:
        result = subprocess.run(["speedtest", "--format=json"], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Speedtest failed!")
        print(f"Exit code: {e.returncode}")
        print("STDOUT:")
        print(e.stdout.strip())
        print("STDERR:")
        print(e.stderr.strip())
        return None

def extract_summary(data):
    return {
        "ping_ms": round(data["ping"]["latency"], 2),
        "jitter_ms": round(data["ping"]["jitter"], 2),
        "download_mbps": bytes_to_mbps(data["download"]["bandwidth"]),
        "upload_mbps": bytes_to_mbps(data["upload"]["bandwidth"]),
        "packet_loss": data.get("packetLoss", 0),
        "external_ip": data["interface"]["externalIp"],
        "isp": data["isp"],
        "server": data["server"]["name"],
        "result_url": data["result"]["url"],
        "image_url": data["result"]["url"] + ".png"
    }

def publish_discovery(client, sensor_id, name, unit, icon, value_template):
    object_id = f"{DEVICE_NAME}_{sensor_id}"
    unique_id = f"{DEVICE_NAME}_{sensor_id}"
    topic = f"{DISCOVERY_PREFIX}/sensor/{DEVICE_NAME}/{sensor_id}/config"
    payload = {
        "name": f"Speedtest {name}",
        "object_id": object_id,
        "state_topic": f"{SENSOR_PREFIX}/{s§ensor_id}",
        "unit_of_measurement": unit,
        "value_template": value_template,
        "unique_id": unique_id,
        "device": {
            "identifiers": [DEVICE_NAME],
            "name": DEVICE_NAME.replace("_", " ").title(),
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL
        },
        "icon": icon
    }
    client.publish(topic, json.dumps(payload), retain=True)

def publish_values(client, summary):
    for key, value in summary.items():
        if isinstance(value, (int, float, str)):
            client.publish(f"{SENSOR_PREFIX}/{key}", value, retain=True)

def connect_mqtt():
    client = mqtt.Client(protocol=mqtt.MQTTv311, callback_api_version=CallbackAPIVersion.VERSION2)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    return client

def run_once():
    result = run_speedtest()
    if result:
        summary = extract_summary(result)
        print(summary)
        client = connect_mqtt()
        client.loop_start()
        publish_discovery(client, "ping_ms", "Ping", "ms", "mdi:speedometer", "{{ value }}")
        publish_discovery(client, "jitter_ms", "Jitter", "ms", "mdi:chart-bell-curve", "{{ value }}")
        publish_discovery(client, "download_mbps", "Download", "Mbps", "mdi:download-network", "{{ value }}")
        publish_discovery(client, "upload_mbps", "Upload", "Mbps", "mdi:upload-network", "{{ value }}")
        publish_discovery(client, "packet_loss", "Packet Loss", "%", "mdi:percent", "{{ value }}")
        publish_discovery(client, "result_image_url", "Result Image URL", None, "mdi:image", "{{ value }}")
        publish_values(client, summary)
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run_once()
