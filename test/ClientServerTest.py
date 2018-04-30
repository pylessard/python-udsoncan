from udsoncan.connections import QueueConnection
from test.ThreadableTest import ThreadableTest
from udsoncan.client import Client

class ClientServerTest(ThreadableTest):
	def __init__(self, *args, **kwargs):
		ThreadableTest.__init__(self, *args, **kwargs)

	def setUp(self):
		self.conn = QueueConnection(name='unittest', mtu=4095)

	def clientSetUp(self):
		self.udsclient = Client(self.conn, request_timeout=0.2)
		self.udsclient.set_config('logger_name', 'unittest')
		self.udsclient.set_config('exception_on_invalid_response', True)
		self.udsclient.set_config('exception_on_unexpected_response', True)
		self.udsclient.set_config('exception_on_negative_response', True)
		
		self.udsclient.open()
		if hasattr(self, "postClientSetUp"):
			self.postClientSetUp()

	def clientTearDown(self):
		self.udsclient.close()

	def wait_request_and_respond(self, bytes):
		self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(bytes) 