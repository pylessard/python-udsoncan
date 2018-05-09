from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestRequestSeed(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_request_seed_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x27\x05")
		self.conn.fromuserqueue.put(b"\x67\x05\x99\x88\x77\x66")	# Positive response

	def _test_request_seed_success(self):
		response = self.udsclient.request_seed(0x05)
		self.assertEqual(response.service_data.seed, b"\x99\x88\x77\x66")

	def test_request_seed_success_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x27\x85")
		self.conn.fromuserqueue.put('wait')	# Synchronize 

	def _test_request_seed_success_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.request_seed(0x05)
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_request_seed_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x27\x22")	# Conditions Not Correct

	def _test_request_seed_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.request_seed(0x05)
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.SecurityAccess))
		self.assertEqual(response.code, 0x22)

	def test_request_seed_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x27\x22")	# Conditions Not Correct

	def _test_request_seed_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.request_seed(0x05)

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.SecurityAccess))
		self.assertEqual(response.code, 0x22)

	def test_request_seed_bad_subfn_exception(self):
		self.wait_request_and_respond(b"\x67\x06\x99\x88\x77\x66")	# Positive response with wrong subfunction

	def _test_request_seed_bad_subfn_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.request_seed(0x05)

	def test_request_seed_bad_subfn_no_exception(self):
		self.wait_request_and_respond(b"\x67\x06\x99\x88\x77\x66")	# Positive response with wrong subfunction

	def _test_request_seed_bad_subfn_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.request_seed(0x05)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_request_seed_incomplete_response_exception(self):
		self.wait_request_and_respond(b"\x67\x05")	# Positive response with no seed

	def _test_request_seed_incomplete_response_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.request_seed(0x05)

	def test_request_seed_incomplete_response_no_exception(self):
		self.wait_request_and_respond(b"\x67\x05")	# Positive response with no seed

	def _test_request_seed_incomplete_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.request_seed(0x05)
		self.assertFalse(response.valid)

	def test_request_seed_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x05") #Inexistent Service

	def _test_request_seed_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.request_seed(0x05)

	def test_request_seed_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x05") #Inexistent Service

	def _test_request_seed_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.request_seed(0x05)
		self.assertFalse(response.valid)

	def test_request_seed_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_request_seed_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.request_seed(0x05)

	def test_request_seed_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_request_seed_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.request_seed(0x05)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)
		
	def test_request_seed_bad_param(self):
		pass

	def _test_request_seed_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.request_seed(0x80)

		with self.assertRaises(ValueError):
			self.udsclient.request_seed(-1)


class TestSendKey(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_send_key_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x27\x06\x11\x22\x33\x44")
		self.conn.fromuserqueue.put(b"\x67\x06")	# Positive response

	def _test_send_key_success(self):
		response = self.udsclient.send_key(0x06,b"\x11\x22\x33\x44")
		self.assertTrue(response.positive)

	def test_send_key_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x27\x35")	# InvalidKey

	def _test_send_key_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.SecurityAccess))
		self.assertEqual(response.code, 0x35)

	def test_send_key_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x27\x35")	# InvalidKey

	def _test_send_key_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.SecurityAccess))
		self.assertEqual(response.code, 0x35)

	def test_send_key_bad_subfn_exception(self):
		self.wait_request_and_respond(b"\x67\x08\x99\x88\x77\x66")	# Positive response with wrong subfunction

	def _test_send_key_bad_subfn_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

	def test_send_key_bad_subfn_no_exception(self):
		self.wait_request_and_respond(b"\x67\x08\x99\x88\x77\x66")	# Positive response with wrong subfunction

	def _test_send_key_bad_subfn_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_send_key_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x06") #Inexistent Service

	def _test_send_key_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

	def test_send_key_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x06") #Inexistent Service

	def _test_send_key_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")
		self.assertFalse(response.valid)

	def test_send_key_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_send_key_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")

	def test_send_key_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

	def _test_send_key_wrongservice_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.send_key(0x06, b"\x11\x22\x33\x44")
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_send_key_bad_param(self):
		pass

	def _test_send_key_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.send_key(0x80, b"\x11\x22\x33\x44")

		with self.assertRaises(ValueError):
			self.udsclient.send_key(-1, b"\x11\x22\x33\x44")

		with self.assertRaises(ValueError):
			self.udsclient.send_key(1, 1)

		with self.assertRaises(ValueError):
			self.udsclient.send_key(1, 'xxx')


class TestUnlockSecurityService(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def dummy_algo(self, seed, params=None):
		key = bytearray(seed)
		for i in range(len(key)):
			key[i] ^= params
		return bytes(key)

	def test_unlock_success(self):
		for i in range(2):
			request = self.conn.touserqueue.get(timeout=0.2)
			self.assertEqual(request, b"\x27\x07")		# Request seed
			self.conn.fromuserqueue.put(b"\x67\x07\x11\x22\x33\x44")	# Positive response
			request = self.conn.touserqueue.get(timeout=0.2)
			self.assertEqual(request, b"\x27\x08\xEE\xDD\xCC\xBB")
			self.conn.fromuserqueue.put(b"\x67\x08")	# Positive response

	def _test_unlock_success(self):
		self.udsclient.config['security_algo'] = self.dummy_algo
		self.udsclient.config['security_algo_params'] = 0xFF
		response = self.udsclient.unlock_security_access(0x07)	
		response = self.udsclient.unlock_security_access(0x08)	
		self.assertTrue(response.positive)


	def test_unlock_seed_fail_exception(self):
		self.wait_request_and_respond(b"\x7F\x27\x11")	

	def _test_unlock_seed_fail_exception(self):
		self.udsclient.config['security_algo'] = self.dummy_algo
		self.udsclient.config['security_algo_params'] = 0xFF
		with self.assertRaises(NegativeResponseException):
			response = self.udsclient.unlock_security_access(0x07)	

	def test_unlock_seed_fail_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x27\x11")	

	def _test_unlock_seed_fail_no_exception(self):
		self.udsclient.config['security_algo'] = self.dummy_algo
		self.udsclient.config['security_algo_params'] = 0xFF
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.unlock_security_access(0x07)
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)

	def test_no_algo_set(self):
		pass

	def _test_no_algo_set(self):
		with self.assertRaises(NotImplementedError):
			self.udsclient.unlock_security_access(0x07)