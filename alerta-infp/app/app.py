import math
import requests
import re
import json
import logging
import pathlib
import time

import paho.mqtt.client as mqtt
from sseclient import SSEClient


def main():
    try:
        configfile = pathlib.Path('/data/options.json')
        if not configfile.exists():
            configfile = pathlib.Path(__file__).parent.parent / 'config.json'

        with open(configfile) as f:
            config = json.load(f)

        if 'options' in config:
            config = config['options']

        logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
                '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging._nameToLevel[config['LOG_LEVEL']])

        mqttClient = mqtt.Client("alerta-infp")
        mqttClient.username_pw_set(config["mqtt_user"], config["mqtt_password"])
        mqttClient.will_set("alerta-infp/online", "offline", retain=True, qos=0)
        
        mqttClient.connect(config["mqtt_server"], config["mqtt_port"])
        mqttClient.loop_start()
        
        mqttClient.publish("alerta-infp/online", "online", retain=True, qos=0)
        mqttClient.publish("homeassistant/binary_sensor/alerta-infp/config", '{"name":"Cutremur","dev_cla":"safety","stat_t":"homeassistant/binary_sensor/alerta-infp/state","avty_t":"alerta-infp/online"}', retain=True, qos=0)
        mqttClient.publish("homeassistant/sensor/alerta-infp/magnitudine/config", '{"name":"Magnitudine Cutremur","stat_t":"homeassistant/sensor/alerta-infp/magnitudine/state","avty_t":"alerta-infp/online","unit_of_meas":"Richter"}', retain=True, qos=0)
        mqttClient.publish("homeassistant/sensor/alerta-infp/seconds/config", '{"name":"Secunde pana la Bucuresti","stat_t":"homeassistant/sensor/alerta-infp/seconds/state","avty_t":"alerta-infp/online"}', retain=True, qos=0)

        while True:
            host = 'http://alerta.infp.ro/'
            response = None
            try:
                response = requests.get(host)    
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to server: {e}")
                time.sleep(10)
                continue
            
            if response is None:
                logger.error("Empty response from server")
                time.sleep(10)
                continue
            
            key =
