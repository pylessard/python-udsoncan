from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestAccessTimingParameter(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_read_extended_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x83\x01")
		self.conn.fromuserqueue.put(b"\xC3\x01\x99\x88\x77\x66")	# Positive response

	def _test_read_extended_params_success(self):
		response = self.udsclient.read_extended_timing_parameters()
		self.assertEqual(response.service_data.access_type_echo, 0x01)
		self.assertEqual(response.service_data.timing_param_record, b"\x99\x88\x77\x66")

	def test_read_extended_params_success_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x83\x81")
		self.conn.fromuserqueue.put('wait')

	def _test_read_extended_params_success_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.read_extended_timing_parameters()
		self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	# Avoid closing the conenction prematurely

	def test_read_active_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x83\x03")
		self.conn.fromuserqueue.put(b"\xC3\x03\x99\x88\x77\x66")	# Positive response

	def _test_read_active_params_success(self):
		response = self.udsclient.read_active_timing_parameters()
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.access_type_echo, 0x03)
		self.assertEqual(response.service_data.timing_param_record, b"\x99\x88\x77\x66")		

	def test_set_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x83\x04\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\xC3\x04")	# Positive response

	def _test_set_params_success(self):
		self.udsclient.set_timing_parameters(params=b"\x11\x22\x33\x44")

	def test_set_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x83\x02")
		self.conn.fromuserqueue.put(b"\xC3\x02")	# Positive response

	def _test_set_params_success(self):
		self.udsclient.reset_default_timing_parameters()

	def test_set_params_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x83\x31") #Request Out Of Range

	def _test_set_params_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

	def test_set_params_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x83\x31") #Request Out Of Range

	def _test_set_params_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.access_timing_parameter(access_type=0x22)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_set_params_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x22") #Inexistent Service

	def _test_set_params_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

	def test_set_params_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x22") #Inexistent Service

	def _test_set_params_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.access_timing_parameter(access_type=0x22)
		self.assertFalse(response.valid)

	def test_routine_control_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_routine_control_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

	def test_routine_control_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_routine_control_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.access_timing_parameter(access_type=0x22)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_access_timing_params_bad_access_type_exception(self):
		self.wait_request_and_respond(b"\xC3\x23") # Valid but access type

	def _test_access_timing_params_bad_access_type_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

	def test_access_timing_params_bad_access_type_no_exception(self):
		self.wait_request_and_respond(b"\xC3\x23") # Valid but access type

	def _test_access_timing_params_bad_access_type_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.access_timing_parameter(access_type=0x22)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=0x100)

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.setTimingParametersToGivenValues, timing_param_record=None)

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.readExtendedTimingParameterSet, timing_param_record=b"\xaa\xbb")

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.setTimingParametersToDefaultValues, timing_param_record=123)
