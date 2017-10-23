from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestDiagnosticSessionControl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_dsc_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x10\x01")
		self.conn.fromuserqueue.put(b"\x50\x01")	# Positive response

	def _test_dsc_success(self):
		success = self.udsclient.change_session(services.DiagnosticSessionControl.defaultSession)
		self.assertTrue(success)

#========================================
	def test_dsc_denied(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x10\x08")
		self.conn.fromuserqueue.put(b"\x50\x7F\x12") # Subfunction not supported

	def _test_dsc_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.change_session(0x08)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.DiagnosticSessionControl))
		self.assertEqual(response.code, 0x12)


#========================================
	def test_dsc_bad_subfunction(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x10\x01")
		self.conn.fromuserqueue.put(b"\x50\x02")	# Positive response

	def _test_dsc_bad_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			success = self.udsclient.change_session(services.DiagnosticSessionControl.defaultSession)

#========================================
	def test_dsc_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x10\x02")
		self.conn.fromuserqueue.put(b"\x00\x02") #Inexistent Service

	def _test_dsc_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			success = self.udsclient.change_session(0x02)


#========================================
	def test_ecu_reset_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x10\x55")
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_ecu_reset_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			success = self.udsclient.change_session(0x55)


#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			success = self.udsclient.change_session(0x100)

		with self.assertRaises(ValueError):
			success = self.udsclient.change_session(-1)
