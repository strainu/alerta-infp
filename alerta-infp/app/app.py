import math
import requests
import re
import json
import logging
import pathlib
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
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging._nameToLevel[config['LOG_LEVEL']])

        mqttClient = mqtt.Client("alerta-infp")
        mqttClient.username_pw_set(config["mqtt_user"], config["mqtt_password"])
        mqttClient.will_set("alerta-infp/online", "offline", retain=True, qos=0)

        if 'phpsessid' in config:
            session_cookie = requests.cookies.RequestsCookieJar()
            session_cookie.set('PHPSESSID', config['phpsessid'], domain='alerta.infp.ro')
            session = requests.Session()
            session.cookies.update(session_cookie)
            response = session.get('http://alerta.infp.ro/server.php?permanent=1')
            if response.status_code != 200:
                logger.error(f'Failed to connect to server: {response.status_code} - {response.reason}')
                return

        else:
            logger.warning('PHPSESSID not found in configuration')

        mqttClient.connect(config["mqtt_server"], config["mqtt_port"])
        mqttClient.loop_start()

        mqttClient.publish("alerta-infp/online", "online", retain=True, qos=0)
        mqttClient.publish("homeassistant/binary_sensor/alerta-infp/config", '{"name":"Cutremur","dev_cla":"safety","stat_t":"homeassistant/binary_sensor/alerta-infp/state","avty_t":"alerta-infp/online"}', retain=True, qos=0)
        mqttClient.publish("homeassistant/sensor/alerta-infp/magnitudine/config", '{"name":"Magnitudine Cutremur","stat_t":"homeassistant/sensor/alerta-infp/magnitudine/state","avty_t":"alerta-infp/online","unit_of_meas":"Richter"}', retain=True, qos=0)
        mqttClient.publish("homeassistant/sensor/alerta-infp/seconds/config", '{"name":"Secunde pana la Bucuresti","stat_t":"homeassistant/sensor/alerta-infp/seconds/state","avty_t":"alerta-infp/online"}', retain=True, qos=0)

        host = 'http://alerta.infp.ro/'
        messages = SSEClient(f'{host}server.php?permanent=1')

        for msg in messages:
            try:
                if msg.data:
                    message = json.loads(msg.data)
                    if 'err' in message:
                        logger.info('Refreshing connection')
                        break
                    else:
                        magnitude = float(message["mag"])
                        earthquake = 'ON' if magnitude >= 1. else 'OFF'
                        seconds = float(message["sec"])
                        heart = message["heart"]

                        logger.debug(f'Magnitude = {magnitude} seconds = {seconds} earthquake = {earthquake}')

                        mqttClient.publish('homeassistant/sensor/alerta-infp/magnitudine/state', magnitude, qos=0)
                        logger.info(f'Magnitude = {magnitude}')

    except Exception as e:
        logger.error(f'Failed to connect to server: {e}')
    return
