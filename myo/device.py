# -*- coding: utf-8 -*-
from __future__ import annotations

import binascii
import logging

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from .commands import *
from .handle import *
from .types import *

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
        except:
            logger.error("the mac address may be invalid")
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

    async def get_services(self, client: BleakClient) -> dict:
        """fetch available services as dict"""
        sd = {"services": {}}
        for service in client.services:  # BleakGATTServiceCollection
            service_id = service.uuid[4:8]
            service_name = Services.get(int(service_id, base=16))

            if not service_name:  # unknown service
                continue

            sd["services"][service_id] = {
                "name": service_name,
                "handle": service.handle,
                "uuid": service.uuid,
                "chars": {},
            }
            for char in service.characteristics:  # List[BleakGATTCharacteristic]
                char_id = char.uuid[4:8]
                char_name = Services.get(int(char_id, base=16))

                if not char_name:  # unknown characteristic
                    continue

                sd["services"][service_id]["chars"][char_id] = {
                    "name": char_name,
                    "handle": char.handle,
                    "uuid": char.uuid,
                }

                sd["services"][service_id]["chars"][char_id]["properties"] = ",".join(char.properties)
                if "read" in char.properties:
                    blob = await client.read_gatt_char(char.uuid)
                    if char_name == "ManufacturerNameString":
                        value = blob.decode("utf-8")
                    else:
                        value = binascii.b2a_hex(blob).decode("utf-8")
                    sd["services"][service_id]["chars"][char_id]["value"] = value
            # end char
        # end service

        return sd

    async def led(self, client: BleakClient, *args):
        """
        LED Command
            - set leds color

        *args: [logoR, logoG, logoB], [lineR, lineG, lineB]
        """

        if not isinstance(args, tuple) or len(args) != 2:
            raise Exception(f"Unknown payload for LEDs: {args}")

        for l in args:
            if any(not isinstance(v, int) for v in l):
                raise Exception(f"Values must be int 0-255: {l}")

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

    """
    def handleNotification(self, handle_enum, data):
        if handle_enum == Handle.CLASSIFIER:
            # sometimes gets the poses mixed up, if this happens, try wearing it in a different orientation.
            data = struct.unpack(">6b", data)
            try:
                ev_type = ClassifierEvent(data[0])
            except:
                raise Exception("Unknown classifier event: " + str(data[0]))
            if ev_type == ClassifierEvent.POSE:
                self.state.pose = Pose(data[1])
                if self.state.pose == Pose.UNSYNC:
                    self.state.synced = False
                    self.state.arm = Arm.UNSYNC
                    self.state.pose = Pose.UNSYNC
                    self.state.x_direction = XDirection.UNSYNC
                    self.state.startq = Quaternion(0, 0, 0, 1)
                else:
                    self.state.napq = self.state.imu.quat.copy()
                    self.on_pose(self.state)

            elif ev_type == ClassifierEvent.SYNC:
                self.state.synced = True
                # rewrite handles
                self.state.arm = Arm(data[1])
                self.state.x_direction = XDirection(data[2])
                self.state.startq = self.state.imu.quat.copy()
                self.on_sync(self.state)

            elif ev_type == ClassifierEvent.UNSYNC:
                self.state.synced = False
                self.state.arm = Arm.UNSYNC
                self.state.x_direction = XDirection.UNSYNC
                self.state.pose = Pose.UNSYNC
                self.state.startq = Quaternion(0, 0, 0, 1)
                self.on_unsync(self.state)

            elif ev_type == ClassifierEvent.UNLOCK:
                self.on_unlock(self.state)

            elif ev_type == ClassifierEvent.LOCK:
                self.on_lock(self.state)

            elif ev_type == ClassifierEvent.SYNCFAIL:
                self.state.synced = False
                self.on_sync_failed(self.state)

            elif ev_type == ClassifierEvent.WARMUP:
                self.on_warmup(self.state)

        elif handle_enum == Handle.IMU:
            self.state.imu = IMU(data)
            self.on_imu(self.state)

        elif handle_enum == Handle.EMG:
            self.state.emg = EMG(data)
            self.on_emg(self.state)
    """
