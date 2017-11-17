from test.UdsTest import UdsTest
from udsoncan.Connection import IsoTPConnection
from test.stub import StubbedIsoTPSocket

class TestIsoTPConnection(UdsTest):

	def setUp(self):
		self.tpsock1 = StubbedIsoTPSocket(timeout=0.1)
		self.tpsock2 = StubbedIsoTPSocket(timeout=0.1)

	def test_open(self):
		conn = IsoTPConnection(interface='vcan0', rxid=0x001, txid=0x002, tpsock=self.tpsock1)
		self.assertFalse(conn.is_open())
		conn.open()
		self.assertTrue(conn.is_open())
		conn.close()
		self.assertFalse(conn.is_open())

	def test_transmit(self):
		conn1 = IsoTPConnection(interface='vcan0', rxid=0x100, txid=0x101, tpsock=self.tpsock1)
		conn2 = IsoTPConnection(interface='vcan0', rxid=0x101, txid=0x100, tpsock=self.tpsock2)
		
		with conn1.open():
			with conn2.open():
				payload1 = b"\x00\x01\x02\x03\x04"
				conn1.send(payload1)
				payload2 = conn2.wait_frame(timeout=0.3)
				self.assertEqual(payload1, payload2)