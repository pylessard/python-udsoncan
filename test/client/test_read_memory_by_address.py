from test.ClientServerTest import ClientServerTest
from udsoncan import MemoryLocation
from udsoncan.exceptions import *

# Note : 
# MemoryLocation object is unit tested in a separate file (test_helper_class). 
# As it is the only parameter to be passed, no need to push this test too far for nothing.

class TestReadMemoryByAddress(ClientServerTest):

	def test_positive_response(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x23\x12\x12\x34\x04")
		self.conn.fromuserqueue.put(b"\x63\x99\x88\x77\x66")

	def _test_positive_response(self):
		data = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
		self.assertEqual(data, b'\x99\x88\x77\x66')

	def test_request_denied(self):
		self.wait_request_and_respond(b"\x7F\x23\x45") #Request Out Of Range

	def _test_request_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_request_invalid_service(self):
		self.wait_request_and_respond(b"\x00\x45") #Inexistent Service

	def _test_request_invalid_service(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_wrong_service(self):
		self.wait_request_and_respond(b"\x7E\x99\x88\x77\x66") # Valid but wrong service (Tester Present)

	def _test_wrong_service(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.read_memory_by_address(1)

		with self.assertRaises(ValueError):
			self.udsclient.read_memory_by_address('aaa')