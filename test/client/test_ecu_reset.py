from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestECUReset(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_ecu_reset_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x51\x55")	# Positive response

	def _test_ecu_reset_success(self):
		response = self.udsclient.ecu_reset(0x55)
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.reset_type_echo, 0x55)

	def test_ecu_reset_success_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\xD5")
		self.conn.fromuserqueue.put("wait")	# Synchronize

	def _test_ecu_reset_success_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.ecu_reset(0x55)
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_ecu_reset_success_pdt(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x04")
		self.conn.fromuserqueue.put(b"\x51\x04\x23")	# Positive response 

	def _test_ecu_reset_success_pdt(self):
		response = self.udsclient.ecu_reset(services.ECUReset.ResetType.enableRapidPowerShutDown)
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.reset_type_echo, services.ECUReset.ResetType.enableRapidPowerShutDown)
		self.assertEqual(response.service_data.powerdown_time, 0x23)

	def test_ecu_reset_denied_exception(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x7F\x11\x33") #Security Access Denied

	def _test_ecu_reset_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.ecu_reset(0x55)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.ECUReset))
		self.assertEqual(response.code, 0x33)

	def test_ecu_reset_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x11\x33") #Security Access Denied

	def _test_ecu_reset_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.ecu_reset(0x55)

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.ECUReset))
		self.assertEqual(response.code, 0x33)

	def test_ecu_reset_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x55") #Inexistent Service

	def _test_ecu_reset_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.ecu_reset(0x55)
	
	def test_ecu_reset_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x55") #Inexistent Service

	def _test_ecu_reset_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.ecu_reset(0x55)

	def test_ecu_reset_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.ecu_reset(0x55)

	def test_ecu_reset_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.ecu_reset(0x55)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_ecu_reset_missing_pdt_exception(self):
		self.wait_request_and_respond(b"\x51\x04") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_missing_pdt_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.ecu_reset(services.ECUReset.ResetType.enableRapidPowerShutDown)

	def test_ecu_reset_missing_pdt_no_exception(self):
		self.wait_request_and_respond(b"\x51\x04") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_missing_pdt_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.ecu_reset(services.ECUReset.ResetType.enableRapidPowerShutDown)
		self.assertFalse(response.valid)

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(0x100)

		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(-1)