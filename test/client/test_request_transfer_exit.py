from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestRequestTransferExit(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_request_transfer_exit_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x37\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x77\x89\xab\xcd\xef")	# Positive response

	def _test_request_transfer_exit_success(self):
		response = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')
		self.assertEqual(response.service, services.RequestTransferExit)
		self.assertEqual(response.service_data.parameter_records, b'\x89\xab\xcd\xef')

	def test_request_transfer_exit_success_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x37\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x77\x89\xab\xcd\xef")	# Positive response

	def _test_request_transfer_exit_success_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')
			self.assertEqual(response.service, services.RequestTransferExit)
			self.assertEqual(response.service_data.parameter_records, b'\x89\xab\xcd\xef')

	def test_request_transfer_exit_no_data_ok(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x37")
		self.conn.fromuserqueue.put(b"\x77")	# Positive response

	def _test_request_transfer_exit_no_data_ok(self):
		response = self.udsclient.request_transfer_exit()
		self.assertEqual(response.service_data.parameter_records, b'')	

	def test_request_transfer_exit_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x37\x24") # reset sequence error

	def _test_request_transfer_exit_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.request_transfer_exit()
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.RequestTransferExit))
		self.assertEqual(response.code, 0x24)

	def test_request_transfer_exit_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x37\x24") # reset sequence error

	def _test_request_transfer_exit_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False	
		response = self.udsclient.request_transfer_exit()
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_request_transfer_exit_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x55") #Inexistent Service

	def _test_request_transfer_exit_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')

	def test_request_transfer_exit_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x55") #Inexistent Service

	def _test_request_transfer_exit_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False	
		response = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')
		self.assertFalse(response.valid)

	def test_request_transfer_exit_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_request_transfer_exit_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')

	def test_request_transfer_exit_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_request_transfer_exit_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False	
		response = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.request_transfer_exit(data=123)

		with self.assertRaises(ValueError):
			self.udsclient.request_transfer_exit(data="asd")