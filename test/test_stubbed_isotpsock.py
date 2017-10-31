from test.UdsTest import UdsTest
from test.stub import StubbedIsoTPSocket
from udsoncan.exceptions import *
import socket

class TestStubbedIsoTPSocket(UdsTest):
	def test_open(self):
		tpsock = StubbedIsoTPSocket()
		self.assertFalse(tpsock.bound)
		tpsock.bind(interface='vcan0', rxid=0x100, txid=0x101)
		self.assertTrue(tpsock.bound)
		tpsock.close()
		self.assertFalse(tpsock.bound)

	def test_transmit(self):
		tpsock1 = StubbedIsoTPSocket()
		tpsock2 = StubbedIsoTPSocket(timeout=0.5)
		tpsock1.bind(interface='vcan0', rxid=0x200, txid=0x201)
		tpsock2.bind(interface='vcan0', rxid=0x201, txid=0x200)
		
		payload1 = b"\x01\x02\x03\x04"
		tpsock1.send(payload1)
		payload2 = tpsock2.recv()
		self.assertEqual(payload1, payload2)

	def test_multicast(self):
		tpsock1 = StubbedIsoTPSocket()
		tpsock2 = StubbedIsoTPSocket(timeout=0.5)
		tpsock3 = StubbedIsoTPSocket(timeout=0.5)
		tpsock1.bind(interface='vcan0', rxid=0x300, txid=0x301)
		tpsock2.bind(interface='vcan0', rxid=0x301, txid=0x300)
		tpsock3.bind(interface='vcan0', rxid=0x301, txid=0x300)
		
		payload1 = b"\x01\x02\x03\x04"
		tpsock1.send(payload1)
		payload2 = tpsock2.recv()
		payload3 = tpsock3.recv()
		self.assertEqual(payload1, payload2)
		self.assertEqual(payload1, payload3)

	def test_empty_on_close(self):
		tpsock1 = StubbedIsoTPSocket()
		tpsock2 = StubbedIsoTPSocket(timeout=0.2)
		tpsock1.bind(interface='vcan0', rxid=0x400, txid=0x401)
		tpsock2.bind(interface='vcan0', rxid=0x401, txid=0x400)
		
		payload = b"\x01\x02\x03\x04"
		tpsock1.send(payload)
		tpsock2.close()

		with self.assertRaises(socket.timeout):
			tpsock2.recv()

	def test_no_listener(self):
		tpsock1 = StubbedIsoTPSocket()
		tpsock2 = StubbedIsoTPSocket(timeout=0.2)
		tpsock1.bind(interface='vcan0', rxid=0x400, txid=0x401)
		
		payload = b"\x01\x02\x03\x04"
		tpsock1.send(payload)
		tpsock2.bind(interface='vcan0', rxid=0x401, txid=0x400)
		
		with self.assertRaises(socket.timeout):
			tpsock2.recv()
		