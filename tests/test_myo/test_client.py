import pytest
from myo import MyoClient

# from myo.types import ClassifierEvent, FVData, IMUData, MotionEvent


# class Client(MyoClient):
#     async def on_classifier_event(self, ce: ClassifierEvent):
#         pass
#
#     async def on_emg_data(self, emg):
#         pass
#
#     async def on_fv_data(self, fvd: FVData):
#         pass
#
#     async def on_imu_data(self, imu: IMUData):
#         pass
#
#     async def on_motion_event(self, me: MotionEvent):
#         pass


@pytest.mark.asyncio
async def test_client():
    mc = MyoClient()
    assert mc._client is None
    # await tc.
