from obd import OBDCommand
from obd.decoders import *
from obd.protocols import ECU

__prius__ = [
    #                      name                             description                    cmd  bytes       decoder           ECU         fast   header
    # OBDCommand("WHEEL_SPEED",                   "Wheel Speed",                            b"2103", 4, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2105", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("STEERING",                      "Deceleration",                           b"2106", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("WHEEL_CYLINDER_PRESSURE",       "Deceleration",                           b"2107", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("WHEEL_CYLINDER_PRESSURE",       "Deceleration",                           b"211D", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"211F", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2121", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"213C", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"213D", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2142", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2146", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2147", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2148", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"2158", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"215A", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"215F", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"21A1", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"21A3", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"21A6", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"21BC", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
    # OBDCommand("DECELERATION",                  "Deceleration",                           b"21BE", 2, raw_string,             ECU.ENGINE, True, b"7B0"),
]

commands = __prius__
