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
		self.conn.fromuserqueue.put(b"\x71\x01\x00\x12")	# Positive response


	def _test_start_routine_success(self):
		response = self.udsclient.start_routine(routine_id=0x12, data = b'\x45\x67\x89\xaa')
		self.assertTrue(self.udsclient.last_response.positive)

	def test_stop_routine_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x31\x02\x12\x34\x45\x67\x89\xaa")
		self.conn.fromuserqueue.put(b"\x71\x02\x12\x34")	# Positive response


	def _test_stop_routine_success(self):
		response = self.udsclient.stop_routine(routine_id=0x1234, data = b'\x45\x67\x89\xaa')
		self.assertTrue(self.udsclient.last_response.positive)

	def test_get_routine_result_success(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x31\x03\x12\x34\x45\x67\x89\xaa")
		self.conn.fromuserqueue.put(b"\x71\x03\x12\x34")	# Positive response


	def _test_get_routine_result_success(self):
		response = self.udsclient.get_routine_result(routine_id=0x1234, data = b'\x45\x67\x89\xaa')
		self.assertTrue(self.udsclient.last_response.positive)


	def test_routine_control_denied(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x7F\x31\x72") #General Programming FAilure

	def _test_routine_control_denied(self):
		with self.assertRaises(NegativeResponseException) as handle:
			response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')
		response = handle.exception.response

		self.assertTrue(response.valid)
		self.assertTrue(issubclass(response.service, services.RoutineControl))
		self.assertEqual(response.code, 0x72)

	def test_routine_control_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x00\x11\x12\x34") #Inexistent Service

	def _test_routine_control_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

	def test_routine_control_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x7E\x11\x12\x34") # Valid but wrong service (Tester Present)

	def _test_routine_control_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')

	def test_routine_control_bad_controltype(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x71\x12\x12\x34") # Valid but wrong service (Tester Present)

	def _test_routine_control_bad_controltype(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')


	def test_routine_control_bad_routine_id(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x71\x11\x12\x35") # Valid but wrong service (Tester Present)

	def _test_routine_control_bad_routine_id(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			response = self.udsclient.routine_control(routine_id=0x1234, control_type=0x11, data=b'\x99\x88')


	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			response = self.udsclient.routine_control(routine_id=-1, control_type=1)

		with self.assertRaises(ValueError):
			response = self.udsclient.routine_control(routine_id=0x10000, control_type=1)

		with self.assertRaises(ValueError):
			response = self.udsclient.routine_control(routine_id=1, control_type=-1)

		with self.assertRaises(ValueError):
			response = self.udsclient.routine_control(routine_id=1, control_type=0x80)
