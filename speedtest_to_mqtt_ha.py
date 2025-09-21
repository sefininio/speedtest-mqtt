#!/usr/bin/env python3
import subprocess
import json
import paho.mqtt.client as mqtt
import os
import time
import requests
import threading
from paho.mqtt.client import CallbackAPIVersion
from datetime import datetime

def get_version():
    """Get version from VERSION file created during Docker build"""
    try:
        with open('/app/VERSION', 'r') as f:
            return f.read().strip()
    except:
        return 'unknown'

# Config from environment (with defaults)
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "localhost")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")

DISCOVERY_PREFIX = os.getenv("DISCOVERY_PREFIX", "homeassistant")
SENSOR_PREFIX = os.getenv("SENSOR_PREFIX", "home/internet/speedtest")
COMMAND_TOPIC = os.getenv("COMMAND_TOPIC", "home/internet/speedtest/run")
DEVICE_MANUFACTURER = os.getenv("DEVICE_MANUFACTURER", "Ookla + MQTT")
DEVICE_MODEL = os.getenv("DEVICE_MODEL", "Speedtest CLI")
DEVICE_NAME = os.getenv("DEVICE_NAME", "speedtest_sensor")

# Global variables for threading and MQTT
speedtest_lock = threading.Lock()
last_speedtest_time = 0
mqtt_client = None

def bytes_to_mbps(bytes_per_sec):
    return round((bytes_per_sec * 8) / 1_000_000, 2)

def run_speedtest():
    global last_speedtest_time
    current_time = time.time()
    
    # Prevent running speedtests too frequently (minimum 30 seconds between runs)
    if current_time - last_speedtest_time < 30:
        print(f"⏳ Speedtest skipped - too soon (minimum 30 seconds between runs)")
        return None
    
    with speedtest_lock:
        print(f"Running speedtest...")
        last_speedtest_time = current_time
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

def on_connect(client, userdata, flags, reason_code, properties=None):
    print(f"Connected to MQTT broker with result code {reason_code}")
    # Subscribe to the command topic
    client.subscribe(COMMAND_TOPIC)
    print(f"📡 Subscribed to command topic: {COMMAND_TOPIC}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode()
        print(f"📨 Received message on {topic}: {payload}")
        
        if topic == COMMAND_TOPIC and payload.lower() in ["run", "start", "execute", "go"]:
            print("🚀 Manual speedtest triggered via MQTT command")
            # Run speedtest in a separate thread to avoid blocking
            thread = threading.Thread(target=run_speedtest_and_publish, daemon=True)
            thread.start()
        else:
            print(f"Unknown command or topic: {topic} -> {payload}")
            
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

def connect_mqtt():
    client = mqtt.Client(protocol=mqtt.MQTTv311, callback_api_version=CallbackAPIVersion.VERSION2)
    if MQTT_USERNAME:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Set callbacks
    client.on_connect = on_connect
    client.on_message = on_message
    
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
    return client

def cleanup_mqtt():
    """Clean up MQTT connection and stop loops"""
    global mqtt_client
    if mqtt_client:
        print("🔌 Disconnecting from MQTT broker...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        mqtt_client = None    

def printEnvVars():
    print(f"MQTT_BROKER_HOST: {MQTT_BROKER_HOST}")
    print(f"MQTT_BROKER_PORT: {MQTT_BROKER_PORT}")
    print(f"MQTT_USERNAME: {MQTT_USERNAME}")
    print(f"MQTT_PASSWORD: {MQTT_PASSWORD}")
    print(f"DISCOVERY_PREFIX: {DISCOVERY_PREFIX}")
    print(f"SENSOR_PREFIX: {SENSOR_PREFIX}")
    print(f"COMMAND_TOPIC: {COMMAND_TOPIC}")
    print(f"DEVICE_MANUFACTURER: {DEVICE_MANUFACTURER}")
    print(f"DEVICE_MODEL: {DEVICE_MODEL}")
    print(f"DEVICE_NAME: {DEVICE_NAME}")
    print(f"TZ: {os.getenv('TZ')}")    

def run_speedtest_and_publish():
    """Run speedtest and publish results - used by both timer and MQTT commands"""
    global mqtt_client
    result = run_speedtest()
    if result:
        summary = extract_summary(result)
        print(summary)
        
        # Use the global MQTT client, create if needed (lazy initialization)
        if not mqtt_client or not mqtt_client.is_connected():
            print("🔌 Connecting to MQTT broker...")
            mqtt_client = connect_mqtt()
            mqtt_client.loop_start()
        
        publish_discovery(mqtt_client, "ping_ms", "Ping", "ms", "mdi:speedometer", "{{ value }}")
        publish_discovery(mqtt_client, "jitter_ms", "Jitter", "ms", "mdi:chart-bell-curve", "{{ value }}")
        publish_discovery(mqtt_client, "download_mbps", "Download", "Mbps", "mdi:download-network", "{{ value }}")
        publish_discovery(mqtt_client, "upload_mbps", "Upload", "Mbps", "mdi:upload-network", "{{ value }}")
        publish_discovery(mqtt_client, "packet_loss", "Packet Loss", "%", "mdi:percent", "{{ value }}")
        publish_discovery(mqtt_client, "external_ip", "External IP", None, "mdi:ip-network", "{{ value }}")
        publish_discovery(mqtt_client, "isp", "ISP", None, "mdi:access-point-network", "{{ value }}")
        publish_discovery(mqtt_client, "server", "Server", None, "mdi:server", "{{ value }}")        
        publish_discovery(mqtt_client, "timestamp", "Timestamp", None, "mdi:clock", "{{ value }}")
        publish_camera_discovery(mqtt_client)
        publish_camera_image(mqtt_client, summary["image_url"])
        publish_values(mqtt_client, summary)

def run_once():
    """Legacy function for backwards compatibility"""
    run_speedtest_and_publish()

def run_interval_timer(interval):
    """Run speedtest at regular intervals in a separate thread"""
    while True:
        time.sleep(interval)
        print(f"⏰ Scheduled speedtest triggered (interval: {interval}s)")
        run_speedtest_and_publish()

if __name__ == "__main__":
    # Print version on startup
    version = get_version()
    print(f"🚀 Speedtest MQTT HA - Version: {version}")
    
    test_mode = os.getenv("TEST_MODE", "0") == "1"
    interval = int(os.getenv("SAMPLE_INTERVAL_SECONDS", "10800"))
    printEnvVars()

    if test_mode:
        print("🧪 Running in test mode (once)...")
        run_once()
        # Clean up the connection after test mode
        cleanup_mqtt()
    else:
        print(f"🔁 Starting service with {interval} second intervals...")
        print(f"📡 MQTT command topic: {COMMAND_TOPIC}")
        print("Send 'run', 'start', 'execute', or 'go' to trigger manual speedtest")
        
        # Connect to MQTT and start listening for commands
        mqtt_client = connect_mqtt()
        mqtt_client.loop_start()
        
        # Start the interval timer in a separate thread
        timer_thread = threading.Thread(target=run_interval_timer, args=(interval,), daemon=True)
        timer_thread.start()
        
        # Run initial speedtest
        print("🚀 Running initial speedtest...")
        run_speedtest_and_publish()
        
        try:
            # Keep the main thread alive
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
            cleanup_mqtt()
