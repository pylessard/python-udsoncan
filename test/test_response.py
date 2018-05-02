from udsoncan import Response, services
from test.UdsTest import UdsTest

class DummyServiceNormal(services.BaseService):
	_sid = 0x13

	def subfunction_id(self):
		return 0x44

class DummyServiceNoSubunction(services.BaseService):
	_sid = 0x13
	_use_subfunction = False

class DummyServiceNoResponseData(services.BaseService):
	_sid = 0x13
	_no_response_data = True

class RandomClass:
	pass


class TestResponse(UdsTest):

	def test_create_from_instance_ok(self):
		response = Response(DummyServiceNormal(), code = 0x22)
		self.assertTrue(response.valid)
		self.assertEqual(response.service.request_id(), 0x13)
		self.assertEqual(response.code, 0x22)

	def test_create_from_class_ok(self):
		response = Response(DummyServiceNormal, code=0x22)
		self.assertTrue(response.valid)
		self.assertEqual(response.service.request_id(), 0x13)
		self.assertEqual(response.code, 0x22)

	def test_make_payload_basic_positive(self):
		response = Response(DummyServiceNormal(), code = 0, data=b"\x01")
		self.assertTrue(response.positive)
		self.assertTrue(response.valid)
		payload = response.get_payload()
		self.assertEqual(b"\x53\x01", payload)	# Original ID + 0x40

	def test_make_payload_basic_negative(self):
		response = Response(DummyServiceNormal(), code = 0x10) # General Reject
		self.assertFalse(response.positive)
		self.assertTrue(response.valid)
		payload = response.get_payload()
		self.assertEqual(b"\x7F\x13\x10", payload)	# Original ID + 0x40. 7F indicate negative

	def test_make_payload_custom_data_negative(self):
		response = Response(DummyServiceNormal(), code = 0x10)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		response.data = b"\x12\x34\x56\x78"
		payload = response.get_payload()
		self.assertEqual(b"\x7F\x13\x10\x12\x34\x56\x78", payload)

	def test_from_payload_basic_positive(self):
		payload=b'\x7E\x00'	# 0x7e = TesterPresent
		response = Response.from_payload(payload)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)
		self.assertEqual(response.service.response_id(), 0x7E)
		self.assertEqual(response.code, 0)
	
	def test_from_payload_basic_negative(self):
		payload=b'\x7F\x3E\x10'	# 0x3e = TesterPresent, 0x10 = General Reject
		response = Response.from_payload(payload)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertEqual(response.service.response_id(), 0x7E)
		self.assertEqual(response.code, 0x10)		
	
	def test_from_payload_custom_data_positive(self):
		payload=b'\x7E\x01\x12\x34\x56\x78'	# 0x3E = TesterPresent
		response = Response.from_payload(payload)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)
		self.assertEqual(response.service.response_id(), 0x7E)	
		self.assertEqual(response.data, b'\x01\x12\x34\x56\x78')

	def test_from_payload_custom_data_negative(self):
		payload=b'\x7F\x3E\x10\x12\x34\x56\x78'	# 0x3E = TesterPresent, 0x10 = General Reject
		response = Response.from_payload(payload)
		self.assertTrue(response.valid)
		self.assertEqual(response.service.response_id(), 0x7E)
		self.assertEqual(response.code, 0x10)	
		self.assertEqual(response.data, b'\x12\x34\x56\x78')

	def test_from_empty_payload(self):
		payload = b''
		response = Response.from_payload(payload)
		self.assertFalse(response.valid)
		self.assertIsNone(response.service)
		self.assertEqual(b'', response.data)

	def test_from_bad_payload(self):
		payload = b'\xFF\xFF'
		response = Response.from_payload(payload)
		self.assertFalse(response.valid)
		self.assertIsNone(response.service)
		self.assertEqual(b'', response.data)

	def test_str_repr(self):
		response = Response(DummyServiceNormal, code=0x22)
		str(response)
		response.__repr__()
		
	def test_from_input_param(self):
		with self.assertRaises(ValueError):
			response = Response(service = "a string")	

		with self.assertRaises(ValueError):
			response = Response(service = RandomClass())	

		with self.assertRaises(ValueError):
			response = Response(service=DummyServiceNormal(), code = "string")	

		with self.assertRaises(ValueError):
			response = Response(service=DummyServiceNormal(), code = -1)	

		with self.assertRaises(ValueError):
			response = Response(service=DummyServiceNormal(), code = 0x100)

		with self.assertRaises(ValueError):
			response = Response(service=DummyServiceNormal(), code = 0x10, data=11)	

