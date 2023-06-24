
import dht
from machine import Pin
from config import utelegram_config

import utelegram
import network
import utime
import ujson
from umqtt.simple import MQTTClient

debug = False

dht_pin = Pin(14, Pin.IN)
dht_sensor = dht.DHT22(dht_pin)

active_users = set()
temperature_hourly = []
humidity_hourly = []
daily_average_temperature = []
daily_average_humidity = []
monthly_average_temperature = []
monthly_average_humidity = []
previous_hour = None

wifi_ssid = "YOUR_WIFISSID"
wifi_password = "YOUR_WIFIPASSWORD"

debug = False

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.scan()
if sta_if.isconnected() == False:
    sta_if.connect(wifi_ssid, wifi_password)

if debug: print('WAITING FOR NETWORK - sleep 20')
utime.sleep(10)

def handle_start(message):
    chat_id = message['message']['chat']['id']
    if chat_id not in active_users:
      active_users.add(chat_id)
      bot.send(chat_id, "Welcome to Temperature and Humidity Monitor Bot!")
    else:
      bot.send(chat_id, "You have already started the bot.")

def handle_stop(message):
    chat_id = message['message']['chat']['id']
    if chat_id in active_users:
      active_users.remove(chat_id)
      bot.send(chat_id, "You have unsubscribed from notifications.")
    else:
      bot.send(chat_id, "You haven't started the bot yet.")

def handle_temperature(message):
    chat_id = message['message']['chat']['id']
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    publish_data_to_favoriot(temperature, "temperature")
    bot.send(chat_id, "Current temperature: {:.1f} Celcius".format(temperature))

def handle_humidity(message):
    chat_id = message['message']['chat']['id']
    dht_sensor.measure()
    humidity = dht_sensor.humidity()
    publish_data_to_favoriot(humidity, "humidity")
    bot.send(chat_id, "Current humidity: {:.1f} %".format(humidity))
    
def publish_data_to_favoriot(data, data_type):
  
    token = 'YOUR FAVORIOT DEVICE ACCESS TOKEN'
    
    mqtt_broker = "mqtt.favoriot.com"
    mqtt_client_id = "YOUR CLIENT NAME (ANY NAME)"
    
    mqtt_topic = token + "/v2/streams"

    mqtt_client = MQTTClient(mqtt_client_id, mqtt_broker, user=token, password=token)
    mqtt_client.connect()

    dat = {
        "device_developer_id": "YOUR DEVICE DEVELOPER NAME",
        "data": {
          data_type: data, 
        }
    }
    payload = str(ujson.dumps(dat))

    mqtt_client.publish(mqtt_topic, payload)
    mqtt_client.disconnect()

if sta_if.isconnected():
    bot = utelegram.ubot(utelegram_config['token'])
    bot.register('/start', handle_start)
    bot.register('/stop', handle_stop)
    bot.register('/temperature', handle_temperature)
    bot.register('/humidity', handle_humidity)

    print('BOT LISTENING')
    bot.listen()
else:
    print('NOT CONNECTED - aborting')

def calculate_hourly_average():
    if temperature_hourly and humidity_hourly:
        average_temperature = sum(temperature_hourly) / len(temperature_hourly)
        average_humidity = sum(humidity_hourly) / len(humidity_hourly)
        daily_average_temperature.append(average_temperature)
        daily_average_humidity.append(average_humidity)
        temperature_hourly.clear()
        humidity_hourly.clear()

def calculate_daily_average():
    if daily_average_temperature and daily_average_humidity:
        average_temperature = sum(daily_average_temperature) / len(daily_average_temperature)
        average_humidity = sum(daily_average_humidity) / len(daily_average_humidity)
        monthly_average_temperature.append(average_temperature)
        monthly_average_humidity.append(average_humidity)
        daily_average_temperature.clear()
        daily_average_humidity.clear()

def calculate_monthly_average():
    if monthly_average_temperature and monthly_average_humidity:
        average_temperature = sum(monthly_average_temperature) / len(monthly_average_temperature)
        average_humidity = sum(monthly_average_humidity) / len(monthly_average_humidity)
        monthly_average_temperature.clear()
        monthly_average_humidity.clear()

def send_notification():
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()

    if temperature > 30 and humidity < 25:
        message = f"High temperature ({temperature} Celcius) and low humidity ({humidity}%) detected!"
        for chat_id in active_users:
            bot.send(chat_id, message)

    temperature_hourly.append(temperature)
    humidity_hourly.append(humidity)

    current_hour = time.localtime().tm_hour

    if previous_hour is not None and current_hour != previous_hour:
        calculate_hourly_average()

        if time.localtime().tm_mday != time.localtime(time.time() - 86400).tm_mday:
            calculate_daily_average()

        if time.localtime().tm_mday == 1 and current_hour == 0:
            calculate_monthly_average()

    previous_hour = current_hour

while True:
    try:
        send_notification()

    except OSError as e:
        print("Failed to read sensor:", e)

    time.sleep(60)

