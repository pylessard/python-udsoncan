from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestTesterPresent(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
#========================================
	def test_tester_present_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x3E\x00")
		self.conn.fromuserqueue.put(b"\x7E\x00")	# Positive response

	def _test_tester_present_success(self):
		success = self.udsclient.tester_present()
		self.assertTrue(success)

#========================================
	def test_tester_present_denied(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x3E\x00")
		self.conn.fromuserqueue.put(b"\x7F\x3E\x13") # IMLOIF

	def _test_tester_present_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.tester_present()
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.TesterPresent))
		self.assertEqual(response.code, 0x13)

#========================================
	def test_tester_present_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x3E\x00")
		self.conn.fromuserqueue.put(b"\x00\x00") #Inexistent Service

	def _test_tester_present_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.tester_present()

#========================================
	def test_tester_present_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x3E\x00")
		self.conn.fromuserqueue.put(b"\x50\x00") # Valid but wrong service (Tester Present)

	def _test_tester_present_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.tester_present()

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.tester_present(1) 