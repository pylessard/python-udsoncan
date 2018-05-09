from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestControlDTCSettings(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_set_on(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x85\x01")
		self.conn.fromuserqueue.put(b"\xC5\x01")	# Positive response

	def _test_set_on(self):
		response = self.udsclient.control_dtc_setting(services.ControlDTCSetting.SettingType.on)
		self.assertEqual(response.service_data.setting_type_echo, services.ControlDTCSetting.SettingType.on)

	def test_set_on_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x85\x81")
		self.conn.fromuserqueue.put("wait")	# Synchronize

	def _test_set_on_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.control_dtc_setting(services.ControlDTCSetting.SettingType.on)
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_set_on_with_extra_data(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x85\x01\x11\x22\x33")
		self.conn.fromuserqueue.put(b"\xC5\x01")	# Positive response

	def _test_set_on_with_extra_data(self):
		response = self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.SettingType.on, data=b'\x11\x22\x33')
		self.assertEqual(response.service_data.setting_type_echo, services.ControlDTCSetting.SettingType.on)

	def test_set_on_harmless_extra_bytes_in_response(self):
		self.wait_request_and_respond(b"\xC5\x01\x77\x88\x99")	# Positive response

	def _test_set_on_harmless_extra_bytes_in_response(self):
		response = self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.SettingType.on)
		self.assertEqual(response.service_data.setting_type_echo, services.ControlDTCSetting.SettingType.on)

	def test_set_params_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x85\x45") #Request Out Of Range

	def _test_set_params_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x45)

	def test_set_params_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x85\x45") #Request Out Of Range

	def _test_set_params_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.control_dtc_setting(setting_type=0x45)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_set_params_invalid_service_exception(self):
		self.wait_request_and_respond(b"\x00\x45") #Inexistent Service

	def _test_set_params_invalid_service_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x45)

	def test_set_params_invalid_service_no_exception(self):
		self.wait_request_and_respond(b"\x00\x45") #Inexistent Service

	def _test_set_params_invalid_service_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.control_dtc_setting(setting_type=0x45)
		self.assertFalse(response.valid)

	def test_wrong_service_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_wrong_service_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x22)

	def test_wrong_service_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_wrong_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.control_dtc_setting(setting_type=0x22)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_setting_type_response_exception(self):
		self.wait_request_and_respond(b"\xC5\x23") # Valid but access type

	def _test_bad_setting_type_response_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.control_dtc_setting(setting_type=0x22)

	def test_bad_setting_type_response_no_exception(self):
		self.wait_request_and_respond(b"\xC5\x23") # Valid but access type

	def _test_bad_setting_type_response_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.control_dtc_setting(setting_type=0x22)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.control_dtc_setting(setting_type=-1)

		with self.assertRaises(ValueError):
			self.udsclient.control_dtc_setting(setting_type=0x80)

		with self.assertRaises(ValueError):
			self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.SettingType.on, data=1)

		with self.assertRaises(ValueError):
			self.udsclient.control_dtc_setting(setting_type=services.ControlDTCSetting.SettingType.on, data='asdasdasd')
