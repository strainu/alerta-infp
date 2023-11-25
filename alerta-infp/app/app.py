import math, requests, re, json, logging, pathlib, time
import uuid
import paho.mqtt.client as mqtt

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
        mqttClient.will_set("alerta-infp/online", "offline", retain = True, qos = 0)

        mqttClient.connect(config["mqtt_server"], config["mqtt_port"])
        mqttClient.loop_start()

        # Generați un UUID unic pentru fiecare entitate
        entity_ids = {
            "binary_sensor": str(uuid.uuid4()),
            "sensor_magnitudine": str(uuid.uuid4()),
            "sensor_seconds": str(uuid.uuid4()),
            "sensor_online": str(uuid.uuid4()),
        }

        # Configurația entităților MQTT cu ID-urile unice
        mqttClient.publish("homeassistant/binary_sensor/alerta-infp/config",f'{{"name":"Cutremur","dev_cla":"safety","stat_t":"homeassistant/binary_sensor/alerta-infp/state","avty_t":"alerta-infp/online","unique_id":"{entity_ids["binary_sensor"]}"}}',retain=True,qos=0,)
        mqttClient.publish("homeassistant/binary_sensor/alerta-infp/conexiune/config",f'{{"name":"Stare conexiune INFP","dev_cla":"safety","stat_t":"homeassistant/binary_sensor/alerta-infp/conexiune/state","avty_t":"alerta-infp/online","unique_id":"{entity_ids["binary_sensor"]}"}}',retain=True,qos=0,)

        mqttClient.publish("homeassistant/sensor/alerta-infp/magnitudine/config",f'{{"name":"Magnitudine Cutremur","stat_t":"homeassistant/sensor/alerta-infp/magnitudine/state","avty_t":"alerta-infp/online","unit_of_meas":"Richter","unique_id":"{entity_ids["sensor_magnitudine"]}"}}',retain=True,qos=0,)
        
        mqttClient.publish(
            "homeassistant/sensor/alerta-infp/seconds/config",
            f'{{"name":"Secunde pana la Bucuresti","stat_t":"homeassistant/sensor/alerta-infp/seconds/state","avty_t":"alerta-infp/online","unique_id":"{entity_ids["sensor_seconds"]}"}}',
            retain=True,
            qos=0,
        )
        mqttClient.publish(
            "homeassistant/binary_sensor/alerta-infp-online/config",
            f'{{"name":"Status addon cutremur","dev_cla":"safety","stat_t":"homeassistant/binary_sensor/alerta-infp-online/state","avty_t":"alerta-infp/online","unique_id":"{entity_ids["binary_sensor"]}"}}',
            retain=True,
            qos=0,
        )
        
        # ...
        while(1):
            try:
                res = requests.get("http://alerta.infp.ro/server.php",    headers= {
                    "accept": "text/event-stream",
                    "accept-language": "en-US,en;q=0.9,ro-RO;q=0.8,ro;q=0.7,zh-CN;q=0.6,zh;q=0.5",
                    "cache-control": "no-cache",
                    "cookie": "PHPSESSID=j9lr97p5oqhr0kgodd81frr161", # set cookie
                    "Referer": "http://alerta.infp.ro/",
                    "Referrer-Policy": "strict-origin-when-cross-origin"
                })
                print(res.text[6:])
                message = json.loads(res.text[6:])
                if('err' in message):
                    mqttClient.publish("alerta-infp/online", "offline", retain = True, qos = 0)
                    logger.info('Refreshing connection')
                    logger.info(f'STATUS = OFFLINE') 
                    mqttClient.publish('homeassistant/binary_sensor/alerta-infp/conexiune/state', 'ON', qos = 0)
                    continue
                else:
                    magnitude = float(message["mag"])
                    earthquake = 'ON' if magnitude >= 1. else 'OFF'
                    seconds = float(message["sec"])
                    heart = str(message["heart"])
                    conex = 'OFF' 
                    
                    logger.debug(f'Magnitude = {magnitude} seconds = {seconds} earthquake = {earthquake}')

                    mqttClient.publish('homeassistant/sensor/alerta-infp/magnitudine/state', magnitude, qos = 0)
                    logger.info(f'Magnitude = {magnitude}')

                    mqttClient.publish('homeassistant/binary_sensor/alerta-infp/conexiune/state', 'ON', qos = 0)
                    
                    
                    mqttClient.publish('homeassistant/binary_sensor/alerta-infp/state', earthquake, qos = 0)
                    logger.info(f'earthquake = {earthquake}')

                    mqttClient.publish('homeassistant/sensor/alerta-infp/seconds/state', seconds, qos = 0)
                    mqttClient.publish("alerta-infp/online", "online", retain = True, qos = 0)
                    logger.info(f'seconds = {seconds}')
                    logger.info(f'last update = {heart}')
                    logger.info(f'STATUS = {conex}') 
            except Exception as e:
                conex = 'ON'
                mqttClient.publish("alerta-infp/online", "offline", retain = True, qos = 0)
                logger.error(e)
                logger.info(f'STATUS = {conex}') 
                mqttClient.publish('homeassistant/binary_sensor/alerta-infp/conexiune/state', conex, qos = 0)

            time.sleep(5) # 5 secunde
    except Exception as e:
        logger.error(e)

if __name__ == '__main__':
    main()
