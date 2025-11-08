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
    Convert a GATT characteristic to a dictionary representation.

    Args:
        client: The BleakClient instance
        char: The GATT characteristic to convert

    Returns:
        Dictionary representation of the characteristic, or None if conversion fails
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
        elif char_name == Handle.BATTERY_LEVEL.name:
            value = ord(blob)
        else:
            value = binascii.b2a_hex(blob).decode("utf-8")

    if value:
        cd["value"] = value
    return cd

