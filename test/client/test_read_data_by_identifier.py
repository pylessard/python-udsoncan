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

	def test_rdbi_single_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x22\x00\x01")
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34")	# Positive response

	def _test_rdbi_single_success(self):
		response = self.udsclient.read_data_by_identifier(dids = 1)
		self.assertTrue(response.positive)
		values = response.service_data.values
		self.assertEqual(values[1], (0x1234,))

	def test_rdbi_multiple_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x22\x00\x01\x00\x02\x00\x03")
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")	# Positive response

	def _test_rdbi_multiple_success(self):
		response = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertTrue(response.positive)
		values = response.service_data.values
		self.assertEqual(values[1], (0x1234,))		
		self.assertEqual(values[2], (0x7856,))		
		self.assertEqual(values[3], 0x10)	

	def test_rdbi_multiple_zero_padding1_success(self):
		data = b'\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11'
		for i in range(8):
			self.wait_request_and_respond(data + b"\x00"*(i+1))	

	def _test_rdbi_multiple_zero_padding1_success(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(8):
			response = self.udsclient.read_data_by_identifier(dids = [1,2,3])
			self.assertTrue(response.positive)
			values = response.service_data.values
			self.assertEqual(values[1], (0x1234,))		
			self.assertEqual(values[2], (0x7856,))		
			self.assertEqual(values[3], 0x10)
			self.assertFalse(0 in values)		

	def test_rdbi_multiple_zero_padding_not_tolerated_exception(self):
		data = b'\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11'
		for i in range(8):
			self.wait_request_and_respond(data + b"\x00"*(i+1))		

	def _test_rdbi_multiple_zero_padding_not_tolerated_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(1):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.read_data_by_identifier(dids = [1,2,3])

		for i in range(7):
			with self.assertRaises(UnexpectedResponseException):	# Not requested DID 0x0000
				self.udsclient.config['data_identifiers'][0] = 'B'*i
				self.udsclient.read_data_by_identifier(dids = [1,2,3])


	def test_rdbi_multiple_zero_padding_not_tolerated_no_exception(self):
		data = b'\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11'
		for i in range(8):
			self.wait_request_and_respond(data + b"\x00"*(i+1))		

	def _test_rdbi_multiple_zero_padding_not_tolerated_no_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False

		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['exception_on_unexpected_response'] = True
		for i in range(1):
			response = self.udsclient.read_data_by_identifier(dids = [1,2,3])
			self.assertFalse(response.valid)

		self.udsclient.config['exception_on_invalid_response'] = True
		self.udsclient.config['exception_on_unexpected_response'] = False
		for i in range(7):
			self.udsclient.config['data_identifiers'][0] = 'B'*i
			response = self.udsclient.read_data_by_identifier(dids = [1,2,3])
			self.assertTrue(response.valid)
			self.assertTrue(response.unexpected)		

	def test_rdbi_incomplete_response_exception(self):
		self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03")	

	def _test_rdbi_incomplete_response_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.read_data_by_identifier(dids = [1,2,3])

	def test_rdbi_incomplete_response_no_exception(self):
		self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03")	

	def _test_rdbi_incomplete_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertFalse(response.valid)

	def test_rdbi_unknown_did_exception(self):
		self.wait_request_and_respond(b"\x62\x00\x09\x12\x34\x00\x02\x56\x78\x00\x03\x11")	

	def _test_rdbi_unknown_did_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.read_data_by_identifier(dids = [1,2,3])	

	def test_rdbi_unknown_did_no_exception(self):
		self.wait_request_and_respond(b"\x62\x00\x09\x12\x34\x00\x02\x56\x78\x00\x03\x11")	

	def _test_rdbi_unknown_did_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)
	
	def test_rdbi_unwanted_did_exception(self):
		self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")

	def _test_rdbi_unwanted_did_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.read_data_by_identifier(dids = [1,3])	

	def test_rdbi_unwanted_did_no_exception(self):
		self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")

	def _test_rdbi_unwanted_did_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.read_data_by_identifier(dids = [1,3])
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_rdbi_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x00\x01\x12\x34")	# Service is inexistant

	def _test_rdbi_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.read_data_by_identifier(dids=1)

	def test_rdbi_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x00\x01\x12\x34")	# Service is inexistant

	def _test_rdbi_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.read_data_by_identifier(dids=1)	
		self.assertFalse(response.valid)

	def test_rdbi_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x50\x00\x01\x12\x34")	# Valid service, but not the one requested

	def _test_rdbi_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.read_data_by_identifier(dids=1)

	def test_rdbi_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x50\x00\x01\x12\x34")	# Valid service, but not the one requested

	def _test_rdbi_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.read_data_by_identifier(dids=1)	
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)		

	def test_no_config(self):
		pass

	def _test_no_config(self):
		with self.assertRaises(ConfigError):
			self.udsclient.read_data_by_identifier(dids=[1,2,3,4]) 