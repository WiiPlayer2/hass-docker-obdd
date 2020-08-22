import logging
import json
from typing import List
from obd import Unit as units
from obd.protocols.protocol import Message

logger = logging.getLogger(__name__)

# https://docs.google.com/spreadsheets/d/1Mmlb-SHATQBuTa_3tORdKQatSbvdIouEdMZcasXJghk/edit#gid=2

def _log(name, messages: List[Message]):
    data = messages
    try:
        data = [{
            'hex': str(m.hex()),
            'raw': str(m.raw()),
        } for m in messages]
    except:
        pass
    representation = repr(data)
    try:
        representation = json.dumps(data, indent=2)
    except:
        pass
    logger.debug(f'{name} <- {representation}')

def fuel_level(messages):
    _log('fuel_level', messages)
    d = messages[0].data
    v = d[0]
    v = v / 2
    return v * units.liter

def hv_battery_status(messages):
    _log('hv_battery_status', messages)
    d = messages[0].data
    battery_current = ((d[0] * 256 + d[1]) / 100) - 327.68
    charge_control = (d[2] / 2) - 64
    discharge_control = (d[3] / 2) - 64
    delta_soc = d[4] / 2
    soc_ign = d[5] / 2
    soc_max = d[6] / 2
    soc_min = d[7] / 2
    return {
        'battery_current': battery_current * units.ampere,
        'charge_control': charge_control * units.kilowatt,
        'discharge_control': discharge_control * units.kilowatt,
        'delta_soc': delta_soc * units.percent,
        'soc_ign': soc_ign * units.percent,
        'soc_max': soc_max * units.percent,
        'soc_min': soc_min * units.percent,
    }

def gforce_and_yaw(messages):
    _log('gforce_and_yaw', messages)
    d = messages[0].data
    lateral_g = (d[0] * 50.02 / 255) - 25.11
    lineal_g = (d[1] * 50.02 / 255) - 25.11
    yaw_rate = d[2] - 128
    steering_angle = ((d[3] * 256 + d[4]) / 10) - 3276.8
    return {
        'lateral_g': lateral_g * units.meter / units.second ** 2,
        'lineal_g': lineal_g * units.meter / units.second ** 2,
        'yaw_rate': yaw_rate * units.degree / units.second,
        'steering_angle': steering_angle * units.degree,
    }

def state_of_charge(messages):
    _log('state_of_charge', messages)
    d = messages[0].data
    v = d[0]
    v = v * 20 / 51
    return v * units.percent
