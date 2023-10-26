# Easy ADS-B
Project to easily setup your device as a ADS-B receiver

# Setup
- run `./installer_raspberrypi.sh`

# System Design
<img src="res/easyadsb_system.png" width="800">

# MQTT API
## Overview
| Topic | Data | Type | Description |
|---|---|---|---|
| /easyadsb/dump1090/sbs | SBS | notification | Raw ADSB Traffic Messages |
| /easyadsb/bme280/json | json | notification | Environmental Sensor (barometric pressure) |
| /easyadsb/ublox/nmea | NMEA | notification | GNSS |
| /easyadsb/monitor/satellites | json | notification | Satellite Information |
| /easyadsb/monitor/position | json | notification | Position Information |
| /easyadsb/monitor/status | json | notification | Status Information (GDL90) |
| /easyadsb/monitor/traffic | json | notification | Traffic Information |
| /easyadsb/monitor/traffic/ctrl/request | json | request |  |
| /easyadsb/monitor/traffic/ctrl/response | json | response |  |
| /easyadsb/sysmgmt/info | json | notification | System Information (WiFi, CPU) |
| /easyadsb/sysmgmt/ctrl/request | json | request |  |
| /easyadsb/sysmgmt/ctrl/response | json | response |  |

## SBS notification
SBS-1 Basestation Protocol. Message format documentation: [http://woodair.net/SBS/Article/Barebones42_Socket_Data.htm]()

Example: `MSG,3,1,1,44039E,1,2023/10/26,07:20:11.481,2023/10/26,07:20:11.491,,30500,,,,,,,0,,0,0
`

## NMEA notification
NMEA Strings. More Info: [https://www.gpsworld.com/what-exactly-is-gps-nmea-data/]()

Currently used Message IDs are **GSV, GSA, VTG & GGA**

Example: `$GNGGA,072015.00,,,,,0,00,99.99,,,,,,*79`

## BME280 json notification
json objects containing the following fields
- humidity, rel. Hum. %, decimal
- pressure, hPa, decimal
- temperature, °C, decimal
- pressureAltitude, m.s.l., decimal

Example: `{"humidity": 33.336, "pressure": 905.348, "temperature": 27.854, "pressureAltitude": 1002.566}`

Pressure Altitude calculation uses 1013.25 hPa as reference pressure and compensates for temperature.
More Info: [https://en.wikipedia.org/wiki/Pressure_altitude]()


# GDL90
Garmin Datalink. Mobile Devices running Sky Demon can be connected to this interface.
Protocol Spec: [https://www.faa.gov/sites/faa.gov/files/air_traffic/technology/adsb/archival/GDL90_Public_ICD_RevA.PDF]()



