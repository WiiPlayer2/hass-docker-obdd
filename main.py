import paho.mqtt.client as mqtt
import obd
import os
import time
import threading

from commands import all_commands

IGNORE_OBD_CONNECTION = os.environ.get('IGNORE_OBD_CONNECTION', 'True') == 'Tru'
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
    def loop_start(self, mqtt_client, watch_commands):
        threading.Thread(target=self._loop, args=(mqtt_client, watch_commands)).run()

    def _loop(self, mqtt_client, watch_commands):
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

            cmds = [cmd for cmd in watch_commands if cmd.cmd in conn.supported_commands]
            for cmd in cmds:
                cmd.register(HASS_DISCOVERY_PREFIX, NODE_ID, client, conn)
            conn.start()

            while is_connected:
                time.sleep(CHECK_INTERVAL)
                try:
                    is_connected = conn.status() == obd.OBDStatus.CAR_CONNECTED or IGNORE_OBD_CONNECTION
                except:
                    is_connected = False



if __name__ == '__main__':
    watch_commands = [cmd for cmd in all_commands if cmd.name in OBD_WATCH_COMMANDS]

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
    obd_service.loop_start(client, watch_commands)

    client.loop_forever()
