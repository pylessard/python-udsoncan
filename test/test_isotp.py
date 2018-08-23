import unittest

from test.UdsTest import UdsTest
from udsoncan.connections import PythonCanConnection

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
