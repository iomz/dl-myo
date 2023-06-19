"""
    myo.client
    ----------------
    MyoClient is a wrapper class to handle the connection to Myo devices.
"""
import asyncio
import binascii
import logging
import json

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic

from .constants import (
    RGB_CYAN,
    RGB_PINK,
    RGB_YELLOW,
    RGB_WHITE,
)
from .core import Myo
from .profile import Handle
from .types import (
    ClassifierEvent,
    ClassifierMode,
    EMGData,
    EMGMode,
    FVData,
    FirmwareInfo,
    FirmwareVersion,
    IMUData,
    IMUMode,
    MotionEvent,
    SleepMode,
    VibrationType,
)

logger = logging.getLogger(__name__)


class MyoClient:
    def __init__(self):
        self.m = None
        self.classifier_mode = None
        self.emg_mode = None
        self.imu_mode = None
        self._client = None

    @classmethod
    async def with_device(cls, mac=None):
        self = cls()
        while self.m is None:
            if mac and mac != "":
                self.m = await Myo.with_mac(mac)
            else:
                self.m = await Myo.with_uuid()

        await self.connect()
        return self

    @property
    def device(self):
        return self.m.device

    async def battery_level(self):
        """
        Battery Level Characteristic
        """
        return self.m.battery_level(self._client)

    async def connect(self):
        """
        <> connect the client to the myo device
        """
        self._client = BleakClient(self.device)
        if self._client is None:
            logger.error("connection failed")
            return None

        # connect to the device
        await self._client.connect()
        logger.info(f"connected to {self.device.name}: {self.device.address}")

    async def deep_sleep(self):
        """
        Deep Sleep Command
        """
        await self.m.deep_sleep(self._client)

    async def disconnect(self):
        """
        <> disconnect the client from the myo device
        """
        if self._client is None:
            logger.error("connection is already closed")

        # disconnect from the device
        await self._client.disconnect()
        self._client = None
        logger.info(f"disconnected from {self.device.name}")

    def emg_data_aggregate(self, handle, emg_data: EMGData):
        """
        <> aggregate the raw EMG data channels
        """
        if handle in [
            Handle.EMG0_DATA,
            Handle.EMG1_DATA,
            Handle.EMG2_DATA,
            Handle.EMG3_DATA,
        ]:
            self.on_emg_data(emg_data.sample1)
            self.on_emg_data(emg_data.sample2)

    async def get_services(self, indent=1) -> str:
        """
        <> fetch available services as dict
        """
        sd = {}
        for service in self._client.services:  # BleakGATTServiceCollection
            try:
                service_name = Handle(service.handle).name
            except Exception as e:
                logger.debug("unknown handle: {}", e)
                continue

            chars = {}
            for char in service.characteristics:  # List[BleakGATTCharacteristic]
                cd = await gatt_char_to_dict(self._client, char)
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

    async def led(self, color):
        """
        LED Command
        args:
            - color: myo.constants.RGB_*
        """
        await self.m.led(self._client, color, color)

    def on_classifier_event(self, ce: ClassifierEvent):
        raise NotImplementedError()

    def on_emg_data(self, emg):  # data: list of 8 8-bit unsigned short
        raise NotImplementedError()

    def on_fv_data(self, fvd: FVData):
        raise NotImplementedError()

    def on_imu_data(self, imu: IMUData):
        raise NotImplementedError()

    def on_motion_event(self, me: MotionEvent):
        raise NotImplementedError()

    def notify_callback(self, sender: BleakGATTCharacteristic, data: bytearray):
        """
        <> invoke the on_* callbacks
        """
        handle = Handle(sender.handle)
        if handle == Handle.CLASSIFIER_EVENT:
            self.on_classifier_event(ClassifierEvent(data))
        elif handle == Handle.FV_DATA:
            self.on_fv_data(FVData(data))
        elif handle == Handle.IMU_DATA:
            self.on_imu_data(IMUData(data))
        elif handle == Handle.MOTION_EVENT:
            self.on_motion_event(MotionEvent(data))
        else:  # on EMG[0-3]_DATA handle
            self.emg_data_aggregate(handle, EMGData(data))

    async def set_mode(self, emg_mode, imu_mode, classifier_mode):
        """
        Set Mode Command
            - configures EMG, IMU, and Classifier modes
        """
        await self.m.set_mode(self._client, emg_mode, imu_mode, classifier_mode)

    async def set_sleep_mode(self, sleep_mode):
        """
        Set Sleep Mode Command
        """
        await self.m.set_sleep_mode(self._client, sleep_mode)

    async def setup(
        self,
        emg_mode=EMGMode.SEND_FILT,
        imu_mode=IMUMode.NONE,
        classifier_mode=ClassifierMode.DISABLED,
    ):
        """
        <> setup the myo device
        """
        await self.led(RGB_YELLOW)
        logger.info(f"setting up the myo: {self.device.name}")
        battery = await self.m.battery_level(self._client)
        logger.info(f"remaining battery: {battery} %")
        # vibrate short *3
        await self.vibrate(VibrationType.SHORT)
        await self.vibrate(VibrationType.SHORT)
        await self.vibrate(VibrationType.SHORT)
        # never sleep
        await self.set_sleep_mode(SleepMode.NEVER_SLEEP)
        # setup modes
        self.emg_mode = emg_mode
        self.imu_mode = imu_mode
        self.classifier_mode = classifier_mode
        await self.set_mode(
            emg_mode,
            imu_mode,
            classifier_mode,
        )
        await self.led(RGB_PINK)

    async def sleep(self):
        """
        <> put the device to sleep
        """
        logger.info(f"sleep {self.device.name}")
        # led purple
        await self.led(RGB_PINK)
        # normal sleep
        await self.set_sleep_mode(SleepMode.NORMAL)
        await asyncio.sleep(0.5)
        await self.disconnect()

    async def start(self):
        """
        <> start notify/indicate
        """
        logger.info(f"start notifying from {self.device.name}")
        # vibrate short
        await self.vibrate(VibrationType.SHORT)
        # subscribe for notify/indicate
        if self.emg_mode in [EMGMode.SEND_EMG, EMGMode.SEND_RAW]:
            await self.start_notify(Handle.EMG0_DATA.value, self.notify_callback)
            await self.start_notify(Handle.EMG1_DATA.value, self.notify_callback)
            await self.start_notify(Handle.EMG2_DATA.value, self.notify_callback)
            await self.start_notify(Handle.EMG3_DATA.value, self.notify_callback)
        elif self.emg_mode == EMGMode.SEND_FILT:
            await self.start_notify(Handle.FV_DATA.value, self.notify_callback)
        if self.imu_mode not in [IMUMode.NONE, IMUMode.SEND_EVENTS]:
            await self.start_notify(Handle.IMU_DATA.value, self.notify_callback)
        if self.imu_mode in [IMUMode.SEND_EVENTS, IMUMode.SEND_ALL]:
            await self.start_notify(Handle.MOTION_EVENT.value, self.notify_callback)
        if self.classifier_mode == ClassifierMode.ENABLED:
            await self.start_notify(Handle.CLASSIFIER_EVENT.value, self.notify_callback)

        await self.led(RGB_CYAN)

    async def start_notify(self, handle, callback):
        await self._client.start_notify(handle, callback)

    async def stop(self):
        """
        <> stop notify/indicate
        """
        # vibrate short*2
        await self.vibrate(VibrationType.SHORT)
        await self.vibrate(VibrationType.SHORT)
        # unsubscribe from notify/indicate
        if self.emg_mode in [EMGMode.SEND_EMG, EMGMode.SEND_RAW]:
            await self.stop_notify(Handle.EMG0_DATA.value)
            await self.stop_notify(Handle.EMG1_DATA.value)
            await self.stop_notify(Handle.EMG2_DATA.value)
            await self.stop_notify(Handle.EMG3_DATA.value)
        elif self.emg_mode == EMGMode.SEND_FILT:
            await self.stop_notify(Handle.FV_DATA.value)
        if self.imu_mode not in [IMUMode.NONE, IMUMode.SEND_EVENTS]:
            await self.stop_notify(Handle.IMU_DATA.value)
        if self.imu_mode in [IMUMode.SEND_EVENTS, IMUMode.SEND_ALL]:
            await self.stop_notify(Handle.MOTION_EVENT.value)
        if self.classifier_mode == ClassifierMode.ENABLED:
            await self.stop_notify(Handle.CLASSIFIER_EVENT.value)

        await self.led(RGB_WHITE)
        logger.info(f"stopped notification from {self.device.name}")

    async def stop_notify(self, handle):
        await self._client.stop_notify(handle)

    async def unlock(self, unlock_type):
        """
        Unlock Command
        """
        await self.m.unlock(self._client, unlock_type)

    async def user_action(self, user_action_type):
        """
        User Action Command
        """
        await self.m.user_action(self._client, user_action_type)

    async def vibrate(self, vibration_type):
        """
        Vibrate Command
        """
        await self.m.vibrate(self._client, vibration_type)

    async def vibrate2(self, duration, strength):
        """
        Vibrate2 Command
        """
        await self.m.vibrate2(self._client, duration, strength)


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
