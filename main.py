import paho.mqtt.client as mqtt
import obd
import os

from commands import all_commands

MQTT_BROKER = os.environ.get('MQTT_BROKER', '192.168.1.102')
MQTT_CLIENT_NAME = os.environ.get('MQTT_CLIENT_NAME', 'obd-service')
HASS_DISCOVERY_PREFIX = os.environ.get('HASS_DISCOVERY_PREFIX', 'homeassistant')
OBD_WATCH_COMMANDS = [s.strip() for s in os.environ.get('OBD_WATCH_COMMANDS', ', '.join([
    'ELM_VERSION',
    'ELM_VOLTAGE',
    'RPM',
])).split(',')]
NODE_ID = os.environ.get('NODE_ID', 'car')

if __name__ == '__main__':
    conn = obd.Async()
    cmds = [cmd for cmd in all_commands if cmd.name in OBD_WATCH_COMMANDS and cmd.cmd in conn.supported_commands]

    client = mqtt.Client(MQTT_CLIENT_NAME)
    client.username_pw_set('car', 'car')
    client.connect(MQTT_BROKER)

    for cmd in cmds:
        cmd.register(HASS_DISCOVERY_PREFIX, NODE_ID, client, conn)
    conn.start()

    client.loop_forever()
