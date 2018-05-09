from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestDiagnosticSessionControl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_dsc_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x10\x01")
		self.conn.fromuserqueue.put(b"\x50\x01\x99\x88")	# Positive response

	def _test_dsc_success(self):
		response = self.udsclient.change_session(services.DiagnosticSessionControl.Session.defaultSession)
		self.assertEqual(response.service_data.session_echo, 1)
		self.assertEqual(response.service_data.session_param_records, b"\x99\x88")

	def test_dsc_success_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x10\x81")
		self.conn.fromuserqueue.put("wait")	#Synchronize

	def _test_dsc_success_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.change_session(services.DiagnosticSessionControl.Session.defaultSession)
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_dsc_denied_exception(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x10\x08")
		self.conn.fromuserqueue.put(b"\x7F\x10\x12") # Subfunction not supported

	def _test_dsc_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.change_session(0x08)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.DiagnosticSessionControl))
		self.assertEqual(response.code, 0x12)

	def test_dsc_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x10\x12") # Subfunction not supported

	def _test_dsc_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.change_session(0x08)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_dsc_bad_subfunction_exception(self):
		self.wait_request_and_respond(b"\x50\x02")	# Positive response

	def _test_dsc_bad_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.change_session(services.DiagnosticSessionControl.Session.defaultSession)

	def test_dsc_bad_subfunction_no_exception(self):
		self.wait_request_and_respond(b"\x50\x02")	# Positive response

	def _test_dsc_bad_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.change_session(services.DiagnosticSessionControl.Session.defaultSession)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_dsc_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x02") #Inexistent Service

	def _test_dsc_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.change_session(0x02)

	def test_dsc_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x02") #Inexistent Service

	def _test_dsc_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.change_session(0x02)
		self.assertFalse(response.valid)

	def test_ecu_reset_wrongservice_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.change_session(0x55)

	def test_ecu_reset_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.change_session(0x55)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			success = self.udsclient.change_session(0x100)

		with self.assertRaises(ValueError):
			success = self.udsclient.change_session(-1)
