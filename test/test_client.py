from udsoncan.client import Client
from udsoncan import services

from test.stub import StubbedConnection
from test.ThreadableTest import ThreadableTest
import time

class TestClient(ThreadableTest):
	def __init__(self, *args, **kwargs):
		#unittest.TestCase.__init__(self, *args, **kwargs)
		ThreadableTest.__init__(self, *args, **kwargs)

	def setUp(self):
		self.conn = StubbedConnection()

	def clientSetUp(self):
		self.udsclient = Client(self.conn, request_timeout=2)
		self.udsclient.open()

	def test_ecu_reset(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x51\x55")


	def _test_ecu_reset(self):
		response = self.udsclient.ecu_reset(0x55)
		self.assertTrue(response.positive)
		self.assertTrue(response.valid)
		self.assertEqual(response.data, b"\x55")
