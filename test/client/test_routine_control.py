from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestRoutineControl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_start_routine_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x31\x01\x00\x12\x45\x67\x89\xaa")
		self.conn.fromuserqueue.put(b"\x71\x01\x00\x12\x99\x88")	# Positive response

	def _test_start_routine_success(self):
		response = self.udsclient.start_routine(routine_id=0x12, data = b'\x45\x67\x89\xaa')
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, 0x1)
		self.assertEqual(response.service_data.routine_id_echo, 0x12)
		self.assertEqual(response.service_data.routine_status_record, b'\x99\x88')

	def test_start_routine_success_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x31\x81\x00\x12\x45\x67\x89\xaa")
		self.conn.fromuserqueue.put('wait')	# Synchronize

	def _test_start_routine_success_spr(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.start_routine(routine_id=0x12, data = b'\x45\x67\x89\xaa')
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_stop_routine_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x31\x02\x12\x34\x45\x67\x89\xaa")
		self.conn.fromuserqueue.put(b"\x71\x02\x12\x34\x99\x88")	# Positive response

	def _test_stop_routine_success(self):
		response = self.udsclient.stop_routine(routine_id=0x1234, data = b'\x45\x67\x89\xaa')
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, 0x2)
		self.assertEqual(response.service_data.routine_id_echo, 0x1234)
		self.assertEqual(response.service_data.routine_status_record, b'\x99\x88')

	def test_get_routine_result_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x31\x03\x12\x34\x45\x67\x89\xaa")
		self.conn.fromuserqueue.put(b"\x71\x03\x12\x34\x99\x88")	# Positive response

	def _test_get_routine_result_success(self):
		response = self.udsclient.get_routine_result(routine_id=0x1234, data = b'\x45\x67\x89\xaa')
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, 0x3)
		self.assertEqual(response.service_data.routine_id_echo, 0x1234)
		self.assertEqual(response.service_data.routine_status_record, b'\x99\x88')

	def test_routine_control_denied_exception(self):
		self.wait_request_and_respond(b"\x7F\x31\x72") #General Programming FAilure

	def _test_routine_control_denied_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.RoutineControl))
		self.assertEqual(response.code, 0x72)

	def test_routine_control_denied_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x31\x72") #General Programming FAilure

	def _test_routine_control_denied_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		self.assertTrue(issubclass(response.service, services.RoutineControl))
		self.assertEqual(response.code, 0x72)

	def test_routine_control_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x11\x12\x34") #Inexistent Service

	def _test_routine_control_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

	def test_routine_control_invalidservice_no_exception(self):
		self.wait_request_and_respond(b"\x00\x11\x12\x34") #Inexistent Service

	def _test_routine_control_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')
		self.assertFalse(response.valid)

	def test_routine_control_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x11\x12\x34") # Valid but wrong service (Tester Present)

	def _test_routine_control_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

	def test_routine_control_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x11\x12\x34") # Valid but wrong service (Tester Present)

	def _test_routine_control_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_routine_control_bad_controltype_exception(self):
		self.wait_request_and_respond(b"\x71\x12\x12\x34") # Valid but wrong service (Tester Present)

	def _test_routine_control_bad_controltype_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

	def test_routine_control_bad_controltype_no_exception(self):
		self.wait_request_and_respond(b"\x71\x12\x12\x34") # Valid but wrong service (Tester Present)

	def _test_routine_control_bad_controltype_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_routine_control_bad_routine_id_exception(self):
		self.wait_request_and_respond(b"\x71\x11\x12\x35") # Valid but wrong service (Tester Present)

	def _test_routine_control_bad_routine_id_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

	def test_routine_control_bad_routine_id_no_exception(self):
		self.wait_request_and_respond(b"\x71\x11\x12\x35") # Valid but wrong service (Tester Present)

	def _test_routine_control_bad_routine_id_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)		

	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.routine_control(routine_id=-1, control_type=1)

		with self.assertRaises(ValueError):
			self.udsclient.routine_control(routine_id=0x10000, control_type=1)

		with self.assertRaises(ValueError):
			self.udsclient.routine_control(routine_id=1, control_type=-1)

		with self.assertRaises(ValueError):
			self.udsclient.routine_control(routine_id=1, control_type=0x80)

		with self.assertRaises(ValueError):
			self.udsclient.routine_control(routine_id=1, control_type=1, data=123)

