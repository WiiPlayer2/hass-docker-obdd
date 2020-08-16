import abc
import json
import logging
from obd import commands as cmds, OBDCommand, Unit as units, Async as OBDAsync
from paho.mqtt.client import Client as MqttClient

logger = logging.getLogger(__name__)

class DiscoveryInfo():
    def __init__(self, discovery_prefix: str, node_id: str, object_id: str, component: str, payload: dict):
        self._prefix = discovery_prefix
        self._node_id = node_id
        self._object_id = object_id
        self._component = component
        self._payload = payload

    @property
    def topic(self):
        return f'{self._prefix}/{self._component}/{self._node_id}/{self._object_id}/config'

    @property
    def payload(self):
        return self._payload

class ObdSensor(abc.ABC):
    def __init__(self, node_id: str, name: str, cmd: OBDCommand):
        self._node_id = node_id
        self._name = name
        self._cmd = cmd

    @property
    def name(self):
        return self._name

    @property
    def cmd(self):
        return self._cmd

    def register(self, discovery_prefix: str, mqtt_client: MqttClient, obd: OBDAsync):
        def callback(value):
            try:
                self._process_value(mqtt_client, value)
            except Exception as e:
                logger.error(f'Error while processing value. ({self.cmd} -> {value})', exc_info=e)
        info = self._get_discovery_info(discovery_prefix)
        mqtt_client.publish(info.topic, json.dumps(info.payload))
        obd.watch(self._cmd, callback)

    @abc.abstractmethod
    def _get_discovery_info(self, discovery_prefix: str) -> DiscoveryInfo:
        pass

    @abc.abstractmethod
    def _process_value(self, mqtt_client: MqttClient, value):
        pass

    @property
    def _uid(self):
        return f'{self._node_id}_{self._cmd.name}_{self._cmd.header.decode()}{self._cmd.command.decode()}'

    @property
    def _state_topic(self):
        return f'obd/{self._uid}'
    
    @property
    def _entity_name(self):
        return f'{self._node_id}_{self._cmd.name.lower()}'

class UnitObdSensor(ObdSensor):
    def __init__(self, node_id: str, name: str, cmd: OBDCommand, unit, device_class: str = None):
        super().__init__(node_id, name, cmd)
        self._unit = unit
        self._device_class = device_class
    
    def _process_value(self, mqtt_client: MqttClient, value):
        mqtt_client.publish(self._state_topic, value.magnitude)

    def _get_discovery_info(self, discovery_prefix: str):
        payload = {
                'unit_of_measurement': str(self._unit),
                'state_topic': self._state_topic,
                'name': self._entity_name,
                'unique_id': self._uid,
                'device': {
                    'identifiers': [
                        f'obd_{self._node_id}',
                    ],
                    'name': 'OBD',
                },
            }
        if self._device_class is not None:
            payload.update({'device_class': self._device_class})
        return DiscoveryInfo(
            discovery_prefix,
            self._node_id,
            self._uid,
            'sensor',
            payload)

class RawObdSensor(ObdSensor):
    def __init__(self, node_id: str, name: str, cmd: OBDCommand):
        super().__init__(node_id, name, cmd)

    def _process_value(self, mqtt_client: MqttClient, value):
        mqtt_client.publish(self._state_topic, value)
    
    def _get_discovery_info(self, discovery_prefix: str):
        return DiscoveryInfo(
            discovery_prefix,
            self._node_id,
            self._uid,
            'sensor',
            {
                'state_topic': self._state_topic,
                'name': self._entity_name,
                'unique_id': self._uid,
                'device': {
                    'identifiers': [
                        f'obd_{self._node_id}',
                    ],
                    'name': 'OBD',
                },
            })

def get_all_sensors(node_id: str):
    return [
        RawObdSensor(node_id, 'ELM_VERSION', cmds.ELM_VERSION),
        RawObdSensor(node_id, 'ELM_VOLTAGE', cmds.ELM_VOLTAGE),
        UnitObdSensor(node_id, 'RPM', cmds.RPM, units.rpm),
    ]
