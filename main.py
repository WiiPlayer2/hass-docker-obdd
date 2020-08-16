import paho.mqtt.client as mqtt
import obd
import os
import time
import threading
import logging
import sys

from sensors import get_all_sensors

IGNORE_OBD_CONNECTION = os.environ.get('IGNORE_OBD_CONNECTION', 'True') == 'True'
MQTT_BROKER = os.environ.get('MQTT_BROKER', '192.168.1.2')
MQTT_CLIENT_NAME = os.environ.get('MQTT_CLIENT_NAME', 'obd-service-debug')
HASS_DISCOVERY_PREFIX = os.environ.get('HASS_DISCOVERY_PREFIX', 'homeassistant')
OBD_WATCH_COMMANDS = [s.strip() for s in os.environ.get('OBD_WATCH_COMMANDS', ', '.join([
    'ELM_VERSION',
    'ELM_VOLTAGE',
    'RPM',
])).split(',')]
NODE_ID = os.environ.get('NODE_ID', 'car')
CHECK_INTERVAL = float(os.environ.get('CHECK_INTERVAL', '30'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')

logger = logging.getLogger(__name__)

class ObdService():
    def loop_start(self, mqtt_client, watch_sensors):
        threading.Thread(target=self._loop, args=(mqtt_client, watch_sensors)).run()

    def _loop(self, mqtt_client, watch_sensors):
        conn = None
        is_connected = False
        while True:
            logger.info('Connecting to obd adapter...')
            while not is_connected:
                try:
                    conn = obd.Async()
                    status = conn.status()
                    logger.debug(f'conn.status() = {status}')
                    is_connected = status == obd.OBDStatus.CAR_CONNECTED or IGNORE_OBD_CONNECTION
                except Exception as e:
                    logger.warning('Connecting to obd adapter failed.', exc_info=e)
                if not is_connected:
                    logger.debug(f'Retrying obd connection in {CHECK_INTERVAL} seconds...')
                    time.sleep(CHECK_INTERVAL)

            logger.info('Connected to obd adapter. Registering sensors and starting connection...')
            sensors = [sensor for sensor in watch_sensors if sensor.cmd in conn.supported_commands]
            for sensor in sensors:
                sensor.register(HASS_DISCOVERY_PREFIX, client, conn)
            conn.start()
            logger.info('OBD connection started.')

            while is_connected:
                time.sleep(CHECK_INTERVAL)
                try:
                    status = conn.status()
                    logger.debug(f'conn.status() = {status}')
                    is_connected = status == obd.OBDStatus.CAR_CONNECTED or IGNORE_OBD_CONNECTION
                except Exception as e:
                    logger.warning('Disconnceted from obd adapter due to an exception.', exc_info=e)
                    is_connected = False



if __name__ == '__main__':
    logging.basicConfig(
        level=LOG_LEVEL,
        format="[%(asctime)s | %(name)s] %(message)s"
        )

    logger.info('Starting...')
    watch_sensors = [sensor for sensor in get_all_sensors(NODE_ID) if sensor.name in OBD_WATCH_COMMANDS]

    logger.info('Connecting to MQTT broker...')
    client = mqtt.Client(MQTT_CLIENT_NAME)
    client.username_pw_set('car', 'car')
    is_connected = False
    while not is_connected:
        try:
            client.connect(MQTT_BROKER)
            is_connected = True
        except Exception as e:
            logger.warning(f'Failed to connect to broker. Retrying in {CHECK_INTERVAL} seconds', exc_info=e)
            is_connected = False
            time.sleep(CHECK_INTERVAL)

    logger.info('Starting up the obd service...')
    obd_service = ObdService()
    obd_service.loop_start(client, watch_sensors)

    logger.info('MQTT is ready.')
    client.loop_forever()
