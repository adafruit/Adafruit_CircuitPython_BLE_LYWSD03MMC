# SPDX-FileCopyrightText: 2021 Dan Halbert, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2021 Adafruit Industries for Adafruit Industries LLC
#
# SPDX-License-Identifier: MIT
"""
`adafruit_ble_lywsd03mmc`
================================================================================

BLE Support for Xiaomi LYWSD03MMC Thermometer/Hygrometer


* Author(s): Adafruit Industries

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases
"""

import struct

import _bleio
from adafruit_ble.services import Service
from adafruit_ble.uuid import VendorUUID
from adafruit_ble.characteristics import Characteristic, ComplexCharacteristic

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_BLE_LYWSD03MMC.git"


class _Readings(ComplexCharacteristic):
    """Notify-only characteristic of temperature/humidity"""

    uuid = VendorUUID("ebe0ccc1-7a0a-4b0c-8a1a-6ff2997da3a6")

    def __init__(self):
        super().__init__(properties=Characteristic.NOTIFY)

    def bind(self, service):
        """Bind to an LYWSD03MMCService."""
        bound_characteristic = super().bind(service)
        bound_characteristic.set_cccd(notify=True)
        # Use a PacketBuffer that can store one packet to receive the data.
        return _bleio.PacketBuffer(bound_characteristic, buffer_size=1)


class LYWSD03MMCService(Service):
    """Service for reading from an LYWSD03MMC sensor."""

    def __init__(self, service=None):
        super().__init__(service=service)
        # Defer creating buffers until needed, since MTU is not known yet.
        self._settings_result_buf = None
        self._readings_buf = None

    uuid = VendorUUID("ebe0ccb0-7a0a-4b0c-8a1a-6ff2997da3a6")

    readings = _Readings()

    @property
    def temperature_humidity(self):
        """Return a tuple of (temperature, humidity)."""
        if self._readings_buf is None:
            self._readings_buf = bytearray(self.readings.incoming_packet_length)
        data = self._readings_buf
        length = self.readings.readinto(data)
        if length > 0:
            low_temp, high_temp, hum = struct.unpack_from("<BBB", data)
            sign = high_temp & 0x80
            temp = ((high_temp & 0x7F) << 8) | low_temp
            if sign:
                temp = temp - 32767
            temp = temp / 100
            return (temp, hum)
        # No data.
        return None
