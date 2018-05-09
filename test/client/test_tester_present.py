from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestTesterPresent(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
	
	def test_tester_present_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x3E\x00")
		self.conn.fromuserqueue.put(b"\x7E\x00")	# Positive response

	def _test_tester_present_success(self):
		response = self.udsclient.tester_present()
		self.assertTrue(response.positive)

	def test_tester_present_success_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x3E\x80")
		self.conn.fromuserqueue.put('wait')	# Syncronize

	def _test_tester_present_success_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.tester_present()
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_tester_present_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x3E\x13") # IMLOIF

	def _test_tester_present_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.tester_present()
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.TesterPresent))
		self.assertEqual(response.code, 0x13)

	def test_tester_present_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x3E\x13") # IMLOIF

	def _test_tester_present_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.tester_present()

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.TesterPresent))
		self.assertEqual(response.code, 0x13)

	def test_tester_present_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x00") #Inexistent Service

	def _test_tester_present_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.tester_present()

	def test_tester_present_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x00") #Inexistent Service

	def _test_tester_present_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.tester_present()
		self.assertFalse(response.valid)

	def test_tester_present_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x50\x00") # Valid but wrong service (Tester Present)

	def _test_tester_present_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.tester_present()

	def test_tester_present_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x50\x00") # Valid but wrong service (Tester Present)

	def _test_tester_present_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.tester_present()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)