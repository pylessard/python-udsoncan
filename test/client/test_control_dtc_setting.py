from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestControlDTCSettings(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_set_on(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x85\x01")
		self.conn.fromuserqueue.put(b"\xC5\x01")	# Positive response

	def _test_set_on(self):
		self.udsclient.control_dtc_setting(services.ControlDTCSetting.on)

#========================================
	def test_set_on_with_extra_data(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x85\x01\x11\x22\x33")
		self.conn.fromuserqueue.put(b"\xC5\x01")	# Positive response

	def _test_set_on_with_extra_data(self):
		self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.on, data=b'\x11\x22\x33')

#========================================
	def test_set_on_harmless_extra_bytes_in_response(self):
		self.wait_request_and_respond(b"\xC5\x01\x77\x88\x99")	# Positive response

	def _test_set_on_harmless_extra_bytes_in_response(self):
		self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.on)

#========================================
	def test_set_params_denied(self):
		self.wait_request_and_respond(b"\x7F\x85\x45") #Request Out Of Range

	def _test_set_params_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x45)

#========================================
	def test_set_params_invalid_service(self):
		self.wait_request_and_respond(b"\x00\x45") #Inexistent Service

	def _test_set_params_invalid_service(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x45)

#========================================
	def test_wrong_service(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_wrong_service(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x22)

#========================================
	def test_bad_setting_type_response(self):
		self.wait_request_and_respond(b"\xC5\x23") # Valid but access type

	def _test_bad_setting_type_response(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x22)

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.control_dtc_setting(setting_type=-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.control_dtc_setting(setting_type=0x80)

		with self.assertRaises(ValueError):
			response = self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.on, data=1)

		with self.assertRaises(ValueError):
			response = self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.on, data='asdasdasd')
