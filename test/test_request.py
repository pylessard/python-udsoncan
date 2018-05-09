from udsoncan import Request, services
from test.UdsTest import UdsTest

class DummyServiceNormal(services.BaseService):
	_sid = 0x13

class DummyServiceNoSubunction(services.BaseService):
	_sid = 0x13
	_use_subfunction = False


class TestRequest(UdsTest):
	
	def test_create_from_instance_ok(self):
		req = Request(DummyServiceNormal())
		self.assertEqual(req.service.request_id(), 0x13)

	def test_create_from_class_ok(self):
		req = Request(DummyServiceNormal, subfunction=0x44)
		self.assertEqual(req.service.request_id(), 0x13)

	def test_make_payload_basic(self):
		req = Request(DummyServiceNormal, subfunction=0x44)
		payload = req.get_payload()
		self.assertEqual(b"\x13\x44", payload)

	def test_make_payload_custom_data(self):
		req = Request(DummyServiceNormal, subfunction=0x44)
		req.data = b"\x12\x34\x56\x78"
		payload = req.get_payload()
		self.assertEqual(b"\x13\x44\x12\x34\x56\x78", payload)
	
	def test_make_payload_custom_data_no_subfunction(self):
		req = Request(DummyServiceNoSubunction, subfunction=0x44)
		req.data = b"\x12\x34\x56\x78"
		payload = req.get_payload()
		self.assertEqual(b"\x13\x12\x34\x56\x78", payload)			

	def test_suppress_positive_response(self):
		req = Request(DummyServiceNormal, subfunction=0x44, suppress_positive_response=True)
		payload = req.get_payload()
		self.assertEqual(b"\x13\xC4", payload)	# Subfunction bit 7 is set

	def test_suppress_positive_response_override(self):
		req = Request(DummyServiceNormal, subfunction=0x44, suppress_positive_response=False)
		payload = req.get_payload(suppress_positive_response=True)
		self.assertEqual(b"\x13\xC4", payload)	# Subfunction bit 7 is set	

		req = Request(DummyServiceNormal, subfunction=0x44, suppress_positive_response=True)
		payload = req.get_payload(suppress_positive_response=False)
		self.assertEqual(b"\x13\x44", payload)	# Subfunction bit 7 is cleared		

	def test_from_payload_basic(self):
		payload=b'\x3E\x01'	# 0x3e = TesterPresent
		req = Request.from_payload(payload)
		self.assertEqual(req.service.request_id(), 0x3E)
		self.assertEqual(req.subfunction, 0x01)
		self.assertFalse(req.suppress_positive_response, 0x01)

	def test_from_payload_suppress_positive_response(self):
		payload=b'\x3E\x81'	# 0x3e = TesterPresent
		req = Request.from_payload(payload)
		self.assertEqual(req.service.request_id(), 0x3E)
		self.assertEqual(req.subfunction, 0x01)
		self.assertTrue(req.suppress_positive_response)

	def test_from_payload_custom_data(self):
		payload=b'\x3E\x01\x12\x34\x56\x78'	# 0x3E = TesterPresent
		req = Request.from_payload(payload)
		self.assertEqual(req.service.request_id(), 0x3E)
		self.assertEqual(req.subfunction, 0x01)
		self.assertEqual(req.data, b'\x12\x34\x56\x78')

	def test_from_empty_payload(self):
		payload = b''
		req = Request.from_payload(payload)
		self.assertIsNone(req.service)
		self.assertIsNone(req.subfunction)
		self.assertIsNone(req.data)

	def test_from_bad_payload(self):
		payload = b'\xFF\xFF'
		req = Request.from_payload(payload)
		self.assertIsNone(req.service)
		self.assertIsNone(req.subfunction)
		self.assertIsNone(req.data)

	def test_str_repr(self):
		req = Request(DummyServiceNormal)
		str(req)
		req.__repr__()

	def test_from_input_param(self):
		with self.assertRaises(ValueError):
			req = Request("a string")	

		with self.assertRaises(ValueError):
			req = Request(DummyServiceNormal, "string")	

		with self.assertRaises(ValueError):
			req = Request(DummyServiceNormal(), data=123)	

	def test_spr_with_no_subfunction(self):
		with self.assertRaises(ValueError):
			Request(service=DummyServiceNoSubunction, suppress_positive_response=True)

