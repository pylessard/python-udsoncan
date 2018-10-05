import unittest
import logging

from test.UdsTest import UdsTest
from udsoncan.connections import PythonCanConnection
from udsoncan.exceptions import TimeoutException

try:
    import aioisotp
except ImportError:
    aioisotp = None

class TestPythonCanConnection(UdsTest):

    @unittest.skipIf(aioisotp is None, 'aioisotp must be installed')
    def test_open(self):
        conn = PythonCanConnection(channel=0, interface='virtual', rxid=0x001, txid=0x002, name='unittest')
        self.assertFalse(conn.is_open())
        conn.open()
        self.assertTrue(conn.is_open())
        conn.close()
        self.assertFalse(conn.is_open())

    @unittest.skipIf(aioisotp is None, 'aioisotp must be installed')
    def test_transmit(self):
        conn1 = PythonCanConnection(channel=0, interface='virtual', rxid=0x100, txid=0x101, name='unittest')
        conn2 = PythonCanConnection(channel=0, interface='virtual', rxid=0x101, txid=0x100, name='unittest')

        with conn1.open():
            with conn2.open():
                payload1 = bytes(range(0x20))
                conn1.send(payload1)
                payload2 = conn2.wait_frame(timeout=1, exception=True)
                self.assertEqual(payload1, payload2)
