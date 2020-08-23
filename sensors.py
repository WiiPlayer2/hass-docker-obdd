import abc
import json
import logging
from obd import commands as cmds, OBDCommand, Unit as units, Async as OBDAsync, OBDResponse
from paho.mqtt.client import Client as MqttClient
from commands import custom_commands

logger = logging.getLogger(__name__)

__unit_symbols__ = {
    # units.percent: '%',
}

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
    def __init__(self, node_id: str, name: str, cmd: OBDCommand, component: str):
        self._node_id = node_id
        self._name = name
        self._cmd = cmd
        self._component = component

    @property
    def name(self):
        return self._name

    @property
    def cmd(self):
        return self._cmd

    def register(self, discovery_prefix: str, mqtt_client: MqttClient, obd: OBDAsync):
        def callback(value):
            logger.debug(f'Incoming value for {self.cmd} -> {value}')
            try:
                self._process_value(mqtt_client, value)
            except Exception as e:
                logger.error(f'Error while processing value. ({self.cmd} -> {value})', exc_info=e)
        info = self._get_discovery_info(discovery_prefix)
        mqtt_client.publish(info.topic, json.dumps(info.payload), retain=True)
        obd.watch(self._cmd, callback)

    def _get_discovery_info(self, discovery_prefix: str) -> DiscoveryInfo:
        payload = {
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
        payload.update(self._get_additional_discovery_configuration())
        return DiscoveryInfo(
            discovery_prefix,
            self._node_id,
            self._uid,
            self._component,
            payload)

    @abc.abstractmethod
    def _get_additional_discovery_configuration(self) -> dict:
        pass

    @abc.abstractmethod
    def _process_value(self, mqtt_client: MqttClient, value: OBDResponse):
        pass

    @property
    def _uid(self):
        return f'{self._node_id}_{self.name}_{self._cmd.header.decode()}{self._cmd.command.decode()}'

    @property
    def _state_topic(self):
        return f'obd/{self._uid}'
    
    @property
    def _entity_name(self):
        return f'{self._node_id}_{self.name.lower()}'

class UnitObdSensor(ObdSensor):
    def __init__(self, node_id: str, name: str, cmd: OBDCommand, unit, device_class: str = None):
        super().__init__(node_id, name, cmd, 'sensor')
        self._unit = unit
        self._device_class = device_class
    
    def _process_value(self, mqtt_client: MqttClient, value: OBDResponse):
        mqtt_client.publish(self._state_topic, value.value.magnitude)

    def _get_additional_discovery_configuration(self):
        unit_of_measurement = __unit_symbols__.get(self._unit)
        if not unit_of_measurement:
            unit_of_measurement = '{:~P}'.format(self._unit)
        if not unit_of_measurement:
            unit_of_measurement = '{:P}'.format(self._unit)
        if not unit_of_measurement:
            unit_of_measurement = str(self._unit)
        payload = {
                'unit_of_measurement': unit_of_measurement,
        }
        if self._device_class is not None:
            payload.update({'device_class': self._device_class})
        return payload

class RawObdSensor(ObdSensor):
    def __init__(self, node_id: str, name: str, cmd: OBDCommand):
        super().__init__(node_id, name, cmd, 'sensor')

    def _process_value(self, mqtt_client: MqttClient, value: OBDResponse):
        mqtt_client.publish(self._state_topic, str(value))
    
    def _get_additional_discovery_configuration(self):
        return {}

class SelectUnitObdSensor(UnitObdSensor):
    def __init__(self, node_id: str, name: str, cmd: OBDCommand, unit, selector, device_class: str = None):
        super().__init__(node_id, name, cmd, unit, device_class)
        self._selector = selector
    
    def _process_value(self, mqtt_client: MqttClient, value: OBDResponse):
        mqtt_client.publish(self._state_topic, self._selector(value.value))


def get_all_sensors(node_id: str):
    return [
        # OBD-II Adapter
        RawObdSensor(node_id, 'ELM_VERSION', cmds.ELM_VERSION),
        UnitObdSensor(node_id, 'ELM_VOLTAGE', cmds.ELM_VOLTAGE, units.volt),

        # Mode 01
        UnitObdSensor(node_id, 'ENGINE_LOAD', cmds.ENGINE_LOAD, units.percent),
        UnitObdSensor(node_id, 'INTAKE_PRESSURE', cmds.INTAKE_PRESSURE, units.kilopascal, 'pressure'),
        UnitObdSensor(node_id, 'RPM', cmds.RPM, units.rpm),
        UnitObdSensor(node_id, 'SPEED', cmds.SPEED, units.kph),
        UnitObdSensor(node_id, 'INTAKE_TEMP', cmds.INTAKE_TEMP, units.celsius, 'temperature'),
        UnitObdSensor(node_id, 'THROTTLE_POS', cmds.THROTTLE_POS, units.percent),
        UnitObdSensor(node_id, 'RUN_TIME', cmds.RUN_TIME, units.second),
        UnitObdSensor(node_id, 'FUEL_LEVEL', cmds.FUEL_LEVEL, units.percent),
        UnitObdSensor(node_id, 'ABSOLUTE_LOAD', cmds.ABSOLUTE_LOAD, units.percent),
        UnitObdSensor(node_id, 'RELATIVE_THROTTLE_POS', cmds.RELATIVE_THROTTLE_POS, units.percent),
        UnitObdSensor(node_id, 'HYBRID_BATTERY_REMAINING', cmds.HYBRID_BATTERY_REMAINING, units.percent, 'battery'),

        # Custom
        UnitObdSensor(node_id, 'FUEL_LEVEL_7C0', custom_commands.FUEL_LEVEL, units.liter),
        SelectUnitObdSensor(node_id, 'BATTERY_CURRENT', custom_commands.HV_BATTERY_STATUS, units.ampere, lambda x: x['battery_current'].magnitude),
        SelectUnitObdSensor(node_id, 'BATTERY_CHARGE', custom_commands.HV_BATTERY_STATUS, units.kilowatt, lambda x: x['charge_control'].magnitude),
        SelectUnitObdSensor(node_id, 'BATTERY_DISCHARGE', custom_commands.HV_BATTERY_STATUS, units.kilowatt, lambda x: x['discharge_control'].magnitude),
        SelectUnitObdSensor(node_id, 'DELTA_SOC', custom_commands.HV_BATTERY_STATUS, units.percent, lambda x: x['delta_soc'].magnitude),
        SelectUnitObdSensor(node_id, 'SOC_IGNITION', custom_commands.HV_BATTERY_STATUS, units.percent, lambda x: x['soc_ign'].magnitude),
        SelectUnitObdSensor(node_id, 'SOC_MAX', custom_commands.HV_BATTERY_STATUS, units.percent, lambda x: x['soc_max'].magnitude),
        SelectUnitObdSensor(node_id, 'SOC_MIN', custom_commands.HV_BATTERY_STATUS, units.percent, lambda x: x['soc_min'].magnitude),
        SelectUnitObdSensor(node_id, 'LATERAL_G', custom_commands.GFORCE_AND_YAW,  units.meter / units.second ** 2, lambda x: x['lateral_g'].magnitude),
        SelectUnitObdSensor(node_id, 'LINEAL_G', custom_commands.GFORCE_AND_YAW,  units.meter / units.second ** 2, lambda x: x['lineal_g'].magnitude),
        SelectUnitObdSensor(node_id, 'YAW_RATE', custom_commands.GFORCE_AND_YAW, units.degree / units.second, lambda x: x['yaw_rate'].magnitude),
        SelectUnitObdSensor(node_id, 'STEERING_ANGLE', custom_commands.GFORCE_AND_YAW, units.degree, lambda x: x['steering_angle'].magnitude),
        UnitObdSensor(node_id, 'STATE_OF_CHARGE', custom_commands.STATE_OF_CHARGE, units.percent, 'battery'),
    ]
