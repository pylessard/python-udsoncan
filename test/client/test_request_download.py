from udsoncan.client import Client
from udsoncan import services, MemoryLocation, DataFormatIdentifier
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestRequestDownload(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_request_download_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x34\x00\x12\x12\x34\xFF")
		self.conn.fromuserqueue.put(b"\x74\x20\xab\xcd")	# Positive response

	def _test_request_download_success(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		response = self.udsclient.request_download(memory_location=memloc)
		self.assertEqual(response.service_data.max_length,0xabcd)

	def test_request_download_success_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x34\x00\x12\x12\x34\xFF")
		self.conn.fromuserqueue.put(b"\x74\x20\xab\xcd")	# Positive response

	def _test_request_download_success_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
			response = self.udsclient.request_download(memory_location=memloc)
			self.assertEqual(response.service_data.max_length,0xabcd)

	def test_request_download_config_format(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x34\x00\x24\x00\x00\x12\x34\x00\xFF")	# dfi = 24 and 0 padding
		self.conn.fromuserqueue.put(b"\x74\x20\xab\xcd")	# Positive response

	def _test_request_download_config_format(self):
		self.udsclient.set_configs({'server_address_format':32, 'server_memorysize_format':16})
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF)
		response = self.udsclient.request_download(memory_location=memloc)
		self.assertEqual(response.service_data.max_length,0xabcd)

	def test_request_download_success_lfid(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x34\x00\x12\x12\x34\xFF")
		self.conn.fromuserqueue.put(b"\x74\x23\xab\xcd")	# Positive response

	def _test_request_download_success_lfid(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		response = self.udsclient.request_download(memory_location=memloc)
		self.assertEqual(response.service_data.max_length,0xabcd)

	def test_request_download_success_dfi(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x34\x52\x12\x12\x34\xFF")
		self.conn.fromuserqueue.put(b"\x74\x20\xab\xcd")	# Positive response

	def _test_request_download_success_dfi(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		dfi  =DataFormatIdentifier(compression=5, encryption=2)
		response = self.udsclient.request_download(memory_location=memloc, dfi=dfi)
		self.assertEqual(response.service_data.max_length,0xabcd)

	def test_incomplete_nblock_response_exception(self):
		self.wait_request_and_respond(b"\x74\x40\xab\xcd")	# Missing 2 bytes to complete number of block

	def _test_incomplete_nblock_response_exception(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		with self.assertRaises(InvalidResponseException):
			self.udsclient.request_download(memory_location=memloc)

	def test_incomplete_nblock_response_no_exception(self):
		self.wait_request_and_respond(b"\x74\x40\xab\xcd")	# Missing 2 bytes to complete number of block

	def _test_incomplete_nblock_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		response = self.udsclient.request_download(memory_location=memloc)
		self.assertFalse(response.valid)

	def test_request_download_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x20\x12\x34") #Inexistent Service

	def _test_request_download_invalidservice_exception(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.request_download(memory_location=memloc)

	def test_request_download_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x20\x12\x34") #Inexistent Service

	def _test_request_download_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False		
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		response = self.udsclient.request_download(memory_location=memloc)
		self.assertFalse(response.valid)

	def test_request_download_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x20\x12\x34") # Valid but wrong service (Tester Present)

	def _test_request_download_wrongservice_exception(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.request_download(memory_location=memloc)

	def test_request_download_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x20\x12\x34") # Valid but wrong service (Tester Present)

	def _test_request_download_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False	
		memloc = MemoryLocation(address=0x1234, memorysize=0xFF, address_format=16, memorysize_format=8)
		response = self.udsclient.request_download(memory_location=memloc)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_params(self):
		pass

	def _test_bad_params(self):
		with self.assertRaises(ValueError) as handle:
			self.udsclient.request_download(memory_location=1)
		
		with self.assertRaises(ValueError) as handle:
			self.udsclient.request_download(memory_location="asd")
