# speedtest-mqtt

A service that wraps a python script for running Ookla Speedtest CLI and report results to MQTT with Home Assistant auto discovery.  
SAMPLE_INTERVAL_SECONDS determines the frequency of the sample.

## Disclaimer

**IMPORTANT LEGAL NOTICE**: By downloading, installing, or using this Docker container service, you acknowledge and agree to the following terms:

### Speedtest CLI License Agreement
This container utilizes the Ookla Speedtest CLI software. The following license terms are directly from the Speedtest CLI and must be strictly adhered to:

You may only use this Speedtest software and information generated
from it for personal, non-commercial use, through a command line
interface on a personal computer. Your use of this software is subject
to the End User License Agreement, Terms of Use and Privacy Policy at
these URLs:

	https://www.speedtest.net/about/eula
	https://www.speedtest.net/about/terms
	https://www.speedtest.net/about/privacy

### Container Service Disclaimer
This Docker container service is provided "AS IS" without warranty of any kind, express or implied. The author(s) and contributors of this container service:

1. Make no representations or warranties regarding the accuracy, functionality, or reliability of this software
2. Shall not be held liable for any direct, indirect, incidental, special, or consequential damages arising from the use or inability to use this software
3. Disclaim all responsibility for any violations of third-party terms of service, including but not limited to the Ookla Speedtest terms and conditions
4. Are not affiliated with or endorsed by Ookla LLC or any of its subsidiaries

**USER RESPONSIBILITY**: Users are solely responsible for:
- Ensuring compliance with all applicable terms of service and licensing agreements
- Any misuse of this container service or the underlying Speedtest software
- Understanding and accepting the risks associated with automated network testing
- Verifying that their use case complies with their internet service provider's terms of service

By proceeding with the installation and use of this container, you acknowledge that you have read, understood, and agree to be bound by these terms.

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

