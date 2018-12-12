from udsoncan import services
from udsoncan.exceptions import *
from udsoncan import Request, Response

from test.ClientServerTest import ClientServerTest
import time

class TestClient(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_timeout(self):
		pass

	def _test_timeout(self):
		req = Request(service = services.TesterPresent, subfunction=0) 
		timeout = 0.5
		try:
			t1 = time.time()
			response = self.udsclient.send_request(req, timeout=timeout)
			raise Exception('Request did not raise a TimeoutException')
		except TimeoutException as e:
			diff = time.time() - t1
			self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
			self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

	def test_timeout_pending_response(self):
		pass

	def _test_param_timeout(self):
		req = Request(service = services.TesterPresent, subfunction=0) 
		timeout = 0.5
		self.udsclient.request_timeout = timeout
		try:
			t1 = time.time()
			response = self.udsclient.send_request(req)
			raise Exception('Request did not raise a TimeoutException')
		except TimeoutException as e:
			diff = time.time() - t1
			self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
			self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))

	def test_param_timeout(self):
		self.conn.touserqueue.get(timeout=0.2)
		response = Response(service=services.TesterPresent, code=Response.Code.RequestCorrectlyReceived_ResponsePending)
		t1 = time.time()
		while time.time() - t1 < 1:
			time.sleep(0.1)
			self.conn.fromuserqueue.put(response.get_payload())

	def _test_timeout_pending_response(self):
		req = Request(service = services.TesterPresent, subfunction=0) 
		timeout = 0.5
		try:
			t1 = time.time()
			response = self.udsclient.send_request(req, timeout=timeout)
			raise Exception('Request did not raise a TimeoutException')
		except TimeoutException as e:
			diff = time.time() - t1
			self.assertGreater(diff, timeout, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
			self.assertLess(diff, timeout+0.5, 'Timeout raised after %.3f seconds when it should be %.3f sec' % (diff, timeout))
