# -*- coding: utf-8 -*-
from __future__ import annotations

import binascii
import json
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .commands import Command, SetMode, Vibrate, DeepSleep, LED, Vibrate2, SetSleepMode, Unlock, UserAction
from .handle import Handle, UUID
from .types import FirmwareInfo, FirmwareVersion

# from .quaternion import Quaternion

logger = logging.getLogger(__name__)


class Device:
    __slots__ = ("__device", "__name")

    def __init__(self):
        pass

    @property
    def device(self) -> BLEDevice:
        return self.__device

    @property
    def name(self) -> str:
        return self.__name

    @classmethod
    async def with_mac(cls, mac: str) -> Device:
        def match_myo_mac(device: BLEDevice, _: AdvertisementData):
            if mac.lower() == device.address.lower():
                return True
            return False

        self = cls()
        try:
            # scan the device
            self.__device = await BleakScanner.find_device_by_filter(match_myo_mac, cb=dict(use_bdaddr=True))
            if self.device is None:
                logger.error(f"could not find device with address {mac}")
                return self
        except Exception as e:
            logger.error("the mac address may be invalid", e)
            return self

        # get the device name
        self.__name = str(self.device.name)

        return self

    @classmethod
    async def with_uuid(cls) -> Device:
        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData):
            if str(UUID.MYO_SERVICE).lower() in adv.service_uuids:
                return True
            return False

        self = cls()
        # scan the device
        self.__device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if self.device is None:
            logger.error(f"could not find device with service UUID {UUID.MYO_SERVICE}")
            return self

        # get the device name
        self.__name = str(self.device.name)

        return self

    async def battery_level(self, client: BleakClient):
        """
        Battery Level Characteristic
        """
        val = await client.read_gatt_char(Handle.BATTERY_LEVEL)
        return ord(val)

    async def command(self, client: BleakClient, cmd: Command):
        """
        Command Characteristic
        """
        await client.write_gatt_char(Handle.COMMAND.value, cmd.data, True)  # pyright: ignore

    async def deep_sleep(self, client: BleakClient):
        """
        Deep Sleep Command
        """
        await self.command(client, DeepSleep())

    async def emg_service(self, client):
        """
        EMG Service
        """
        await client.write_gatt_char(Handle.EMG_SERVICE.value, b"\x01\x00", True)  # pyright: ignore

    async def get_services(self, client: BleakClient, indent=2) -> str:  # noqa: C901
        """fetch available services as dict"""
        sd = {"services": {}}
        for service in client.services:  # BleakGATTServiceCollection
            try:
                service_name = Handle(service.handle).name  # pyright: ignore
            except Exception as e:
                logger.debug("unknown handle: {}", e)
                continue

            sd["services"][service.handle] = {
                "name": service_name,
                "uuid": service.uuid,
                "chars": {},
            }
            for char in service.characteristics:  # List[BleakGATTCharacteristic]
                try:
                    char_name = Handle(char.handle).name  # pyright: ignore
                except Exception as e:
                    logger.debug("unknown handle: {}", e)
                    continue

                sd["services"][service.handle]["chars"][char.handle] = {
                    "name": char_name,
                    "uuid": char.uuid,
                }

                sd["services"][service.handle]["chars"][char.handle]["properties"] = ",".join(char.properties)
                if "read" in char.properties:
                    blob = await client.read_gatt_char(char.handle)
                    if char_name == Handle.MANUFACTURER_NAME_STRING.name:  # pyright: ignore
                        value = blob.decode("utf-8")
                    elif char_name == Handle.FIRMWARE_INFO.name:  # pyright: ignore
                        value = FirmwareInfo(blob).to_dict()
                    elif char_name == Handle.FIRMWARE_VERSION.name:  # pyright: ignore
                        value = str(FirmwareVersion(blob))
                    elif char_name == Handle.BATTERY_LEVEL.name:  # pyright: ignore
                        value = ord(blob)
                    else:
                        value = binascii.b2a_hex(blob).decode("utf-8")
                    sd["services"][service.handle]["chars"][char.handle]["value"] = value
            # end char
        # end service

        return json.dumps(sd, indent=indent)

    async def led(self, client: BleakClient, *args):
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

        await self.command(client, LED(args[0], args[1]))

    async def set_mode(self, client: BleakClient, emg_mode, imu_mode, classifier_mode):
        """
        Set Mode Command
            - configures EMG, IMU, and Classifier modes
        """
        await self.command(client, SetMode(emg_mode, imu_mode, classifier_mode))

    async def set_sleep_mode(self, client: BleakClient, sleep_mode):
        """
        Set Sleep Mode Command
        """
        await self.command(client, SetSleepMode(sleep_mode))

    async def unlock(self, client: BleakClient, unlock_type):
        """
        Unlock Command
        """
        await self.command(client, Unlock(unlock_type))

    async def user_action(self, client: BleakClient, user_action_type):
        """
        User Action Command
        """
        await self.command(client, UserAction(user_action_type))

    async def vibrate(self, client: BleakClient, vibration_type):
        """
        Vibrate Command
        """
        await self.command(client, Vibrate(vibration_type))

    async def vibrate2(self, client: BleakClient, duration, strength):
        """
        Vibrate2 Command
        """
        await self.command(client, Vibrate2(duration, strength))
