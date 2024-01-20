import unittest
from test.UdsTest import UdsTest
from test.stub import StubbedIsoTPSocket
from udsoncan.exceptions import *
import socket

try:
    import isotp
    _isotp_available = True
except ImportError:
    _isotp_available = False


@unittest.skipIf(_isotp_available == False, "isotp module not available")
class TestStubbedIsoTPSocket(UdsTest):
    def test_open(self):
        tpsock = StubbedIsoTPSocket()
        self.assertFalse(tpsock.bound)
        addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x100, txid=0x101)
        tpsock.bind(interface='vcan0', address=addr)
        self.assertTrue(tpsock.bound)
        tpsock.close()
        self.assertFalse(tpsock.bound)

    def test_transmit(self):
        tpsock1 = StubbedIsoTPSocket()
        tpsock2 = StubbedIsoTPSocket(timeout=0.5)
        addr1 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x200, txid=0x201)
        addr2 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x201, txid=0x200)
        tpsock1.bind(interface='vcan0', address=addr1)
        tpsock2.bind(interface='vcan0', address=addr2)

        payload1 = b"\x01\x02\x03\x04"
        tpsock1.send(payload1)
        payload2 = tpsock2.recv()
        self.assertEqual(payload1, payload2)

    def test_multicast(self):
        tpsock1 = StubbedIsoTPSocket()
        tpsock2 = StubbedIsoTPSocket(timeout=0.5)
        tpsock3 = StubbedIsoTPSocket(timeout=0.5)
        addr1 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x300, txid=0x301)
        addr2 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x301, txid=0x300)
        addr3 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x301, txid=0x300)

        tpsock1.bind(interface='vcan0', address=addr1)
        tpsock2.bind(interface='vcan0', address=addr2)
        tpsock3.bind(interface='vcan0', address=addr3)

        payload1 = b"\x01\x02\x03\x04"
        tpsock1.send(payload1)
        payload2 = tpsock2.recv()
        payload3 = tpsock3.recv()
        self.assertEqual(payload1, payload2)
        self.assertEqual(payload1, payload3)

    def test_empty_on_close(self):
        tpsock1 = StubbedIsoTPSocket()
        tpsock2 = StubbedIsoTPSocket(timeout=0.2)
        addr1 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x400, txid=0x401)
        addr2 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x401, txid=0x400)
        tpsock1.bind(interface='vcan0', address=addr1)
        tpsock2.bind(interface='vcan0', address=addr2)

        payload = b"\x01\x02\x03\x04"
        tpsock1.send(payload)
        tpsock2.close()

        with self.assertRaises(socket.timeout):
            tpsock2.recv()

    def test_no_listener(self):
        tpsock1 = StubbedIsoTPSocket()
        tpsock2 = StubbedIsoTPSocket(timeout=0.2)
        addr1 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x400, txid=0x401)
        addr2 = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=0x401, txid=0x400)
        tpsock1.bind(interface='vcan0', address=addr1)

        payload = b"\x01\x02\x03\x04"
        tpsock1.send(payload)
        tpsock2.bind(interface='vcan0', address=addr2)

        with self.assertRaises(socket.timeout):
            tpsock2.recv()
