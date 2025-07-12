# speedtest-mqtt

A service that wraps a python script for running Ookla Speedtest CLI and report results to MQTT with Home Assistant auto discovery.  
SAMPLE_INTERVAL_SECONDS determines the frequency of the sample.

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

> HA Device name. Add postfix for the server name, this will allow multiple instances running speedtest and reporting to the same mqtt+ha instance  
> For example `speedtest_nas` will create a `Speedtest Nas` Device.
DEVICE_NAME=speedtest  

> HA Device manufacturer  
DEVICE_MANUFACTURER="Ookla + MQTT"  

> HA Device model  
DEVICE_MODEL=Speedtest CLI  

> Timezone override  
TZ=Asia/Jerusalem  

