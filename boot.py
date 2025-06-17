# boot.py

import network
import time
import secrets
from umqtt.simple import MQTTClient

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)

def connect_wifi():
    if not sta_if.isconnected():
        print("Connecting to WiFi...")
        sta_if.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
        while not sta_if.isconnected():
            print(".", end="")
            time.sleep(0.5)
    print("\nWiFi connected:", sta_if.ifconfig())

def init_mqtt():
    client = MQTTClient("esp32_modbus", secrets.MQTT_BROKER_IP)
    try:
        client.connect()
        print("MQTT connected to", secrets.MQTT_BROKER_IP)
        return client
    except Exception as e:
        print("Failed to connect to MQTT broker:", e)
        return None

# Call on boot
connect_wifi()
