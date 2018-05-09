from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *
from udsoncan import DidCodec
import struct

from test.ClientServerTest import ClientServerTest


class StubbedDidCodec(DidCodec):
	def encode(self, did_value):
		return struct.pack('B', did_value+1)

	def decode(self, did_payload):
		return struct.unpack('B', did_payload)[0] - 1

	def __len__(self):
		return 1

class TestReadDataByIdentifier(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def postClientSetUp(self):
		self.udsclient.config["data_identifiers"] = {
			1 : '>H',
			2 : '<H',
			3 : StubbedDidCodec
		}

	def test_wdbi_single_success1(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2E\x00\x01\x12\x34")
		self.conn.fromuserqueue.put(b"\x6E\x00\x01")	# Positive response

	def _test_wdbi_single_success1(self):
		response = self.udsclient.write_data_by_identifier(did = 1, value=0x1234)
		self.assertTrue(response.positive)

	def test_wdbi_single_success1_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2E\x00\x01\x12\x34")
		self.conn.fromuserqueue.put(b"\x6E\x00\x01")	# Positive response

	def _test_wdbi_single_success1_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.write_data_by_identifier(did = 1, value=0x1234)
			self.assertTrue(response.positive)

	def test_wdbi_single_success2(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2E\x00\x02\x34\x12")
		self.conn.fromuserqueue.put(b"\x6E\x00\x02")	# Positive response

	def _test_wdbi_single_success2(self):
		self.udsclient.write_data_by_identifier(did = 2, value=0x1234)

	def test_wdbi_incomplete_response_exception(self):
		self.wait_request_and_respond(b"\x6E\x00")	#Incomplete response

	def _test_wdbi_incomplete_response_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.write_data_by_identifier(did = 1, value=0x1234)

	def test_wdbi_incomplete_response_no_exception(self):
		self.wait_request_and_respond(b"\x6E\x00")	#Incomplete response

	def _test_wdbi_incomplete_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.write_data_by_identifier(did = 1, value=0x1234)
		self.assertFalse(response.valid)

	def test_wdbi_unknown_did_exception(self):
		self.wait_request_and_respond(b"\x6E\x00\x09")	# Positive response

	def _test_wdbi_unknown_did_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.write_data_by_identifier(did = 1, value=0x1234)			
	
	def test_wdbi_unknown_did_no_exception(self):
		self.wait_request_and_respond(b"\x6E\x00\x09")	# Positive response

	def _test_wdbi_unknown_did_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.write_data_by_identifier(did = 1, value=0x1234)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)			
	
	def test_wdbi_unwanted_did_exception(self):
		self.wait_request_and_respond(b"\x6E\x00\x02")	# Positive response

	def _test_wdbi_unwanted_did_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.write_data_by_identifier(did = 1, value=0x1234)			
	
	def test_wdbi_unwanted_did_no_exception(self):
		self.wait_request_and_respond(b"\x6E\x00\x02")	# Positive response

	def _test_wdbi_unwanted_did_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.write_data_by_identifier(did = 1, value=0x1234)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_wdbi_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x00\x01")	# Service is inexistant

	def _test_wdbi_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.write_data_by_identifier(did=1, value=0x1234)

	def test_wdbi_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x00\x01")	# Service is inexistant

	def _test_wdbi_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.write_data_by_identifier(did=1, value=0x1234)
		self.assertFalse(response.valid)

	def test_wdbi_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x50\x00\x01")	# Valid service, but not the one requested

	def _test_wdbi_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.write_data_by_identifier(did=1, value=0x1234)

	def test_wdbi_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x50\x00\x01")	# Valid service, but not the one requested

	def _test_wdbi_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.write_data_by_identifier(did = 1, value=0x1234)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_no_config(self):
		pass

	def _test_no_config(self):
		with self.assertRaises(ConfigError):
			self.udsclient.write_data_by_identifier(did = 4, value=0x1234) 