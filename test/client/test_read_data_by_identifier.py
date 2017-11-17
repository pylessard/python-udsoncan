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

#========================================
	def test_rdbi_single_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x22\x00\x01")
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34")	# Positive response

	def _test_rdbi_single_success(self):
		values = self.udsclient.read_data_by_identifier(dids = 1)
		self.assertEqual(values[1], (0x1234,))

#========================================
	def test_rdbi_multiple_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x22\x00\x01\x00\x02\x00\x03")
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")	# Positive response

	def _test_rdbi_multiple_success(self):
		values = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertEqual(values[1], (0x1234,))		
		self.assertEqual(values[2], (0x7856,))		
		self.assertEqual(values[3], 0x10)	

#========================================
	def test_rdbi_multiple_zero_padding1_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00")				# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00\x00")			# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00\x00\x00")		# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00\x00\x00\x00")	# Positive response

	def _test_rdbi_multiple_zero_padding1_success(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		values = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertEqual(values[1], (0x1234,))		
		self.assertEqual(values[2], (0x7856,))		
		self.assertEqual(values[3], 0x10)
		self.assertFalse(0 in values)		

		values = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertEqual(values[1], (0x1234,))		
		self.assertEqual(values[2], (0x7856,))		
		self.assertEqual(values[3], 0x10)		
		self.assertFalse(0 in values)		

		values = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertEqual(values[1], (0x1234,))		
		self.assertEqual(values[2], (0x7856,))		
		self.assertEqual(values[3], 0x10)		
		self.assertFalse(0 in values)		

		values = self.udsclient.read_data_by_identifier(dids = [1,2,3])
		self.assertEqual(values[1], (0x1234,))		
		self.assertEqual(values[2], (0x7856,))		
		self.assertEqual(values[3], 0x10)	
		self.assertFalse(0 in values)		

#========================================
	def test_rdbi_multiple_zero_padding_not_tolerated(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00")				# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00\x00")			# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00\x00\x00")		# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11\x00\x00\x00\x00")	# Positive response

	def _test_rdbi_multiple_zero_padding_not_tolerated(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,2,3])

		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,2,3])	

		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,2,3])

		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,2,3])
			
#========================================
	def test_rdbi_output_format(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")	# Positive response
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")	# Positive response

	def _test_rdbi_output_format(self):
		values = self.udsclient.read_data_by_identifier(dids = [1,2,3], output_fmt="dict")
		self.assertTrue(isinstance(values, dict))	
		self.assertEqual(len(values), 3)		

		values = self.udsclient.read_data_by_identifier(dids = [1,2,3], output_fmt="list")
		self.assertTrue(isinstance(values, list))	
		self.assertEqual(len(values), 3)		

#========================================
	def test_rdbi_incomplete_response(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03")	# Positive response

	def _test_rdbi_incomplete_response(self):
		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,2,3])

#========================================
	def test_rdbi_unknown_did(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x09\x12\x34\x00\x02\x56\x78\x00\x03\x11")	# Positive response

	def _test_rdbi_unknown_did(self):
		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,2,3])			
	
#========================================
	def test_rdbi_unwanted_did(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")	# Positive response

	def _test_rdbi_unwanted_did(self):
		with self.assertRaises(UnexpectedResponseException):
			values = self.udsclient.read_data_by_identifier(dids = [1,3])			

#========================================
	def test_rdbi_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x00\x00\x01\x12\x34")	# Service is inexistant

	def _test_rdbi_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.read_data_by_identifier(dids=1)

#========================================
	def test_rdbi_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x50\x00\x01\x12\x34")	# Valid service, but not the one requested

	def _test_rdbi_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.read_data_by_identifier(dids=1)

#========================================
	def test_no_config(self):
		pass

	def _test_no_config(self):
		with self.assertRaises(LookupError):
			response = self.udsclient.read_data_by_identifier(dids=[1,2,3,4]) 