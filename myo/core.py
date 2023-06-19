"""
    myo.core
    ----------------
    The core (i.e., _row_) Myo BLE device manager.
"""
import logging
from bleak import BleakClient, BleakScanner
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
from .profile import (
    GATTProfile,
    Handle,
)

logger = logging.getLogger(__name__)


class Myo:
    __slots__ = "_device"

    def __init__(self):
        pass

    @property
    def device(self) -> BLEDevice:
        return self._device

    @classmethod
    async def with_mac(cls, mac: str):
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

        return self

    @classmethod
    async def with_uuid(cls):
        def match_myo_uuid(_: BLEDevice, adv: AdvertisementData):
            if str(GATTProfile.MYO_SERVICE).lower() in adv.service_uuids:
                return True
            return False

        self = cls()
        # scan the device
        self._device = await BleakScanner.find_device_by_filter(match_myo_uuid, cb=dict(use_bdaddr=True))
        if self.device is None:
            logger.error(f"could not find device with service UUID {GATTProfile.MYO_SERVICE}")
            return None

        return self

    async def battery_level(self, client: BleakClient):
        """
        Battery Level Characteristic
        """
        val = await client.read_gatt_char(Handle.BATTERY_LEVEL.value)
        return ord(val)

    async def command(self, client: BleakClient, cmd: Command):
        """
        Command Characteristic
        """
        await client.write_gatt_char(Handle.COMMAND.value, cmd.data, True)

    async def deep_sleep(self, client: BleakClient):
        """
        Deep Sleep Command
        """
        await self.command(client, DeepSleep())

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

    async def write(self, client: BleakClient, handle, value):
        """
        Write characteristic
        """
        await client.write_gatt_char(handle, value, True)
