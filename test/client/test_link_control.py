from udsoncan.client import Client
from udsoncan import services, Baudrate
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestLinkContorl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_linkcontrol_verify_fixed(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x01\x11")
		self.conn.fromuserqueue.put(b"\xC7\x01")	# Positive response

	def _test_linkcontrol_verify_fixed(self):
		baudrate = Baudrate(250000, baudtype=Baudrate.Type.Fixed)
		response = self.udsclient.link_control(control_type=1, baudrate=baudrate)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, 1)

	def test_linkcontrol_verify_fixed_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x81\x11")
		self.conn.fromuserqueue.put("wait")	# Synchronize

	def _test_linkcontrol_verify_fixed_spr(self):
		baudrate = Baudrate(250000, baudtype=Baudrate.Type.Fixed)
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.link_control(control_type=1, baudrate=baudrate)
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_linkcontrol_verify_fixed_from_specific(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x01\x11")
		self.conn.fromuserqueue.put(b"\xC7\x01")	# Positive response

	def _test_linkcontrol_verify_fixed_from_specific(self):
		baudrate = Baudrate(250000, baudtype=Baudrate.Type.Specific)
		response = self.udsclient.link_control(control_type=1, baudrate=baudrate)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, 1)

	def test_linkcontrol_verify_specific(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x02\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\xC7\x02")	# Positive response

	def _test_linkcontrol_verify_specific(self):
		baudrate = Baudrate(0x123456, baudtype=Baudrate.Type.Specific)
		response = self.udsclient.link_control(control_type=2, baudrate=baudrate)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, 2)

	def test_linkcontrol_verify_specific_from_fixed(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x02\x07\xA1\x20")
		self.conn.fromuserqueue.put(b"\xC7\x02")	# Positive response

	def _test_linkcontrol_verify_specific_from_fixed(self):
		baudrate = Baudrate(500000, baudtype=Baudrate.Type.Fixed)
		response = self.udsclient.link_control(control_type=2, baudrate=baudrate)
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)

	def test_linkcontrol_custom_control_type(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x55")
		self.conn.fromuserqueue.put(b"\xC7\x55")	# Positive response

	def _test_linkcontrol_custom_control_type(self):
		response = self.udsclient.link_control(control_type=0x55)	
		self.assertTrue(response.valid)
		self.assertTrue(response.positive)

	def test_linkcontrol_negative_response_exception(self):
		self.wait_request_and_respond(b"\x7F\x87\x31") 	# Request Out Of Range

	def _test_linkcontrol_negative_response_exception(self):
		with self.assertRaises(NegativeResponseException):
			self.udsclient.link_control(control_type=0x55)

	def test_linkcontrol_negative_response_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x87\x31") 	# Request Out Of Range

	def _test_linkcontrol_negative_response_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.link_control(control_type=0x55)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_linkcontrol_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x22") 	# Request Out Of Range

	def _test_linkcontrol_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.link_control(control_type=0x55)

	def test_linkcontrol_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x22") 	# Request Out Of Range

	def _test_linkcontrol_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.link_control(control_type=0x55)
		self.assertFalse(response.valid)

	def test_linkcontrol_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_linkcontrol_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.link_control(control_type=0x55)
	
	def test_linkcontrol_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_linkcontrol_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.link_control(control_type=0x55)			
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_linkcontrol_bad_control_type_exception(self):
		self.wait_request_and_respond(b"\xC7\x08") # Valid but bad control type

	def _test_linkcontrol_bad_control_type_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.link_control(control_type=0x55)

	def test_linkcontrol_bad_control_type_no_exception(self):
		self.wait_request_and_respond(b"\xC7\x08") # Valid but bad control type

	def _test_linkcontrol_bad_control_type_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.link_control(control_type=0x55)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type='x')	

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=0x80)

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=1) # Missing Baudrate

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=2) # Missing Baudrate

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=0, baudrate=Baudrate(500000)) # Baudrate is not needed

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=1, baudrate=1) # Baudrate should be Baudrate instance

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=1, baudrate='x') # Baudrate should be Baudrate instance
