import logging

from myo import MyoClient
from myo.types import ClassifierEvent, FVData, IMUData, MotionEvent

logger = logging.getLogger(__name__)


class TestClient(MyoClient):
    async def on_classifier_event(self, ce: ClassifierEvent):
        logger.info(ce)

    async def on_emg_data(self, emg):
        logger.info(emg)

    async def on_fv_data(self, fvd: FVData):
        logger.info(fvd)

    async def on_imu_data(self, imu: IMUData):
        logger.info(imu)

    async def on_motion_event(self, me: MotionEvent):
        logger.info(me)


def test_client():
    tc = TestClient()
    assert tc._client is None
