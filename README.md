# sunrise_alarm_clock_micropython
Sunrise alarm clock which activates lamp with relay (or 433mHz outlets) at a set time. Also CO2 logger which shows the current concentration of carbon dioxide in ppm to log and monitor
the air in the sleeping room.
All is controlled trough a simple html webinterface in the local wifi network and the co2+temperature mesurements are uploaded to a IoT API (thinger) to
visualize the data.

CO2+Temperature Sensor: MH-Z19

Microcontroller: Raspberry Pi Pico running Micropython

Relay: random Aliexpress relay

Webinterface:

![Screenshot_20230603-233025_1](https://github.com/f321x/sunrise_alarm_clock_co2_monitor/assets/51097237/5ff4cc5c-98c7-47da-9d02-2a009fbbeb8c)

IoT API (Thinger):

![Screenshot_20230603-233051](https://github.com/f321x/sunrise_alarm_clock_co2_monitor/assets/51097237/a3dcbb65-6e58-49be-8d81-4342a51a9735)
