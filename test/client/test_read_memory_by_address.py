from test.ClientServerTest import ClientServerTest
from udsoncan import MemoryLocation
from udsoncan.exceptions import *

# Note : 
# MemoryLocation object is unit tested in a separate file (test_helper_class). 
# As it is the only parameter to be passed, no need to push this test too far for nothing.

class TestReadMemoryByAddress(ClientServerTest):

	def test_4byte_block(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x23\x12\x12\x34\x04")
		self.conn.fromuserqueue.put(b"\x63\x99\x88\x77\x66")

	def _test_4byte_block(self):
		response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
		self.assertEqual(response.service_data.memory_block, b'\x99\x88\x77\x66')

	def test_4byte_block_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x23\x12\x12\x34\x04")
		self.conn.fromuserqueue.put(b"\x63\x99\x88\x77\x66")

	def _test_4byte_block_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
			self.assertEqual(response.service_data.memory_block, b'\x99\x88\x77\x66')		

	def test_config_format(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x23\x24\x00\x00\x12\x34\x00\x04")
		self.conn.fromuserqueue.put(b"\x63\x99\x88\x77\x66")

	def _test_config_format(self):
		self.udsclient.config['server_address_format'] = 32
		self.udsclient.config['server_memorysize_format'] = 16
		self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4))

	def test_4byte_block_zeropadding_ok(self):
		data = b"\x63\x99\x88\x77\x66"
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00'*(i+1))

	def _test_4byte_block_zeropadding_ok(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(8):
			response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
			self.assertEqual(response.service_data.memory_block, b'\x99\x88\x77\x66')

	def test_4byte_block_zeropadding_not_ok_exception(self):
		data = b"\x63\x99\x88\x77\x66"
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00'*(i+1))

	def _test_4byte_block_zeropadding_not_ok_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			with self.assertRaises(UnexpectedResponseException):
				self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_4byte_block_zeropadding_not_ok_no_exception(self):
		data = b"\x63\x99\x88\x77\x66"
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00'*(i+1))

	def _test_4byte_block_zeropadding_not_ok_no_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['exception_on_unexpected_response'] = False
		for i in range(8):
			response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
			self.assertTrue(response.valid)
			self.assertTrue(response.unexpected)

	def test_request_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x23\x45") #Request Out Of Range

	def _test_request_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_request_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x23\x45") #Request Out Of Range

	def _test_request_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_request_invalid_service_exception(self):
		self.wait_request_and_respond(b"\x00\x45") #Inexistent Service

	def _test_request_invalid_service_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_request_invalid_service_no_exception(self):
		self.wait_request_and_respond(b"\x00\x45") #Inexistent Service

	def _test_request_invalid_service_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
		self.assertFalse(response.valid)

	def test_wrong_service_exception(self):
		self.wait_request_and_respond(b"\x7E\x99\x88\x77\x66") # Valid but wrong service (Tester Present)

	def _test_wrong_service_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))

	def test_wrong_service_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x99\x88\x77\x66") # Valid but wrong service (Tester Present)

	def _test_wrong_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.read_memory_by_address(MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8))
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.read_memory_by_address(1)

		with self.assertRaises(ValueError):
			self.udsclient.read_memory_by_address('aaa')