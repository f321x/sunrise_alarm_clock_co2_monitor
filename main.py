from machine import RTC, Pin, PWM
from co2sensor import MH_Z19
from utime import sleep
import network
import rp2
from microdot_asyncio import Microdot
import uasyncio as asyncio
from random import randint
import urequests as requests
import json
import gc

relai = Pin(21, Pin.OUT)
rtc = RTC()
ws = Microdot()
sensor = MH_Z19(Pin(0), Pin(1))
sensor.enable_self_calibration()
buzzer = PWM(Pin(17))
buzzer.duty_u16(0)
buzzer.deinit()

alarm_time = "00:00"
time = None
sensor_values = None
alarm_sound = 0
sensor_values = {'temperature': 0, 'co2': 0}

rp2.country('DE')
wlan = network.WLAN(network.STA_IF)
SSID = "WIFI SSID"
pw = "WIFI PASSWORD"
wlan.active(True)

def connect_wifi():
    for tries in range(5):
        wlan_status = wlan.status()
        if wlan_status != 3:
            wlan.connect(SSID, pw)
            sleep(3)
        else:
            wlan_status = None
            break

def init_rtc():
    try:
        real_time = requests.get("https://www.timeapi.io/api/Time/current/zone?timeZone=Europe/Berlin")
        time_data = json.loads(real_time.text)
        real_time.close()
        if time_data["dayOfWeek"] == "Monday":
            dow = 0
        elif time_data["dayOfWeek"] == "Tuesday":
            dow = 1
        elif time_data["dayOfWeek"] == "Wednesday":
            dow = 2
        elif time_data["dayOfWeek"] == "Thursday":
            dow = 3
        elif time_data["dayOfWeek"] == "Friday":
            dow = 4
        elif time_data["dayOfWeek"] == "Saturday":
            dow = 5
        elif time_data["dayOfWeek"] == "Sunday":
            dow = 6
        rt_tuple = (time_data["year"], time_data["month"], time_data["day"], dow, time_data["hour"], time_data["minute"], time_data["seconds"], 255)
        time_data = None
        dow = None
        rtc.datetime(rt_tuple)
        rt_tuple = None
    except:
        connect_wifi()

async def upload_co2():
    global sensor_values
    headers = {
    'Content-Type': 'application/json;charset=UTF-8',
    'Authorization': 'Bearer your_authentification_token_here',
    'Accept': 'application/json, text/plain, */*',}
    try: 
        sensor_values = sensor.read_all()
        await asyncio.sleep(0.5)
        if sensor_values != {}:
            response = requests.post('https://backend.thinger.io/v3/users/my_custom_dashboard', headers=headers, json=sensor_values)
            response.close()
            headers = None
        elif sensor_values == {}:
            headers = None
            sensor_values = {'temperature': 0, 'co2': 0}
    except:
        headers = None
        pass

html = """<style>
  form {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 50px;
  }

  label {
    font-weight: bold;
    margin-bottom: 10px;
  }

  input[type="time"] {
    padding: 10px;
    font-size: 18px;
    margin-bottom: 20px;
  }

  input[type="submit"] {
    padding: 10px 20px;
    background-color: lightblue;
    border-radius: 5px;
    font-size: 18px;
    cursor: pointer;
  }

  .status {
    display: flex;
    justify-content: space-between;
    margin: 50px;
  }

  .status h1 {
    font-size: 24px;
  }
</style>

<form action="/set-alarm" method="post">
  <label for="alarm-time">Set alarm for:</label>
  <input type="time" id="alarm-time" name="alarm-time">
  <input type="submit" value="Submit">
</form>

<form action="/togglelight" method="post">
  <label for="lightswitch">Toggle light:</label>
  <input type="submit" value="On/Off">
</form>

<form action="/togglesound" method="post">
  <label for="sound">Toggle sound (beeper):</label>
  <input type="submit" value="On/Off">
</form>

<div class="status">
  <h1>Current alarm status: %s</h1>
  <h1>Sound status: %s</h1>
  <h1>Current RTC time: %s</h1>
</div>

<div class="status">
  <h1>CO2 concentration: %s ppm</h1>
  <h1>Temperature: %s C</h1>
</div>"""


        
@ws.route('/')
async def index(request):
    global time
    global alarm_sound
    time_web = str(time[4])+":"+str(time[5])+":"+str(time[6])+" "+str(time[2])+"."+str(time[1])+"."+str(time[0])
    return html % (alarm_time, str(alarm_sound),time_web, sensor_values["co2"], sensor_values["temperature"]), 202, {'Content-Type': 'text/html'}

@ws.route('/set-alarm', methods=['POST'])
async def set_alarm(request):
    global alarm_time
    alarm_time = request.form['alarm-time']
    return "<h1>Alarm set!</h1>", 202, {'Content-Type': 'text/html'}

@ws.route('/togglelight', methods=['POST'])
async def togglelight(request):
    relai.toggle()
    if relai.value() == 1:
        return "<h1>Licht an!</h1>", 202, {'Content-Type': 'text/html'}
    elif relai.value() == 0:
        return "<h1>Licht aus!</h1>", 202, {'Content-Type': 'text/html'}
    else:
        return "Fehler beim Lichtwechsel!"
    
@ws.route('/togglesound', methods=['POST'])
async def togglesound(request):
    global alarm_sound
    if alarm_sound == 1:
        alarm_sound = 0
        return "<h1>Beeper deactivated!</h1>", 202, {'Content-Type': 'text/html'}
    elif alarm_sound == 0:
        alarm_sound = 1
        return "<h1>Beeper activated!</h1>", 202, {'Content-Type': 'text/html'}

async def alarm(duration_min):
    buzzer.init(freq=1000, duty_u16=32768)
    # buzzer.duty_u16(32768)
    for sound in range(int(duration_min*60)):
        if relai.value() == 1:
            buzzer.freq(randint(1000,6000))
            asyncio.sleep(1)
        else:
            buzzer.duty_u16(0)
            break
    buzzer.deinit()

async def alarm_clock():
    global alarm_time
    global alarm_sound
    global time
    while True:
        await upload_co2()
        time = rtc.datetime()
        if alarm_time == "00:00":
            pass
        elif time[4] == int(alarm_time[:2]) and time[5] == int(alarm_time[3:]):
            relai.on()
            if alarm_sound == 1 and relai.value() == 1:
                await asyncio.sleep(600)
                await alarm(10)
        elif alarm_time == "00:01":
            init_rtc()
            alarm_time = "00:00"
        gc.collect()
        await asyncio.sleep(20)

        
async def main():
    asyncio.create_task(alarm_clock())
    asyncio.create_task(ws.run(port=80))
    await asyncio.sleep(0)

connect_wifi()
init_rtc()

asyncio.run(main())
