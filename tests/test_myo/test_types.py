import pytest
from myo.types import ClassifierEvent, EMGData, FirmwareInfo, FirmwareVersion, FVData, IMUData, MotionEvent


# (Handle.CLASSIFIER_EVENT): bytearray(b'\x03\x00\x00\x00\x00\x00')
# {"type": "POSE", "pose": "REST"}
# (Handle.CLASSIFIER_EVENT): bytearray(b'\x03\x01\x00\x00\x00\x00')
# {"type": "POSE", "pose": "FIST"}
@pytest.mark.parametrize(
    "blob,out",
    [
        (bytes.fromhex('01010202d708'), (1, 3)),
        (bytes.fromhex('030000000000'), (3, 0)),
        (bytes.fromhex('030100000000'), (3, 1)),
        (bytes.fromhex('030500000000'), (3, 5)),
        (bytes.fromhex('020000000000'), (2,)),
    ],
)
def test_classifier_event(blob, out):
    ce = ClassifierEvent(blob)
    assert repr(ce) == repr(out)


@pytest.mark.parametrize(
    "blob,out",
    [
        (
            bytes.fromhex('090d01fefefefa0206e9fcfdfcfe0502'),
            (9, 13, 1, -2, -2, -2, -6, 2, 6, -23, -4, -3, -4, -2, 5, 2),
        ),
        (
            bytes.fromhex('fe0200ff0000ff0304110000fefe0304'),
            (-2, 2, 0, -1, 0, 0, -1, 3, 4, 17, 0, 0, -2, -2, 3, 4),
        ),
        (
            bytes.fromhex('05fe00000204151ef2f3fffe02fc01ed'),
            (5, -2, 0, 0, 2, 4, 21, 30, -14, -13, -1, -2, 2, -4, 1, -19),
        ),
        (
            bytes.fromhex('021100fe00fdfd0504ff020100040801'),
            (2, 17, 0, -2, 0, -3, -3, 5, 4, -1, 2, 1, 0, 4, 8, 1),
        ),
        (
            bytes.fromhex('fffbfd00ff000001ff00fffffefcfe08'),
            (-1, -5, -3, 0, -1, 0, 0, 1, -1, 0, -1, -1, -2, -4, -2, 8),
        ),
    ],
)
def test_emg_data(blob, out):
    emg = EMGData(blob)
    assert repr(emg.sample1 + emg.sample2) == str(out)
    assert emg.json() == str({"sample1": list(out)[:8], "sample2": list(out)[8:]}).replace("'", '"')


@pytest.mark.parametrize(
    "blob,out",
    [
        (
            bytes.fromhex('5203ce0061007901d80062006f00730100'),
            (850, 206, 97, 377, 216, 98, 111, 371, 0),
        ),
        (
            bytes.fromhex('9b017a03d201cc000c01c4007201fc0100'),
            (411, 890, 466, 204, 268, 196, 370, 508, 0),
        ),
        (
            bytes.fromhex('db004b01ff008c011004e603f8026b0100'),
            (219, 331, 255, 396, 1040, 998, 760, 363, 0),
        ),
        (
            bytes.fromhex('0000000000000000000000000000000000'),
            (0, 0, 0, 0, 0, 0, 0, 0, 0),
        ),
        (
            bytes.fromhex('ffffffffffffffffffffffffffffffff00'),
            (65535, 65535, 65535, 65535, 65535, 65535, 65535, 65535, 0),
        ),
    ],
)
def test_fv_data(blob, out):
    fvd = FVData(blob)
    assert repr(fvd) == str(out)


@pytest.mark.parametrize(
    "blob,out",
    [
        (
            bytes.fromhex('3e2eab2be5f824004e01bd0757000300f5fffcff'),
            (
                0.7225341796875,
                0.68231201171875,
                -0.11102294921875,
                0.002197265625,
                [0.1630859375, 0.96728515625, 0.04248046875],
                [0.1875, -0.6875, -0.25],
            ),
        ),
        (
            bytes.fromhex('0a2ee12be5f810005b01c6075300f1ff0400f7ff'),
            (
                0.7193603515625,
                0.68560791015625,
                -0.11102294921875,
                0.0009765625,
                [0.16943359375, 0.9716796875, 0.04052734375],
                [-0.9375, 0.25, -0.5625],
            ),
        ),
        (
            bytes.fromhex('5c2d9e2c23f99cff03fc1a06eaf94900feffe3ff'),
            (
                0.708740234375,
                0.6971435546875,
                -0.10723876953125,
                -0.006103515625,
                [-0.49853515625, 0.7626953125, -0.7607421875],
                [4.5625, -0.125, -1.8125],
            ),
        ),
    ],
)
def test_imu_data(blob, out):
    imud = IMUData(blob)
    assert repr(imud) == str(out)


# (Handle.MOTION_EVENT): bytearray(b'\x00\x01\x01')
# {"type": "TAP", "tap-direction": 1, "tap-count": 1}
@pytest.mark.parametrize(
    "blob,out",
    [
        (bytes.fromhex('000201'), (0, 2, 1)),
        (bytes.fromhex('000306'), (0, 3, 6)),
        (bytes.fromhex('000402'), (0, 4, 2)),
        (bytes.fromhex('000501'), (0, 5, 1)),
        (bytes.fromhex('000601'), (0, 6, 1)),
    ],
)
def test_motion_event(blob, out):
    me = MotionEvent(blob)
    assert repr(me) == str(out)


@pytest.mark.parametrize(
    "blob,fi_dict",
    [
        (
            bytearray(b'\x8e2\x94\x85;\xd2\x05\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00'),
            {
                'serial_number': 'D2:3B:85:94:32:8E',
                'unlock_pose': 'DOUBLE_TAP',  # Fixed: was True (buggy behavior)
                'active_classifier_type': 'BUILTIN',
                'active_classifier_index': 0,
                'has_custom_classifier': True,
                'stream_indicating': False,
                'sku': 'UNKNOWN',
            },
        ),  # noqa
    ],
)
def test_firmware_info(blob, fi_dict):
    fi = FirmwareInfo(blob)
    assert fi.to_dict() == fi_dict


@pytest.mark.parametrize(
    "blob,fv_str",
    [
        (bytearray(b'\x01\x00\x05\x00\xb2\x07\x02\x00'), '1.5.1970.REVD'),
    ],
)
def test_firmware_version(blob, fv_str):
    fv = FirmwareVersion(blob)
    assert str(fv) == fv_str
