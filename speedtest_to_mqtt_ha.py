#!/usr/bin/env python3
import subprocess
import json
import paho.mqtt.client as mqtt
import os
import time
import requests
from paho.mqtt.client import CallbackAPIVersion
from datetime import datetime

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
    # Parse the UTC ISO timestamp from Speedtest
    utc_time = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

    # Convert to local system time (respects TZ env variable)
    local_time = utc_time.astimezone()  # ← no arguments = use system local time
    local_time_str = local_time.strftime("%d/%m/%Y %H:%M:%S %Z")

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
        "image_url": data["result"]["url"] + ".png",
        "timestamp": local_time_str  # ISO string in system timezone
    }

def publish_discovery(client, sensor_id, name, unit, icon, value_template):
    object_id = f"{DEVICE_NAME}_{sensor_id}"
    unique_id = f"{DEVICE_NAME}_{sensor_id}"
    topic = f"{DISCOVERY_PREFIX}/sensor/{DEVICE_NAME}/{sensor_id}/config"
    payload = {
        "name": f"Speedtest {name}",
        "object_id": object_id,
        "state_topic": f"{SENSOR_PREFIX}/{sensor_id}",
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

def publish_camera_discovery(client):
    topic = f"{DISCOVERY_PREFIX}/camera/{DEVICE_NAME}/result/config"
    payload = {
        "name": "Speedtest Result Image",
        "unique_id": f"{DEVICE_NAME}_camera",
        "topic": f"{SENSOR_PREFIX}/image",  # not used here, but needed
        "device": {
            "identifiers": [DEVICE_NAME],
            "name": DEVICE_NAME.replace("_", " ").title(),
            "manufacturer": DEVICE_MANUFACTURER,
            "model": DEVICE_MODEL
        }
    }
    client.publish(topic, json.dumps(payload), retain=True)    

def publish_camera_image(client, image_url):
    try:
        response = requests.get(image_url)
        response.raise_for_status()
        image_data = response.content  # binary data
        client.publish(f"{SENSOR_PREFIX}/image", image_data, retain=False)
    except Exception as e:
        print(f"Failed to download or publish image: {e}")
        
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

def printEnvVars():
    print(f"MQTT_BROKER_HOST: {MQTT_BROKER_HOST}")
    print(f"MQTT_BROKER_PORT: {MQTT_BROKER_PORT}")
    print(f"MQTT_USERNAME: {MQTT_USERNAME}")
    print(f"MQTT_PASSWORD: {MQTT_PASSWORD}")
    print(f"DISCOVERY_PREFIX: {DISCOVERY_PREFIX}")
    print(f"SENSOR_PREFIX: {SENSOR_PREFIX}")
    print(f"DEVICE_MANUFACTURER: {DEVICE_MANUFACTURER}")
    print(f"DEVICE_MODEL: {DEVICE_MODEL}")
    print(f"DEVICE_NAME: {DEVICE_NAME}")
    print(f"TZ: {os.getenv('TZ')}")    

def run_once():
    printEnvVars()
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
        publish_discovery(client, "external_ip", "External IP", None, "mdi:ip-network", "{{ value }}")
        publish_discovery(client, "isp", "ISP", None, "mdi:access-point-network", "{{ value }}")
        publish_discovery(client, "server", "Server", None, "mdi:server", "{{ value }}")        
        publish_discovery(client, "timestamp", "Timestamp", None, "mdi:clock", "{{ value }}")
        publish_camera_discovery(client)
        publish_camera_image(client, summary["image_url"])
        publish_values(client, summary)
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    run_once()
