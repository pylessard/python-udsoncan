from test.stub import StubbedConnection
from test.ThreadableTest import ThreadableTest
from udsoncan.client import Client

class ClientServerTest(ThreadableTest):
	def __init__(self, *args, **kwargs):
		ThreadableTest.__init__(self, *args, **kwargs)

	def setUp(self):
		self.conn = StubbedConnection(name='unittest')

	def clientSetUp(self):
		self.udsclient = Client(self.conn, request_timeout=0.2)
		self.udsclient.config['logger_name'] = 'unittest'
		self.udsclient.refresh_config()
		
		self.udsclient.open()
		if hasattr(self, "postClientSetUp"):
			self.postClientSetUp()

	def clientTearDown(self):
		self.udsclient.close()

	def wait_request_and_respond(self, bytes):
		self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(bytes) 