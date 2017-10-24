from test.stub import StubbedConnection
from test.ThreadableTest import ThreadableTest
from udsoncan.client import Client

class ClientServerTest(ThreadableTest):
	def __init__(self, *args, **kwargs):
		ThreadableTest.__init__(self, *args, **kwargs)

	def setUp(self):
		self.conn = StubbedConnection()

	def clientSetUp(self):
		self.udsclient = Client(self.conn, request_timeout=1)
		self.udsclient.open()

	def clientTearDown(self):
		self.udsclient.close()