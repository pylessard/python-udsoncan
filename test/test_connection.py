from test.UdsTest import UdsTest
from udsoncan import Connection
from test.stub import StubbedIsoTPSocket

class TestConnection(UdsTest):
	def test_transmit(self):
		tpsock1 = StubbedIsoTPSocket(timeout=0.5)
		tpsock2 = StubbedIsoTPSocket(timeout=0.5)

		conn1 = Connection(interface='vcan0', rxid=0x100, txid=0x101, tpsock=tpsock1)
		conn2 = Connection(interface='vcan0', rxid=0x101, txid=0x100, tpsock=tpsock2)
		
		with conn1.open():
			with conn2.open():
				payload1 = b"\x00\x01\x02\x03\x04"
				conn1.send(payload1)
				payload2 = conn2.wait_frame(timeout=0.3)
				self.assertEqual(payload1, payload2)