from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestClearDtc(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_clear_dtc_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x14\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x54")	# Positive response

	def _test_clear_dtc_success(self):
		response = self.udsclient.clear_dtc(0x123456)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)

	def test_clear_dtc_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x14\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x54")	# Positive response

	def _test_clear_dtc_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.clear_dtc(0x123456)
			self.assertTrue(response.valid)
			self.assertTrue(response.positive)

	def test_clear_dtc_all(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x14\xFF\xFF\xFF")
		self.conn.fromuserqueue.put(b"\x54")	# Positive response

	def _test_clear_dtc_all(self):
		response = self.udsclient.clear_dtc()
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)

	def test_clear_dtc_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x14\x31") #Request Out Of Range

	def _test_clear_dtc_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.clear_dtc(0x123456)

	def test_clear_dtc_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x14\x31") #Request Out Of Range

	def _test_clear_dtc_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response =self.udsclient.clear_dtc(0x123456)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertEqual(response.code, 0x31)

	def test_clear_dtc_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00") #Inexistent Service

	def _test_clear_dtc_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.clear_dtc(0x123456)

	def test_clear_dtc_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00") #Inexistent Service

	def _test_clear_dtc_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.clear_dtc(0x123456)
		self.assertFalse(response.valid)

	def test_clear_dtc_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_clear_dtc_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.clear_dtc(0x123456)

	def test_clear_dtc_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_clear_dtc_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.clear_dtc(0x123456)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.clear_dtc(0x1000000)

		with self.assertRaises(ValueError):
			self.udsclient.clear_dtc(-1)