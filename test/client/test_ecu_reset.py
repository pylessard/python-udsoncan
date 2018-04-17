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

	def test_ecu_reset_success_pdt(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x04\x23")
		self.conn.fromuserqueue.put(b"\x51\x04")	# Positive response 

	def _test_ecu_reset_success_pdt(self):
		response = self.udsclient.ecu_reset(services.ECUReset.ResetType.enableRapidPowerShutDown, 0x23)
		self.assertTrue(response.positive)

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

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(0x100)

		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(0, powerdowntime = 123)	# Power Down time only valid with rapid shutdown
