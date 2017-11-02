from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestRequestTransferExit(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_request_transfer_exit_success(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.assertEqual(request, b"\x37\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x77\x89\xab\xcd\xef")	# Positive response

	def _test_request_transfer_exit_success(self):
		response_data = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')
		self.assertEqual(response_data, b'\x89\xab\xcd\xef')

#========================================
	def test_request_transfer_exit_no_data_ok(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.assertEqual(request, b"\x37")
		self.conn.fromuserqueue.put(b"\x77")	# Positive response

	def _test_request_transfer_exit_no_data_ok(self):
		response_data = self.udsclient.request_transfer_exit()
		self.assertEqual(response_data, None)	

#========================================
	def test_request_transfer_exit_denied(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.conn.fromuserqueue.put(b"\x7F\x77\x24") # reset sequence error

	def _test_request_transfer_exit_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.request_transfer_exit()
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.RequestTransferExit))
		self.assertEqual(response.code, 0x24)

#========================================
	def test_request_transfer_exit_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.conn.fromuserqueue.put(b"\x00\x55") #Inexistent Service

	def _test_request_transfer_exit_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')

#========================================
	def test_request_transfer_exit_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_request_transfer_exit_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.request_transfer_exit(data=b'\x12\x34\x56')

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.request_transfer_exit(data=123)

		with self.assertRaises(ValueError):
			response = self.udsclient.request_transfer_exit(data="asd")