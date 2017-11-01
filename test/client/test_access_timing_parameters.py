from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestAccessTimingParameter(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_read_extended_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x83\x01")
		self.conn.fromuserqueue.put(b"\xC3\x01\x99\x88\x77\x66")	# Positive response


	def _test_read_extended_params_success(self):
		params = self.udsclient.read_extended_timing_parameters()
		self.assertEqual(params, b"\x99\x88\x77\x66")

#========================================
	def test_read_active_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x83\x03")
		self.conn.fromuserqueue.put(b"\xC3\x03\x99\x88\x77\x66")	# Positive response


	def _test_read_active_params_success(self):
		params = self.udsclient.read_active_timing_parameters()
		self.assertEqual(params, b"\x99\x88\x77\x66")		

#========================================
	def test_set_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x83\x04\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\xC3\x04")	# Positive response

	def _test_set_params_success(self):
		self.udsclient.set_timing_parameters(params=b"\x11\x22\x33\x44")


#========================================
	def test_set_params_success(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x83\x02")
		self.conn.fromuserqueue.put(b"\xC3\x02")	# Positive response

	def _test_set_params_success(self):
		self.udsclient.reset_default_timing_parameters()



#========================================
	def test_set_params_denied(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\xC3\x7F\x31") #Request Out Of Range

	def _test_set_params_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

#========================================
	def test_set_params_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x00\x22") #Inexistent Service

	def _test_set_params_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

#========================================
	def test_routine_control_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_routine_control_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

#========================================
	def test_access_timing_params_bad_access_type(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\xC3\x23") # Valid but access type

	def _test_access_timing_params_bad_access_type(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.access_timing_parameter(access_type=0x22)

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=0x80)

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=services.AccessTimingParameter.setTimingParametersToGivenValues, request_record=None)

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=services.AccessTimingParameter.readExtendedTimingParameterSet, request_record=b"\xaa\xbb")

		with self.assertRaises(ValueError):
			response = self.udsclient.access_timing_parameter(access_type=services.AccessTimingParameter.setTimingParametersToDefaultValues, request_record=123)
