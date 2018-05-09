from test.ClientServerTest import ClientServerTest
from udsoncan import MemoryLocation, AddressAndLengthFormatIdentifier
from udsoncan.exceptions import *

# Note : 
# MemoryLocation object is unit tested in a separate file (test_helper_class). 
# As it is the only parameter to be passed, no need to push this test too far for nothing.

class TestWriteMemoryByAddress(ClientServerTest):

	def test_4byte_block(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x3D\x12\x12\x34\x04\x66\x77\x88\x99")
		self.conn.fromuserqueue.put(b"\x7D\x12\x12\x34\x04")

	def _test_4byte_block(self):
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

		self.assertEqual(response.service_data.alfid_echo, memloc.alfid.get_byte_as_int())
		self.assertEqual(response.service_data.memory_location_echo.address, 0x1234)
		self.assertEqual(response.service_data.memory_location_echo.memorysize, 4)

	def test_4byte_block_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x3D\x12\x12\x34\x04\x66\x77\x88\x99")
		self.conn.fromuserqueue.put(b"\x7D\x12\x12\x34\x04")

	def _test_4byte_block_spr_no_effect(self):
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
			self.assertEqual(response.service_data.alfid_echo, memloc.alfid.get_byte_as_int())
			self.assertEqual(response.service_data.memory_location_echo.address, 0x1234)
			self.assertEqual(response.service_data.memory_location_echo.memorysize, 4)

	def test_config_format(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x3D\x24\x00\x00\x12\x34\x00\x04\x66\x77\x88\x99")
		self.conn.fromuserqueue.put(b"\x7D\x24\x00\x00\x12\x34\x00\x04")

	def _test_config_format(self):
		self.udsclient.config['server_address_format'] = 32
		self.udsclient.config['server_memorysize_format'] = 16
		response = self.udsclient.write_memory_by_address(MemoryLocation(address=0x1234, memorysize=4), b'\x66\x77\x88\x99')
		alfid = AddressAndLengthFormatIdentifier(address_format = self.udsclient.config['server_address_format'], memorysize_format=self.udsclient.config['server_memorysize_format'])
		self.assertEqual(response.service_data.alfid_echo, alfid.get_byte_as_int())
		self.assertEqual(response.service_data.memory_location_echo.address, 0x1234)
		self.assertEqual(response.service_data.memory_location_echo.memorysize, 4)

	def test_4byte_block_harmless_extra_bytes(self):
		self.wait_request_and_respond(b'\x7D\x12\x12\x34\x04\x01\x02\x03\x04\x05')


	def _test_4byte_block_harmless_extra_bytes(self):
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

	def test_bad_echo_ali_exception(self):
		self.wait_request_and_respond(b'\x7D\x21\x12\x34\x04')

	def _test_bad_echo_ali_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
			self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

	def test_bad_echo_ali_no_exception(self):
		self.wait_request_and_respond(b'\x7D\x21\x12\x34\x04')

	def _test_bad_echo_ali_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
		self.assertTrue(response.valid)	
		self.assertTrue(response.unexpected)

	def test_bad_echo_address_exception(self):
		self.wait_request_and_respond(b'\x7D\x12\x12\x35\x04')

	def _test_bad_echo_address_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
			self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
	
	def test_bad_echo_address_no_exception(self):
		self.wait_request_and_respond(b'\x7D\x12\x12\x35\x04')

	def _test_bad_echo_address_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False		
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
		self.assertTrue(response.valid)		
		self.assertTrue(response.unexpected)

	def test_bad_echo_memorysize_exception(self):
		self.wait_request_and_respond(b'\x7D\x12\x12\x34\x05')

	def _test_bad_echo_memorysize_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
			self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

	def test_bad_echo_memorysize_no_exception(self):
		self.wait_request_and_respond(b'\x7D\x12\x12\x34\x05')

	def _test_bad_echo_memorysize_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False			
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_request_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x3D\x45") #Request Out Of Range

	def _test_request_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
			self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

	def test_request_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x3D\x45") #Request Out Of Range

	def _test_request_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_request_invalid_service_exception(self):
		self.wait_request_and_respond(b"\x00\x12\x12\x34\x04") #Inexistent Service

	def _test_request_invalid_service_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
			self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

	def test_request_invalid_service_no_exception(self):
		self.wait_request_and_respond(b"\x00\x12\x12\x34\x04") #Inexistent Service

	def _test_request_invalid_service_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
		self.assertFalse(response.valid)

	def test_wrong_service_exception(self):
		self.wait_request_and_respond(b"\x7E\x12\x12\x34\x04") # Valid but wrong service (Tester Present)

	def _test_wrong_service_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
			self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')

	def test_wrong_service_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x12\x12\x34\x04") # Valid but wrong service (Tester Present)

	def _test_wrong_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False	
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)
		response = self.udsclient.write_memory_by_address(memloc, b'\x66\x77\x88\x99')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)		

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		memloc = MemoryLocation(address=0x1234, memorysize=4, address_format=16, memorysize_format=8)

		with self.assertRaises(ValueError):
			self.udsclient.write_memory_by_address(1, b'\x00\x01')

		with self.assertRaises(ValueError):
			self.udsclient.write_memory_by_address('aaa',  b'\x00\x01')

		with self.assertRaises(ValueError):
			self.udsclient.write_memory_by_address(memloc,  1)

		with self.assertRaises(ValueError):
			self.udsclient.write_memory_by_address(memloc,  'aaa')