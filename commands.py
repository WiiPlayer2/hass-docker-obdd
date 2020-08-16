import abc
import json
from obd import commands as cmds, OBDCommand, Unit as units, Async as OBDAsync
from paho.mqtt.client import Client as MqttClient

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
    def __init__(self, name: str, cmd: OBDCommand):
        self._name = name
        self._cmd = cmd

    @property
    def name(self):
        return self._name

    @property
    def cmd(self):
        return self._cmd

    def register(self, discovery_prefix: str, node_id: str, mqtt_client: MqttClient, obd: OBDAsync):
        def callback(value):
            self._process_value(node_id, mqtt_client, value)
        info = self._get_discovery_info(discovery_prefix, node_id)
        mqtt_client.publish(info.topic, json.dumps(info.payload))
        obd.watch(self._cmd, callback)

    @abc.abstractmethod
    def _get_discovery_info(self, discovery_prefix: str, node_id: str) -> DiscoveryInfo:
        pass

    @abc.abstractmethod
    def _process_value(self, node_id: str, mqtt_client: MqttClient, value):
        pass

    def _uid(self, node_id: str):
        return f'{node_id}_{self._cmd.name}_{self._cmd.header.decode()}{self._cmd.command.decode()}'

class UnitObdSensor(ObdSensor):
    def __init__(self, name: str, cmd: OBDCommand, unit, device_class: str = None):
        super().__init__(name, cmd)
        self._unit = unit
        self._device_class = device_class
    
    def _process_value(self, node_id: str, mqtt_client: MqttClient, value):
        mqtt_client.publish(f'obd/{self._uid(node_id)}', value.magnitude)

    def _get_discovery_info(self, discovery_prefix: str, node_id: str):
        payload = {
                'unit_of_measurement': str(self._unit),
                'state_topic': f'obd/{self._uid(node_id)}',
                'name': self._cmd.name,
                'unique_id': self._uid(node_id),
                'device': {
                    'identifiers': [
                        f'obd_{node_id}',
                    ],
                    'name': 'OBD',
                },
            }
        if self._device_class is not None:
            payload.update({'device_class': self._device_class})
        return DiscoveryInfo(
            discovery_prefix,
            node_id,
            self._uid(node_id),
            'sensor',
            payload)

class RawObdSensor(ObdSensor):
    def __init__(self, name: str, cmd: OBDCommand):
        super().__init__(name, cmd)

    def _process_value(self, node_id: str, mqtt_client: MqttClient, value):
        mqtt_client.publish(f'obd/{self._uid(node_id)}', value)
    
    def _get_discovery_info(self, discovery_prefix: str, node_id: str):
        return DiscoveryInfo(
            discovery_prefix,
            node_id,
            self._uid(node_id),
            'sensor',
            {
                'state_topic': f'obd/{self._uid(node_id)}',
                'name': self._cmd.name,
                'unique_id': self._uid(node_id),
                'device': {
                    'identifiers': [
                        f'obd_{node_id}',
                    ],
                    'name': 'OBD',
                },
            })

all_commands = [
    RawObdSensor('ELM_VERSION', cmds.ELM_VERSION),
    RawObdSensor('ELM_VOLTAGE', cmds.ELM_VOLTAGE),
    UnitObdSensor('RPM', cmds.RPM, units.rpm),
]
