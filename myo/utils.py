"""
myo.utils
------------
Utility functions for GATT characteristic handling
"""

import binascii
import logging
from typing import Optional

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from .profile import Handle
from .types import FirmwareInfo, FirmwareVersion

logger = logging.getLogger(__name__)


async def gatt_char_to_dict(client: BleakClient, char: BleakGATTCharacteristic) -> Optional[dict]:
    """
    Convert a GATT characteristic into a serializable dictionary
    with a human-readable name, UUID, properties, and optionally its value.

    Parameters:
        client (BleakClient): BLE client used to read the characteristic value when the characteristic is readable.
        char (BleakGATTCharacteristic): The characteristic to convert.

    Returns:
        dict | None: A dictionary containing:
            - "name" (str): Human-readable characteristic name.
            - "uuid" (str): Characteristic UUID.
            - "properties" (str): Comma-separated characteristic properties.
            - "value" (varies, optional): Decoded value when the characteristic is readable:
                - Manufacturer Name String: UTF-8 decoded `str`.
                - Firmware Info: `dict` from `FirmwareInfo.to_dict()`.
                - Firmware Version: `str` representation of `FirmwareVersion`.
                - Battery Level: `int` interpreted from little-endian bytes.
                - Other readable characteristics: hex-encoded `str`.
          Returns `None` if the characteristic handle cannot be mapped to a known name.
    """
    try:
        char_name = Handle(char.handle).name
    except Exception as e:
        logger.debug("unknown handle: %s", e)
        return None

    cd = {
        "name": char_name,
        "uuid": char.uuid,
        "properties": ",".join(char.properties),
    }
    value = None
    if "read" in char.properties:
        blob = await client.read_gatt_char(char.handle)
        if char_name == Handle.MANUFACTURER_NAME_STRING.name:
            value = blob.decode("utf-8")
        elif char_name == Handle.FIRMWARE_INFO.name:
            value = FirmwareInfo(blob).to_dict()
        elif char_name == Handle.FIRMWARE_VERSION.name:
            value = str(FirmwareVersion(blob))
        elif char_name == Handle.BATTERY_LEVEL.name and blob:
            value = int.from_bytes(blob, "little")
        else:
            value = binascii.b2a_hex(blob).decode("utf-8")

    if value is not None:
        cd["value"] = value
    return cd
