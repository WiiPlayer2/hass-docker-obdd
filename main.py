import paho.mqtt.client as mqtt
import obd
import os
import time
import threading

from sensors import get_all_sensors

IGNORE_OBD_CONNECTION = os.environ.get('IGNORE_OBD_CONNECTION', 'True') == 'True'
MQTT_BROKER = os.environ.get('MQTT_BROKER', '192.168.1.2')
MQTT_CLIENT_NAME = os.environ.get('MQTT_CLIENT_NAME', 'obd-service')
HASS_DISCOVERY_PREFIX = os.environ.get('HASS_DISCOVERY_PREFIX', 'homeassistant')
OBD_WATCH_COMMANDS = [s.strip() for s in os.environ.get('OBD_WATCH_COMMANDS', ', '.join([
    'ELM_VERSION',
    'ELM_VOLTAGE',
    'RPM',
])).split(',')]
NODE_ID = os.environ.get('NODE_ID', 'car')
CHECK_INTERVAL = float(os.environ.get('CHECK_INTERVAL', '30'))

class ObdService():
    def loop_start(self, mqtt_client, watch_sensors):
        threading.Thread(target=self._loop, args=(mqtt_client, watch_sensors)).run()

    def _loop(self, mqtt_client, watch_sensors):
        conn = None
        is_connected = False
        while True:
            while not is_connected:
                try:
                    conn = obd.Async()
                    is_connected = conn.status() == obd.OBDStatus.CAR_CONNECTED or IGNORE_OBD_CONNECTION
                except:
                    pass
                if not is_connected:
                    time.sleep(CHECK_INTERVAL)

            sensors = [sensor for sensor in watch_sensors if sensor.cmd in conn.supported_commands]
            for sensor in sensors:
                sensor.register(HASS_DISCOVERY_PREFIX, client, conn)
            conn.start()

            while is_connected:
                time.sleep(CHECK_INTERVAL)
                try:
                    is_connected = conn.status() == obd.OBDStatus.CAR_CONNECTED or IGNORE_OBD_CONNECTION
                except:
                    is_connected = False



if __name__ == '__main__':
    watch_sensors = [sensor for sensor in get_all_sensors(NODE_ID) if sensor.name in OBD_WATCH_COMMANDS]

    client = mqtt.Client(MQTT_CLIENT_NAME)
    client.username_pw_set('car', 'car')

    is_connected = False
    while not is_connected:
        try:
            client.connect(MQTT_BROKER)
            is_connected = True
        except:
            is_connected = False
            time.sleep(CHECK_INTERVAL)

    obd_service = ObdService()
    obd_service.loop_start(client, watch_sensors)

    client.loop_forever()
