# speedtest-mqtt

A service that wraps a python script for running Ookla Speedtest CLI and report results to MQTT with Home Assistant auto discovery.  
SAMPLE_INTERVAL_SECONDS determines the frequency of the sample.

## Features
- **Scheduled speedtests**: Run speedtests at regular intervals
- **On-demand speedtests**: Trigger speedtests manually via MQTT commands
- **Home Assistant integration**: Automatic device and sensor discovery
- **Thread-safe**: Multiple speedtest requests are handled safely with rate limiting

A Home Assistant device will be created with the following sensors:
* Ping (ms)  
* Jitter(ms)  
* Download (Mbps)  
* Upload (Mbps)  
* Packet Loss (%)  
* External IP  
* ISP  
* Speedtest Server  
* Speedtest Timestamp  

It will also create a camera entity for the speed test snapshot image  

# Installation  
The easiest way to install is with a container and docker-compose:  
```
version: "3.8"

services:
  speedtest-mqtt:
    image: ghcr.io/sefininio/speedtest-mqtt:latest
    container_name: speedtest-mqtt
    restart: unless-stopped
    env_file: .env
    network_mode: host  
    environment:      
      - TZ=Asia/Jerusalem    
```


# Manual Speedtest Commands

You can trigger speedtests manually by publishing MQTT messages to the command topic (default: `home/internet/speedtest/run`).

Supported commands:
- `run`
- `start` 
- `execute`
- `go`

Example using mosquitto client:
```bash
mosquitto_pub -h your-mqtt-broker -t "home/internet/speedtest/run" -m "run"
```

**Rate limiting**: Manual speedtests are rate-limited to prevent running more than once every 30 seconds.

# .env file:
### MQTT connection  
> The MQTT host IP  
MQTT_BROKER_HOST    

> The MQTT host port   
MQTT_BROKER_PORT=1883    

> The MQTT username  (optional)   
MQTT_USERNAME       

> The MQTT password  (optional)  
MQTT_PASSWORD       

> every 3 hours by default  
SAMPLE_INTERVAL_SECONDS=10800

### Entity naming and discovery

> MQTT discovery topic prefix  
DISCOVERY_PREFIX=homeassistant  

> HA sensor name prefix  
SENSOR_PREFIX=home/internet/speedtest  

> MQTT topic to listen for manual speedtest commands  
COMMAND_TOPIC=home/internet/speedtest/run

> HA Device name. Add postfix for the server name, this will allow multiple instances running speedtest and reporting to the same mqtt+ha instance  
> For example `speedtest_nas` will create a `Speedtest Nas` Device.
DEVICE_NAME=speedtest  

> HA Device manufacturer  
DEVICE_MANUFACTURER="Ookla + MQTT"  

> HA Device model  
DEVICE_MODEL=Speedtest CLI  

> Timezone override  
TZ=Asia/Jerusalem  

