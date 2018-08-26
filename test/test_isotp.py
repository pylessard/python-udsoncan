import unittest
import logging

from test.UdsTest import UdsTest
from udsoncan.connections import PythonCanConnection
from udsoncan.isotp import ISOTPMixin, ISOTPError
from udsoncan.exceptions import TimeoutException

try:
    import can
except ImportError:
    can = None

class TestPythonCanConnection(UdsTest):

    @unittest.skipIf(can is None, 'python-can must be installed')
    def test_open(self):
        conn = PythonCanConnection(channel=0, interface='virtual', rxid=0x001, txid=0x002, name='unittest')
        self.assertFalse(conn.is_open())
        conn.open()
        self.assertTrue(conn.is_open())
        conn.close()
        self.assertFalse(conn.is_open())

    @unittest.skipIf(can is None, 'python-can must be installed')
    def test_transmit(self):
        conn1 = PythonCanConnection(channel=0, interface='virtual', rxid=0x100, txid=0x101, name='unittest')
        conn2 = PythonCanConnection(channel=0, interface='virtual', rxid=0x101, txid=0x100, name='unittest')

        with conn1.open():
            with conn2.open():
                payload1 = b"\x00\x01\x02\x03\x04"
                conn1.send(payload1)
                payload2 = conn2.wait_frame(timeout=0.3, exception=True)
                self.assertEqual(payload1, payload2)


class IsoTpProtocolTest(UdsTest, ISOTPMixin):
    """Test of the ISOTPMixin class.

    Mocks the send_raw and recv_raw methods in order to check the transmitted
    messages against expected CAN data and feed it with simulated received messages.
    """

    logger = logging.getLogger('isotp_test')

    def setUp(self):
        ISOTPMixin.__init__(self, block_size=3, st_min=0)

    def send_raw(self, data):
        dir, expected = self.can_data.pop(0)
        self.assertEqual(dir, 'TX', 'Did not expect a CAN frame')
        self.assertSequenceEqual(data, expected, 'CAN frame does not contain the expected data')

    def recv_raw(self, timeout):
        dir, data = self.can_data.pop(0)
        self.assertEqual(dir, 'RX', 'Did not expect a message to be received')
        if dir != 'RX':
            raise TimeoutException('No message was expected')
        return data

    def test_send_single_frame(self):
        self.can_data = [
            ('TX', b'\x06\x00\x01\x02\x03\x04\x05\x00')
        ]

        self.send_isotp(b'\x00\x01\x02\x03\x04\x05')

    def test_recv_single_frame(self):
        self.can_data = [
            ('RX', b'\x06\x00\x01\x02\x03\x04\x05\x00')
        ]

        data = self.recv_isotp()
        self.assertSequenceEqual(data, b'\x00\x01\x02\x03\x04\x05')

    def test_send_multi_frame(self):
        self.can_data = [
            # First frame
            ('TX', b'\x10\x27\x00\x01\x02\x03\x04\x05'),
            # Flow control with padding, bs=4
            ('RX', b'\x30\x04\x00\xCC\xCC\xCC\xCC\xCC'),
            # 4 consecutive frames
            ('TX', b'\x21\x06\x07\x08\x09\x0A\x0B\x0C'),
            ('TX', b'\x22\x0D\x0E\x0F\x10\x11\x12\x13'),
            ('TX', b'\x23\x14\x15\x16\x17\x18\x19\x1A'),
            ('TX', b'\x24\x1B\x1C\x1D\x1E\x1F\x20\x21'),
            # Flow control without padding
            ('RX', b'\x30\x04\x00'),
            # 1 last consecutive frame
            ('TX', b'\x25\x22\x23\x24\x25\x26')
        ]

        self.send_isotp(range(0x27))

    def test_recv_multi_frame(self):
        self.can_data = [
            # First frame
            ('RX', b'\x10\x27\x00\x01\x02\x03\x04\x05'),
            # Flow control frame, bs=3
            ('TX', b'\x30\x03\x00'),
            # 3 consecutive frames
            ('RX', b'\x21\x06\x07\x08\x09\x0A\x0B\x0C'),
            ('RX', b'\x22\x0D\x0E\x0F\x10\x11\x12\x13'),
            ('RX', b'\x23\x14\x15\x16\x17\x18\x19\x1A'),
            # Flow control frame
            ('TX', b'\x30\x03\x00'),
            # 2 more consecutive frames
            ('RX', b'\x24\x1B\x1C\x1D\x1E\x1F\x20\x21'),
            ('RX', b'\x25\x22\x23\x24\x25\x26\xCC\xCC')
        ]

        data = self.recv_isotp()
        self.assertSequenceEqual(data, range(0x27))
