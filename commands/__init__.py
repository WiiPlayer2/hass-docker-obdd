from obd import OBDCommand, Unit as units
from obd.decoders import raw_string
from obd.protocols import ECU
from .decoders import *

# https://docs.google.com/spreadsheets/d/1Mmlb-SHATQBuTa_3tORdKQatSbvdIouEdMZcasXJghk/edit#gid=2

custom_commands = [
    # Name, Description, Command, Bytes, Decoder, ECU, Fast, Header
    OBDCommand('FUEL_LEVEL',        'Fuel Level',                       b'2129', 1, fuel_level,         ECU.ALL, True, b'7C0'),
    OBDCommand('HV_BATTERY_STATUS', 'HV Battery Status',                b'2198', 8, hv_battery_status,  ECU.ALL, True, b'7E2'),
    OBDCommand('GFORCE_AND_YAW',    'G-Force, Yaw and Steering Angle',  b'2147', 5, raw_string,         ECU.ALL, True, b'7B0'),
]