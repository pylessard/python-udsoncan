from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestRequestSeed(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_request_seed_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x67\x05\x99\x88\x77\x66")	# Positive response

	def _test_request_seed_success(self):
		seed = self.udsclient.request_seed(0x05)
		self.assertEqual(seed, b"\x99\x88\x77\x66")

#========================================
	def test_request_seed_denied(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x7F\x67\x22")	# Conditions Not Correct

	def _test_request_seed_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			seed = self.udsclient.request_seed(0x05)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.SecurityAccess))
		self.assertEqual(response.code, 0x22)

#========================================
	def test_request_seed_bad_subfn(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x67\x06\x99\x88\x77\x66")	# Positive response with wrong subfunction

	def _test_request_seed_bad_subfn(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			seed = self.udsclient.request_seed(0x05)

#========================================
	def test_request_seed_incomplete_response(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x67\x05")	# Positive response with no seed

	def _test_request_seed_incomplete_response(self):
		with self.assertRaises(InvalidResponseException) as handle:
			seed = self.udsclient.request_seed(0x05)

#========================================
	def test_request_seed_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x00\x05") #Inexistent Service

	def _test_request_seed_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.request_seed(0x05)

#========================================
	def test_request_seed_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_request_seed_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.request_seed(0x05)

#========================================
	def test_request_seed_bad_param(self):
		pass

	def _test_request_seed_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.request_seed(0x80)

		with self.assertRaises(ValueError):
			response = self.udsclient.request_seed(-1)

#============================================================================
#============================================================================

class TestSendKey(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_send_key_success(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x06\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\x67\x06")	# Positive response

	def _test_send_key_success(self):
		success = self.udsclient.send_key(0x06,b"\x11\x22\x33\x44")
		self.assertTrue(success)

#========================================
	def test_send_key_denied(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x06\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\x7F\x67\x35")	# InvalidKey

	def _test_send_key_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			success = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.SecurityAccess))
		self.assertEqual(response.code, 0x35)

#========================================
	def test_send_key_bad_subfn(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x06\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\x67\x08\x99\x88\x77\x66")	# Positive response with wrong subfunction

	def _test_send_key_bad_subfn(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			success = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

#========================================
	def test_send_key_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x06\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\x00\x06") #Inexistent Service

	def _test_send_key_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

#========================================
	def test_send_key_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.assertEqual(request, b"\x27\x06\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_send_key_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

#========================================
	def test_send_key_bad_param(self):
		pass

	def _test_send_key_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.send_key(0x80, b"\x11\x22\x33\x44")

		with self.assertRaises(ValueError):
			response = self.udsclient.send_key(-1, b"\x11\x22\x33\x44")

#============================================================================
#============================================================================

class TestUnlockSecurityService(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def dummy_algo(self, seed, params=None):
		key = bytearray(seed)
		for i in range(len(key)):
			key[i] ^= params
		return key

	def test_unlock_success(self):
		for i in range(2):
			request = self.conn.touserqueue.get(timeout=1)
			self.assertEqual(request, b"\x27\x07")		# Request seed
			self.conn.fromuserqueue.put(b"\x67\x07\x11\x22\x33\x44")	# Positive response
			request = self.conn.touserqueue.get(timeout=1)
			self.assertEqual(request, b"\x27\x08\xEE\xDD\xCC\xBB")
			self.conn.fromuserqueue.put(b"\x67\x08")	# Positive response

	def _test_unlock_success(self):
		self.udsclient.config['security_algo'] = self.dummy_algo
		self.udsclient.config['security_algo_params'] = 0xFF
		success = self.udsclient.unlock_security_access(0x07)	
		self.assertTrue(success)

		success = self.udsclient.unlock_security_access(0x08)
		self.assertTrue(success)

	def test_no_algo_set(self):
		pass

	def _test_no_algo_set(self):
		with self.assertRaises(NotImplementedError):
			self.udsclient.unlock_security_access(0x07)