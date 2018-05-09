from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestTransferData(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_transfer_data_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x36\x22\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x76\x22\x89\xab\xcd\xef")	# Positive response

	def _test_transfer_data_success(self):
		response = self.udsclient.transfer_data(sequence_number=0x22, data=b'\x12\x34\x56')
		self.assertEqual(response.service_data.sequence_number_echo, 0x22)
		self.assertEqual(response.service_data.parameter_records, b'\x89\xab\xcd\xef')

	def test_transfer_data_success_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x36\x22\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x76\x22\x89\xab\xcd\xef")	# Positive response

	def _test_transfer_data_success_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.transfer_data(sequence_number=0x22, data=b'\x12\x34\x56')
			self.assertEqual(response.service_data.sequence_number_echo, 0x22)
			self.assertEqual(response.service_data.parameter_records, b'\x89\xab\xcd\xef')

	def test_transfer_data_no_data_ok(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x36\x22")
		self.conn.fromuserqueue.put(b"\x76\x22")	# Positive response

	def _test_transfer_data_no_data_ok(self):
		response = self.udsclient.transfer_data(sequence_number=0x22)
		self.assertEqual(response.service_data.sequence_number_echo, 0x22)
		self.assertEqual(response.service_data.parameter_records, b'')	

	def test_transfer_data_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x36\x73") # wrong block sequence number

	def _test_transfer_data_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.transfer_data(sequence_number=0x55)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.TransferData))
		self.assertEqual(response.code, 0x73)

	def test_transfer_data_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x36\x73") # wrong block sequence number

	def _test_transfer_data_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.transfer_data(sequence_number=0x55)

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.TransferData))
		self.assertEqual(response.code, 0x73)

	def test_transfer_data_bad_sequence_number_exception(self):
		self.wait_request_and_respond(b"\x76\x23\x89\xab\xcd\xef")	# Positive response

	def _test_transfer_data_bad_sequence_number_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.transfer_data(sequence_number=0x22, data=b'\x12\x34\x56')

	def test_transfer_data_bad_sequence_number_no_exception(self):
		self.wait_request_and_respond(b"\x76\x23\x89\xab\xcd\xef")	# Positive response

	def _test_transfer_data_bad_sequence_number_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.transfer_data(sequence_number=0x22, data=b'\x12\x34\x56')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_transfer_data_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x55") #Inexistent Service

	def _test_transfer_data_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.transfer_data(sequence_number=0x55)

	def test_transfer_data_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x55") #Inexistent Service

	def _test_transfer_data_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.transfer_data(sequence_number=0x55)
		self.assertFalse(response.valid)

	def test_transfer_data_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_transfer_data_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.transfer_data(sequence_number=0x55)

	def test_transfer_data_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_transfer_data_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.transfer_data(sequence_number=0x55)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)
		
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.transfer_data(sequence_number=-1)

		with self.assertRaises(ValueError):
			self.udsclient.transfer_data(sequence_number=0x100)

		with self.assertRaises(ValueError):
			self.udsclient.transfer_data(sequence_number=1, data=123)

		with self.assertRaises(ValueError):
			self.udsclient.transfer_data(sequence_number=1, data='asd')