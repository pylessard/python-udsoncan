from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestTransferData(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_transfer_data_success(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.assertEqual(request, b"\x36\x22\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x76\x22\x89\xab\xcd\xef")	# Positive response

	def _test_transfer_data_success(self):
		response_data = self.udsclient.transfer_data(block_sequence_counter=0x22, data=b'\x12\x34\x56')
		self.assertEqual(response_data, b'\x89\xab\xcd\xef')

#========================================
	def test_transfer_data_no_data_ok(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.assertEqual(request, b"\x36\x22")
		self.conn.fromuserqueue.put(b"\x76\x22")	# Positive response

	def _test_transfer_data_no_data_ok(self):
		response_data = self.udsclient.transfer_data(block_sequence_counter=0x22)
		self.assertEqual(response_data, None)	

#========================================
	def test_transfer_data_denied(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.conn.fromuserqueue.put(b"\x7F\x36\x73") # wrong block sequence number

	def _test_transfer_data_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.transfer_data(block_sequence_counter=0x55)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.TransferData))
		self.assertEqual(response.code, 0x73)

#========================================
	def test_transfer_data_bad_sequence_number(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x76\x23\x89\xab\xcd\xef")	# Positive response

	def _test_transfer_data_bad_sequence_number(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.transfer_data(block_sequence_counter=0x22, data=b'\x12\x34\x56')


#========================================
	def test_transfer_data_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.conn.fromuserqueue.put(b"\x00\x55") #Inexistent Service

	def _test_transfer_data_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.transfer_data(block_sequence_counter=0x55)

#========================================
	def test_transfer_data_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=0.3)
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_transfer_data_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.transfer_data(block_sequence_counter=0x55)

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.transfer_data(block_sequence_counter=-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.transfer_data(block_sequence_counter=0x100)

		with self.assertRaises(ValueError):
			response = self.udsclient.transfer_data(block_sequence_counter=1, data=123)

		with self.assertRaises(ValueError):
			response = self.udsclient.transfer_data(block_sequence_counter=1, data='asd')