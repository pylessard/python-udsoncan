from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestClearDtc(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_clear_dtc_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x14\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x54")	# Positive response

	def _test_clear_dtc_success(self):
		success = self.udsclient.clear_dtc(0x123456)
		self.assertTrue(success)

#========================================
	def test_clear_dtc_all(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x14\xFF\xFF\xFF")
		self.conn.fromuserqueue.put(b"\x54")	# Positive response

	def _test_clear_dtc_all(self):
		success = self.udsclient.clear_dtc()
		self.assertTrue(success)

#========================================
	def test_clear_dtc_denied(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x7F\x54\x31") #Request Out Of Range

	def _test_clear_dtc_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.clear_dtc(0x123456)

#========================================
	def test_clear_dtc_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x00") #Inexistent Service

	def _test_clear_dtc_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.clear_dtc(0x123456)

#========================================
	def test_clear_dtc_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_clear_dtc_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.clear_dtc(0x123456)

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.clear_dtc(0x1000000)

		with self.assertRaises(ValueError):
			response = self.udsclient.clear_dtc(-1)