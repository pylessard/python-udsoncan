from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestECUReset(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_ecu_reset_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x51\x55")	# Positive response

	def _test_ecu_reset_success(self):
		success = self.udsclient.ecu_reset(0x55)
		self.assertTrue(success)

#========================================
	def test_ecu_reset_success_pdt(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x04\x23")
		self.conn.fromuserqueue.put(b"\x51\x04")	# Positive response 

	def _test_ecu_reset_success_pdt(self):
		success = self.udsclient.ecu_reset(services.ECUReset.enableRapidPowerShutDown, 0x23)
		self.assertTrue(success)	

#========================================
	def test_ecu_reset_denied(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x7F\x11\x33") #Security Access Denied

	def _test_ecu_reset_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.ecu_reset(0x55)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.ECUReset))
		self.assertEqual(response.code, 0x33)

#========================================
	def test_ecu_reset_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x00\x55") #Inexistent Service

	def _test_ecu_reset_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.ecu_reset(0x55)

#========================================
	def test_ecu_reset_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x11\x55")
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.ecu_reset(0x55)

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(0x100)

		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.ecu_reset(0, powerdowntime = 123)	# Power Down time only valid with rapid shutdown
