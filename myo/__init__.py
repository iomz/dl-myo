# -*- coding: utf-8 -*-
"""
    Top-level package for dl-myo
~~~~~~~~~~~~~~~~~~~~
   >>> import myo
"""

from __future__ import annotations

__author__ = """Iori Mizutani"""
__email__ = "iori.mizutani@gmail.com"

from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)

import binascii
import json
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


from .commands import (
    Command,
    SetMode,
    Vibrate,
    DeepSleep,
    LED,
    Vibrate2,
    SetSleepMode,
    Unlock,
    UserAction,
)
from .handle import Handle, UUID
from .types import FirmwareInfo, FirmwareVersion

logger = logging.getLogger(__name__)


class Myo:
    __slots__ = ("_client", "_device")

    def __init__(self):
        pass

    @property
    def client(self) -> BleakClient:
        return self._client

    @property
    def device(self) -> BLEDevice:
        return self._device

    @classmethod
    async def with_mac(cls, mac: str) -> Myo:
        def match_myo_mac(device: BLEDevice, _: AdvertisementData):
            if mac.lower() == device.address.lower():
                return True
            return False

        self = cls()
        try:
            # scan the device
            self._device = await BleakScanner.find_device_by_filter(match_myo_mac, cb=dict(use_bdaddr=True))
            if self.device is None:
                logger.error(f"could not find device with address {mac}")
                return None
        except Exception as e:
            logger.error("the mac address may be invalid", e)
            return None

        await self.connect()
        return self

    @classmethod
    async def with_uuid(cls) -> Myo:
        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData):
            if str(UUID.MYO_SERVICE).lower() in adv.service_uuids:
                return True
            return False

        self = cls()
        # scan the device
        self._device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if self.device is None:
            logger.error(f"could not find device with service UUID {UUID.MYO_SERVICE}")
            return None

        await self.connect()
        return self

    async def battery_level(self):
        """
        Battery Level Characteristic
        """
        val = await self.client.read_gatt_char(Handle.BATTERY_LEVEL.value)
        return ord(val)

    async def command(self, cmd: Command):
        """
        Command Characteristic
        """
        await self.client.write_gatt_char(Handle.COMMAND.value, cmd.data, True)

    async def connect(self):
        self._client = BleakClient(self.device)
        if self.client is None:
            logger.error("connection failed")
            return None

        # connect to the device
        await self.client.connect()
        logger.info(f"connected to {self.device.name}")

    async def deep_sleep(self, client: BleakClient):
        """
        Deep Sleep Command
        """
        await self.command(client, DeepSleep())

    async def disconnect(self):
        if self.client is None:
            logger.error("connection is already closed")

        # disconnect from the device
        await self.client.disconnect()
        self._client = None
        logger.info(f"disconnected from {self.device.name}")

    async def get_services(self, indent=2) -> str:
        """fetch available services as dict"""
        sd = {}
        for service in self.client.services:  # BleakGATTServiceCollection
            try:
                service_name = Handle(service.handle).name
            except Exception as e:
                logger.debug("unknown handle: {}", e)
                continue

            chars = {}
            for char in service.characteristics:  # List[BleakGATTCharacteristic]
                cd = await gatt_char_to_dict(self.client, char)
                if cd:
                    chars[hex(char.handle)] = cd

            # end char
            sd[hex(service.handle)] = {
                "name": service_name,
                "uuid": service.uuid,
                "chars": chars,
            }
        # end service
        return json.dumps({"services": sd}, indent=indent)

    async def led(self, *args):
        """
        LED Command
            - set leds color

        *args: [logoR, logoG, logoB], [lineR, lineG, lineB]
        """

        if not isinstance(args, tuple) or len(args) != 2:
            raise Exception(f"Unknown payload for LEDs: {args}")

        for lst in args:
            if any(not isinstance(v, int) for v in lst):
                raise Exception(f"Values must be int 0-255: {lst}")

        await self.command(LED(args[0], args[1]))

    async def set_mode(self, emg_mode, imu_mode, classifier_mode):
        """
        Set Mode Command
            - configures EMG, IMU, and Classifier modes
        """
        await self.command(SetMode(emg_mode, imu_mode, classifier_mode))

    async def set_sleep_mode(self, sleep_mode):
        """
        Set Sleep Mode Command
        """
        await self.command(SetSleepMode(sleep_mode))

    async def unlock(self, unlock_type):
        """
        Unlock Command
        """
        await self.command(Unlock(unlock_type))

    async def user_action(self, user_action_type):
        """
        User Action Command
        """
        await self.command(UserAction(user_action_type))

    async def vibrate(self, vibration_type):
        """
        Vibrate Command
        """
        await self.command(Vibrate(vibration_type))

    async def vibrate2(self, duration, strength):
        """
        Vibrate2 Command
        """
        await self.command(Vibrate2(duration, strength))

    async def write(self, handle, value):
        """
        Write characteristic
        """
        await self.client.write_gatt_char(handle, value, True)


async def gatt_char_to_dict(client: BleakClient, char: BleakGATTCharacteristic):
    try:
        char_name = Handle(char.handle).name
    except Exception as e:
        logger.debug("unknown handle: {}", e)
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
