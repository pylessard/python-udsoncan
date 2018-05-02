from udsoncan.client import Client
from udsoncan import services, DidCodec
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest
from udsoncan import Dtc
import struct

class GenericTest_RequestStatusMask_ResponseNumberOfDTC():	
		
	def __init__(self, subfunction, client_function):
		self.sb = struct.pack('B', subfunction)
		self.badsb = struct.pack('B', subfunction+1)
		self.client_function = client_function
	
	def test_normal_behaviour_param_int(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_int(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(response.service_data.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.service_data.dtc_count, 0x1234)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_instance(self):
		response = getattr(self.udsclient, self.client_function).__call__(Dtc.Status(test_failed_this_operation_cycle = True, confirmed = True, test_not_completed_since_last_clear = True, test_not_completed_this_operation_cycle = True))
		self.assertEqual(response.service_data.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.service_data.dtc_count, 0x1234)

	def test_normal_behaviour_harmless_extra_byte(self):
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01\x12\x34\x00\x11\x22")

	def _test_normal_behaviour_harmless_extra_byte(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(response.service_data.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.service_data.dtc_count, 0x1234)		

	def test_bad_response_subfn_exception(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\xFB\x01\x12\x34")

	def _test_bad_response_subfn_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

	def test_bad_response_subfn_no_exception(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\xFB\x01\x12\x34")

	def _test_bad_response_subfn_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\xFB\x01\x12\x34")

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)	

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\xFB\x01\x12\x34")

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)	
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_length_response_exception(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB")
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01")
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01\x12")

	def _test_bad_length_response_exception(self):
		for i in range(5):
			with self.assertRaises(InvalidResponseException):
				getattr(self.udsclient, self.client_function).__call__(0x5A)

	def test_bad_length_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB")
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01")
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01\x12")

	def _test_bad_length_response_no_exception(self):
		for i in range(5):
			response = getattr(self.udsclient, self.client_function).__call__(0x5A)
			self.assertFalse(response.valid)

	def test_oob_value(self):
		pass

	def _test_oob_value(self):
		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_mask(0x100)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_mask(-1)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_mask('aaa')

class TestReportNumberOfDTCByStatusMask(ClientServerTest, GenericTest_RequestStatusMask_ResponseNumberOfDTC):	# Subfn = 0x1
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestStatusMaskRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x1, client_function = 'get_number_of_dtc_by_status_mask')

class GenericTestStatusMaskRequest_DtcAndStatusMaskResponse():
	def __init__(self, subfunction, client_function):
		self.sb = struct.pack('B', subfunction)
		self.badsb = struct.pack('B', subfunction+1)
		self.client_function = client_function


	def client_assert_response(self, response, expect_all_zero_third_dtc=False):
		self.assertEqual(response.service_data.status_availability.get_byte_as_int(), 0xFB)
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.service_data.dtcs), number_of_dtc)
		self.assertEqual(response.service_data.dtc_count, number_of_dtc)

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.service_data.dtcs[0].severity.get_byte_as_int(), 0x00)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123457)
		self.assertEqual(response.service_data.dtcs[1].status.get_byte_as_int(), 0x60)
		self.assertEqual(response.service_data.dtcs[1].severity.get_byte_as_int(), 0x00)
		
		if expect_all_zero_third_dtc:
			self.assertEqual(response.service_data.dtcs[2].id, 0)
			self.assertEqual(response.service_data.dtcs[2].status.get_byte_as_int(), 0x00)
			self.assertEqual(response.service_data.dtcs[2].severity.get_byte_as_int(), 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x12\x34\x56\x20\x12\x34\x57\x60")	

	def _test_normal_behaviour(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.client_assert_response(response)

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x12\x34\x56\x20\x12\x34\x56\x60")

	def _test_dtc_duplicate(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(len(response.service_data.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x20)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[1].status.get_byte_as_int(), 0x60)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x12\x34\x56\x20\x12\x34\x57\x60")	

	def _test_normal_behaviour_param_instance(self):
		getattr(self.udsclient, self.client_function).__call__(Dtc.Status(test_failed_this_operation_cycle = True, confirmed = True, test_not_completed_since_last_clear = True, test_not_completed_this_operation_cycle = True))

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		data = b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60'

		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True

		for i in range(5):
			response = getattr(self.udsclient, self.client_function).__call__(0x5A)
			self.client_assert_response(response, expect_all_zero_third_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		data = b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False

		expect_all_zero_third_dtc_values = [False, False, False, True, True]
		for i in range(5):
			response = getattr(self.udsclient, self.client_function).__call__(0x5A)
			self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	# Since we ignore all 0 DTC, we consider case number 4 with 4 extra 0 like a valid answer just like these 0 were not ther
	def test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		data = b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		exception_values = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, False, None]

		for i in range(5):
			if exception_values[i]:
				with self.assertRaises(InvalidResponseException):
					getattr(self.udsclient, self.client_function).__call__(0x5A)
			else:
				response = getattr(self.udsclient, self.client_function).__call__(0x5A)
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	# Since we ignore all 0 DTC, we consider case number 4 with 4 extra 0 like a valid answer just like these 0 were not ther
	def test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		data = b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		exception_values = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, False, None]

		for i in range(5):
			response = getattr(self.udsclient, self.client_function).__call__(0x5A)
			if exception_values[i]:
				self.assertFalse(response.valid)
			else:
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	# Since we consider all 0 DTC, case number 4 with 4 extra 0 bytes is a valid response where DTC ID=0
	def test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		data = b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		exception_values = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, True, None]

		for i in range(5):
			if exception_values[i]:
				with self.assertRaises(InvalidResponseException):
					getattr(self.udsclient, self.client_function).__call__(0x5A)
			else:
				response = getattr(self.udsclient, self.client_function).__call__(0x5A)
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])
	
	# Since we consider all 0 DTC, case number 4 with 4 extra 0 bytes is a valid response where DTC ID=0
	def test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		data = b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		error_values = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, True, None]

		for i in range(5):
			response = getattr(self.udsclient, self.client_function).__call__(0x5A)
			if error_values[i]:
				self.assertFalse(response.valid)
			else:
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_no_dtc(self):
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB")	

	def _test_no_dtc(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(len(response.service_data.dtcs), 0)

	def test_bad_response_subfunction_exception(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\xFB")	

	def _test_bad_response_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

	def test_bad_response_subfunction_no_exception(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\xFB")

	def _test_bad_response_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\xFB")	

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)	

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\xFB")	

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_length_exception(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)	

	def _test_bad_response_length_exception(self):
		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

	def test_bad_response_length_no_exception(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)	

	def _test_bad_response_length_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertFalse(response.valid)
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertFalse(response.valid)

	def test_oob_value(self):
		pass

	def _test_oob_value(self):
		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(0x100)

		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(-1)

		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__('aaa')

class TestReportDTCByStatusMask(ClientServerTest, GenericTestStatusMaskRequest_DtcAndStatusMaskResponse):	# Subfn = 0x2
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestStatusMaskRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x2, client_function = 'get_dtc_by_status_mask')

class TestReportDTCSnapshotIdentification(ClientServerTest):	# Subfn = 0x3
	def client_assert_response(self, response, expect_all_zero_third_dtc=False):
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.service_data.dtcs), number_of_dtc)
		self.assertEqual(response.service_data.dtc_count, number_of_dtc)

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)		
		self.assertEqual(len(response.service_data.dtcs[0].snapshots), 2)
		self.assertEqual(response.service_data.dtcs[0].snapshots[0], 1)
		self.assertEqual(response.service_data.dtcs[0].snapshots[1], 2)

		self.assertEqual(response.service_data.dtcs[1].id, 0x789abc)		
		self.assertEqual(len(response.service_data.dtcs[1].snapshots), 1)
		self.assertEqual(response.service_data.dtcs[1].snapshots[0], 3)
		
		if expect_all_zero_third_dtc:
			self.assertEqual(response.service_data.dtcs[2].id, 0)		
			self.assertEqual(len(response.service_data.dtcs[2].snapshots), 1)
			self.assertEqual(response.service_data.dtcs[2].snapshots[0], 0)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x03")
		self.conn.fromuserqueue.put(b"\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03")	

	def _test_normal_behaviour(self):
		response = self.udsclient.get_dtc_snapshot_identification()
		self.client_assert_response(response)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		data = b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03'

		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		for i in range(5):
			response = self.udsclient.get_dtc_snapshot_identification()
			self.client_assert_response(response, expect_all_zero_third_dtc=False)
		
	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		data = b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		expect_all_zero_third_dtc_values = [False, False, False, True, True]
		for i in range(5):
			response = self.udsclient.get_dtc_snapshot_identification()
			self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		data = b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, False, None]

		for i in range(5):
			if must_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.udsclient.get_dtc_snapshot_identification()
			else:
				response = self.udsclient.get_dtc_snapshot_identification()
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		data = b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, False, None]

		for i in range(5):
			response = self.udsclient.get_dtc_snapshot_identification()
			if must_return_invalid[i]:
				self.assertFalse(response.valid)
			else:
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		data = b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03'

		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, True, None]

		for i in range(5):
			if must_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.udsclient.get_dtc_snapshot_identification()
			else:
				response = self.udsclient.get_dtc_snapshot_identification()
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		data = b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03'

		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, True, None]

		for i in range(5):
			response = self.udsclient.get_dtc_snapshot_identification()
			if must_return_invalid[i]:
				self.assertFalse(response.valid)
			else:
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_no_dtc(self):
		self.wait_request_and_respond(b"\x59\x03")	

	def _test_no_dtc(self):
		response  = self.udsclient.get_dtc_snapshot_identification()
		self.assertEqual(len(response.service_data.dtcs), 0)

	def test_bad_response_subfunction_exception(self):
		self.wait_request_and_respond(b"\x59\x04")	

	def _test_bad_response_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_identification()

	def test_bad_response_subfunction_no_exception(self):
		self.wait_request_and_respond(b"\x59\x04")	

	def _test_bad_response_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_identification()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b"\x6F\x03")	

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_identification()

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b"\x6F\x03")	

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_identification()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)			

	def test_bad_response_length_exception(self):
		self.wait_request_and_respond(b'\x59')	
		self.wait_request_and_respond(b'\x59\x03\x12')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12')	

	def _test_bad_response_length_exception(self):
		for i in range(5):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_identification()

	def test_bad_response_length_no_exception(self):
		self.wait_request_and_respond(b'\x59')	
		self.wait_request_and_respond(b'\x59\x03\x12')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12')	

	def _test_bad_response_length_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(5):
			response = self.udsclient.get_dtc_snapshot_identification()
			self.assertFalse(response.valid)

class TestReportDTCSnapshotRecordByDTCNumber(ClientServerTest):	# Subfn = 0x4
	
	class Codec4711(DidCodec):
		def encode(self, did_value):
			return struct.pack('>BBHB', did_value['ect'], did_value['tp'], did_value['rpm'], did_value['map'])

		def decode(self, did_payload):
			v = dict(ect=0, tp=0, rpm=0, map=0)
			(v['ect'], v['tp'], v['rpm'], v['map']) = struct.unpack('>BBHB', did_payload)
			return v

		def __len__(self):
			return 5

	class Codec4455(DidCodec):
		def encode(self, did_value):
			return struct.pack('>H', did_value)

		def decode(self, did_payload):
			return struct.unpack('>H', did_payload)[0]

		def __len__(self):
			return 2

	def postClientSetUp(self):
		self.udsclient.config["data_identifiers"] = {
			0x4455 : self.__class__.Codec4455,
			0x4711 : self.__class__.Codec4711,
			0x6789 : 'BBB'
		}

	def single_snapshot_assert_response(self, response):
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)

		self.assertEqual(len(dtc.snapshots), 1)
		snapshot = dtc.snapshots[0]

		self.assertTrue(isinstance(snapshot, Dtc.Snapshot))
		self.assertEqual(snapshot.record_number, 0x02)	
		self.assertEqual(snapshot.did, 0x4711)	

		self.assertEqual(dtc.snapshots[0].data['ect'], 0xA6)	# Engine Coolant Temp
		self.assertEqual(dtc.snapshots[0].data['tp'], 0x66)		# Throttle Position
		self.assertEqual(dtc.snapshots[0].data['rpm'], 0x750)	# Engine speed
		self.assertEqual(dtc.snapshots[0].data['map'], 0x20)  	# Manifoled Absolute Value

	def single_snapshot_2_dids_assert_response(self, response):
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)

		self.assertEqual(len(dtc.snapshots), 2)

		self.assertTrue(isinstance(dtc.snapshots[0], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[0].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[0].did, 0x4711)	

		self.assertTrue(isinstance(dtc.snapshots[1], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[1].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[1].did, 0x6789)	


		self.assertEqual(dtc.snapshots[0].data['ect'], 0xA6)	# Engine Coolant Temp
		self.assertEqual(dtc.snapshots[0].data['tp'], 0x66)		# Throttle Position
		self.assertEqual(dtc.snapshots[0].data['rpm'], 0x750)	# Engine speed
		self.assertEqual(dtc.snapshots[0].data['map'], 0x20)  	# Manifoled Absolute Value

		self.assertEqual(dtc.snapshots[1].data[0], 0x99)
		self.assertEqual(dtc.snapshots[1].data[1], 0x88)
		self.assertEqual(dtc.snapshots[1].data[2], 0x77)


	def test_single_snapshot(self): # Example provided in standard
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x04\x12\x34\x56\x02")
		self.conn.fromuserqueue.put(b"\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20")

	def _test_single_snapshot(self):
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=2)
		self.single_snapshot_assert_response(response)

	def test_single_snapshot_with_instance_param(self): # Example provided in standard
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x04\x12\x34\x56\x02")
		self.conn.fromuserqueue.put(b"\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20")

	def _test_single_snapshot_with_instance_param(self):
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=Dtc(0x123456), record_number=2)
		self.single_snapshot_assert_response(response)

	def test_single_snapshot_zeropadding_ok(self): # Example provided in standard
		data = b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20'
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_snapshot_zeropadding_ok(self):
		for i in range(7):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=2)
			self.single_snapshot_assert_response(response)

	def test_single_snapshot_zeropadding_notok_exception(self): # Example provided in standard
		data = b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20'
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_snapshot_zeropadding_notok_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range (7):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=2)

	def test_single_snapshot_zeropadding_notok_no_exception(self): # Example provided in standard
		data = b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20'
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_snapshot_zeropadding_notok_no_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range (7):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=2)
			self.assertFalse(response.valid)

	def test_single_snapshot_2_did(self): # Example provided in standard
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x04\x12\x34\x56\x02")
		self.conn.fromuserqueue.put(b"\x59\x04\x12\x34\x56\x24\x02\x02\x47\x11\xa6\x66\x07\x50\x20\x67\x89\x99\x88\x77")

	def _test_single_snapshot_2_did(self):
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=2)
		self.single_snapshot_2_dids_assert_response(response)

	def test_multiple_snapshot_multiple_did(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x04\x12\x34\x56\xFF")
		self.conn.fromuserqueue.put(b"\x59\x04\x12\x34\x56\x24\x02\x02\x47\x11\xa6\x66\x07\x50\x20\x67\x89\x99\x88\x77\x03\x01\x44\x55\x43\x21")

	def _test_multiple_snapshot_multiple_did(self):
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0xFF)

		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)

		self.assertEqual(len(dtc.snapshots), 3)

		self.assertTrue(isinstance(dtc.snapshots[0], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[0].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[0].did, 0x4711)	

		self.assertTrue(isinstance(dtc.snapshots[1], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[1].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[1].did, 0x6789)

		self.assertTrue(isinstance(dtc.snapshots[2], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[2].record_number, 0x03)	
		self.assertEqual(dtc.snapshots[2].did, 0x4455)	

		# data
		self.assertEqual(dtc.snapshots[0].data['ect'], 0xA6)	# Engine Coolant Temp
		self.assertEqual(dtc.snapshots[0].data['tp'], 0x66)		# Throttle Position
		self.assertEqual(dtc.snapshots[0].data['rpm'], 0x750)	# Engine speed
		self.assertEqual(dtc.snapshots[0].data['map'], 0x20)  	# Manifoled Absolute Value

		self.assertEqual(dtc.snapshots[1].data[0], 0x99)
		self.assertEqual(dtc.snapshots[1].data[1], 0x88)
		self.assertEqual(dtc.snapshots[1].data[2], 0x77)

		self.assertEqual(dtc.snapshots[2].data, 0x4321)

	def test_invalid_length_incomplete_dtc_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12')
		self.wait_request_and_respond(b'\x59\x04\x12\x34')

	def _test_invalid_length_incomplete_dtc_exception(self):
		for i in range(2):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_invalid_length_incomplete_dtc_no_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12')
		self.wait_request_and_respond(b'\x59\x04\x12\x34')

	def _test_invalid_length_incomplete_dtc_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(2):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
			self.assertFalse(response.valid)
	
	def test_invalid_length_missing_status_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56')

	def _test_invalid_length_missing_status_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_invalid_length_missing_status_no_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56')

	def _test_invalid_length_missing_status_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)			
		self.assertFalse(response.valid)

	def test_invalid_length_missing_identifier_number_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03')

	def _test_invalid_length_missing_identifier_number_exception(self):
		for i in range(2):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_invalid_length_missing_identifier_number_no_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03')

	def _test_invalid_length_missing_identifier_number_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(2):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
			self.assertFalse(response.valid)

	def invalid_length_missing_did_server_task(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x01')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x01\x67')

	def test_invalid_length_missing_did_exception(self):
		self.invalid_length_missing_did_server_task()

	def _test_invalid_length_missing_did_exception(self):
		for i in range(4):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0xFF)

	def test_invalid_length_missing_did_no_exception(self):
		self.invalid_length_missing_did_server_task()

	def _test_invalid_length_missing_did_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(4):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0xFF)
			self.assertFalse(response.valid)

	def invalid_length_missing_data_server_task(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x01\x67\x89')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x01\x67\x89\x99')
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x01\x67\x89\x99\x88')

	def test_invalid_length_missing_data_exception(self):
		self.invalid_length_missing_data_server_task()

	def _test_invalid_length_missing_data_exception(self):
		for i in range(9):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0xff)

	def test_invalid_length_missing_data_no_exception(self):
		self.invalid_length_missing_data_server_task()

	def _test_invalid_length_missing_data_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(9):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0xff)
			self.assertFalse(response.valid)

	def test_bad_subfunction_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_bad_subfunction_no_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x12\x34\x56\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_dtc_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x57\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_dtc_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_bad_dtc_no_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x57\x24\x02\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_dtc_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_record_number_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x03\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_record_number_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_bad_record_number_no_exception(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24\x03\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_record_number_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_no_record(self):
		self.wait_request_and_respond(b'\x59\x04\x12\x34\x56\x24')

	def _test_no_record(self):
		response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
		
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)
		dtc = response.service_data.dtcs[0]
		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)
		self.assertEqual(len(dtc.snapshots), 0)

	def test_no_record_zero_padding_ok(self):
		data = b'\x59\x04\x12\x34\x56\x24'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
		
	def _test_no_record_zero_padding_ok(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(8):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
			
			self.assertEqual(len(response.service_data.dtcs), 1)
			self.assertEqual(response.service_data.dtc_count, 1)
			dtc = response.service_data.dtcs[0]
			self.assertEqual(dtc.id, 0x123456)
			self.assertEqual(dtc.status.get_byte_as_int(), 0x24)
			self.assertEqual(len(dtc.snapshots), 0)

	def test_no_record_zero_padding_not_ok_exception(self):
		data = b'\x59\x04\x12\x34\x56\x24'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_no_record_zero_padding_not_ok_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)

	def test_no_record_zero_padding_not_ok_no_exception(self):
		data = b'\x59\x04\x12\x34\x56\x24'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_no_record_zero_padding_not_ok_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			response = self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x02)
			self.assertFalse(response.valid)

	def test_oob_values(self):
		pass

	def _test_oob_values(self):
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=-1, record_number=0x02)
		
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x1000000, record_number=0x02)
		
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=-1)
		
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_snapshot_by_dtc_number(dtc=0x123456, record_number=0x100)

class TestReportDTCSnapshotRecordByRecordNumber(ClientServerTest):	# Subfn = 0x5
	class Codec4711(DidCodec):
		def encode(self, did_value):
			return struct.pack('>BBHB', did_value['ect'], did_value['tp'], did_value['rpm'], did_value['map'])

		def decode(self, did_payload):
			v = dict(ect=0, tp=0, rpm=0, map=0)
			(v['ect'], v['tp'], v['rpm'], v['map']) = struct.unpack('>BBHB', did_payload)
			return v

		def __len__(self):
			return 5

	class Codec4455(DidCodec):
		def encode(self, did_value):
			return struct.pack('>H', did_value)

		def decode(self, did_payload):
			return struct.unpack('>H', did_payload)[0]

		def __len__(self):
			return 2

	def postClientSetUp(self):
		self.udsclient.config["data_identifiers"] = {
			0x4455 : self.__class__.Codec4455,
			0x4711 : self.__class__.Codec4711,
			0x6789 : 'BBB'
		}

	def single_snapshot_assert_response(self, response):
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)

		self.assertEqual(len(dtc.snapshots), 1)
		snapshot = dtc.snapshots[0]

		self.assertTrue(isinstance(snapshot, Dtc.Snapshot))
		self.assertEqual(snapshot.record_number, 0x02)	
		self.assertEqual(snapshot.did, 0x4711)	

		self.assertEqual(dtc.snapshots[0].data['ect'], 0xA6)	# Engine Coolant Temp
		self.assertEqual(dtc.snapshots[0].data['tp'], 0x66)		# Throttle Position
		self.assertEqual(dtc.snapshots[0].data['rpm'], 0x750)	# Engine speed
		self.assertEqual(dtc.snapshots[0].data['map'], 0x20)  	# Manifoled Absolute Value

	def single_snapshot_2_dids_assert_response(self, response):
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)

		self.assertEqual(len(dtc.snapshots), 2)

		self.assertTrue(isinstance(dtc.snapshots[0], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[0].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[0].did, 0x4711)	

		self.assertTrue(isinstance(dtc.snapshots[1], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[1].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[1].did, 0x6789)	


		self.assertEqual(dtc.snapshots[0].data['ect'], 0xA6)	# Engine Coolant Temp
		self.assertEqual(dtc.snapshots[0].data['tp'], 0x66)		# Throttle Position
		self.assertEqual(dtc.snapshots[0].data['rpm'], 0x750)	# Engine speed
		self.assertEqual(dtc.snapshots[0].data['map'], 0x20)  	# Manifoled Absolute Value

		self.assertEqual(dtc.snapshots[1].data[0], 0x99)
		self.assertEqual(dtc.snapshots[1].data[1], 0x88)
		self.assertEqual(dtc.snapshots[1].data[2], 0x77)

	def test_single_snapshot(self): # Example provided in standard
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x05\x02")
		self.conn.fromuserqueue.put(b"\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20")

	def _test_single_snapshot(self):
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=2)
		self.single_snapshot_assert_response(response)

	def test_single_snapshot_zeropadding_ok_1(self): # Example provided in standard
		data = b'\x59\x05\x02'
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_snapshot_zeropadding_ok_1(self):
		for i in range(7):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=2)
			self.assertEqual(len(response.service_data.dtcs), 0)

	def test_single_snapshot_zeropadding_ok_2(self): # Example provided in standard
		data = b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20'
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
	
	def _test_single_snapshot_zeropadding_ok_2(self):
		for i in range(7):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=2)
			self.single_snapshot_assert_response(response)

	def test_single_snapshot_zeropadding_notok_exception(self): # Example provided in standard
		data = b'\x59\x05\x00\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20'
		self.udsclient.config['tolerate_zero_padding'] = False

		# one extra 0 is valid for this subfunction, so we start with 2 extra 0 (i+2)
		for i in range(6):
			self.wait_request_and_respond(data + b'\x00' * (i + 2))

	def _test_single_snapshot_zeropadding_notok_exception(self):
		for i in range (6):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_record_number(record_number=0)

	def test_single_snapshot_zeropadding_notok_no_exception(self): # Example provided in standard
		data = b'\x59\x05\x00\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20'
		self.udsclient.config['tolerate_zero_padding'] = False

		# one extra 0 is valid for this subfunction, so we start with 2 extra 0 (i+2)
		for i in range(6):
			self.wait_request_and_respond(data + b'\x00' * (i + 2))

	def _test_single_snapshot_zeropadding_notok_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range (6):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0)
			self.assertFalse(response.valid)

	def test_single_snapshot_2_did(self): # Example provided in standard
		self.wait_request_and_respond(b"\x59\x05\x02\x12\x34\x56\x24\x02\x47\x11\xa6\x66\x07\x50\x20\x67\x89\x99\x88\x77")

	def _test_single_snapshot_2_did(self):
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=2)
		self.single_snapshot_2_dids_assert_response(response)

	def test_multiple_snapshot_multiple_dtc(self):
		self.wait_request_and_respond(b"\x59\x05\x02\x12\x34\x56\x24\x02\x47\x11\xa6\x66\x07\x50\x20\x67\x89\x99\x88\x77\x03\x12\x34\x57\x25\x01\x44\x55\x43\x21")

	def _test_multiple_snapshot_multiple_dtc(self):
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xFF)

		self.assertEqual(len(response.service_data.dtcs), 2)
		self.assertEqual(response.service_data.dtc_count, 2)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x24)

		self.assertEqual(len(dtc.snapshots), 2)

		self.assertTrue(isinstance(dtc.snapshots[0], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[0].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[0].did, 0x4711)	

		self.assertTrue(isinstance(dtc.snapshots[1], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[1].record_number, 0x02)	
		self.assertEqual(dtc.snapshots[1].did, 0x6789)
		
		# data
		self.assertEqual(dtc.snapshots[0].data['ect'], 0xA6)		# Engine Coolant Temp
		self.assertEqual(dtc.snapshots[0].data['tp'], 0x66)		# Throttle Position
		self.assertEqual(dtc.snapshots[0].data['rpm'], 0x750)	# Engine speed
		self.assertEqual(dtc.snapshots[0].data['map'], 0x20)  	# Manifoled Absolute Value

		self.assertEqual(dtc.snapshots[1].data[0], 0x99)
		self.assertEqual(dtc.snapshots[1].data[1], 0x88)
		self.assertEqual(dtc.snapshots[1].data[2], 0x77)

		dtc = response.service_data.dtcs[1]

		self.assertEqual(dtc.id, 0x123457)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x25)

		self.assertTrue(isinstance(dtc.snapshots[0], Dtc.Snapshot))
		self.assertEqual(dtc.snapshots[0].record_number, 0x03)	
		self.assertEqual(dtc.snapshots[0].did, 0x4455)	

		self.assertEqual(dtc.snapshots[0].data, 0x4321)

	def test_invalid_length_no_record_number_exception(self):
		self.wait_request_and_respond(b'\x59\x05')

	def _test_invalid_length_no_record_number_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)

	def test_invalid_length_no_record_number_no_exception(self):
		self.wait_request_and_respond(b'\x59\x05')

	def _test_invalid_length_no_record_number_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
		self.assertFalse(response.valid)

	def test_invalid_length_incomplete_dtc_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34')

	def _test_invalid_length_incomplete_dtc_exception(self):
		for i in range(2):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
	
	def test_invalid_length_incomplete_dtc_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34')

	def _test_invalid_length_incomplete_dtc_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(2):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
			self.assertFalse(response.valid)
	
	def test_invalid_length_missing_status_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56')

	def _test_invalid_length_missing_status_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)

	def test_invalid_length_missing_status_no_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56')

	def _test_invalid_length_missing_status_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
		self.assertFalse(response.valid)


	def invalid_length_missing_identifier_number_server_task(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x12\x34\x57\x25')

	def test_invalid_length_missing_identifier_number_exception(self):
		self.invalid_length_missing_identifier_number_server_task()

	def _test_invalid_length_missing_identifier_number_exception(self):
		for i in range(2):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xFF)

	def test_invalid_length_missing_identifier_number_no_exception(self):
		self.invalid_length_missing_identifier_number_server_task()

	def _test_invalid_length_missing_identifier_number_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(2):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xFF)
			self.assertFalse(response.valid)

	def invalid_length_missing_did_server_task(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x12\x34\x57\x25\x01')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x12\x34\x57\x25\x01\x67')

	def test_invalid_length_missing_did_exception(self):
		self.invalid_length_missing_did_server_task()

	def _test_invalid_length_missing_did_exception(self):
		for i in range(4):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xFF)

	def test_invalid_length_missing_did_no_exception(self):
		self.invalid_length_missing_did_server_task()

	def _test_invalid_length_missing_did_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(4):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xFF)
			self.assertFalse(response.valid)

	def invalid_length_missing_data_server_task(self):
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x12\x34\x57\x25\x01\x67\x89')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x12\x34\x57\x25\x01\x67\x89\x99')
		self.wait_request_and_respond(b'\x59\x05\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20\x03\x12\x34\x57\x25\x01\x67\x89\x99\x88')

	def test_invalid_length_missing_data_exception(self):
		self.invalid_length_missing_data_server_task()

	def _test_invalid_length_missing_data_exception(self):
		for i in range(8):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xff)

	def test_invalid_length_missing_data_no_exception(self):
		self.invalid_length_missing_data_server_task()

	def _test_invalid_length_missing_data_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(8):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0xff)
			self.assertFalse(response.valid)

	def test_bad_subfunction_exception(self):
		self.wait_request_and_respond(b'\x59\x06\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)

	def test_bad_subfunction_no_exception(self):
		self.wait_request_and_respond(b'\x59\x06\x02\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)		

	def test_bad_record_number_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x03\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_record_number_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)

	def test_bad_record_number_no_exception(self):
		self.wait_request_and_respond(b'\x59\x05\x03\x12\x34\x56\x24\x01\x47\x11\xa6\x66\x07\x50\x20')

	def _test_bad_record_number_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)	

	def test_no_record(self):
		self.wait_request_and_respond(b'\x59\x05\x02')

	def _test_no_record(self):
		response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
		
		self.assertEqual(len(response.service_data.dtcs), 0)
		self.assertEqual(response.service_data.dtc_count, 0)

	def test_no_record_zero_padding_ok(self):
		data = b'\x59\x05\x02'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_no_record_zero_padding_ok(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(8):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
			self.assertEqual(len(response.service_data.dtcs), 0)
			self.assertEqual(response.service_data.dtc_count, 0)

	def test_no_record_zero_padding_not_ok_exception(self):
		data = b'\x59\x05\x02'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_no_record_zero_padding_not_ok_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)

	def test_no_record_zero_padding_not_ok_no_exception(self):
		data = b'\x59\x05\x02'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_no_record_zero_padding_not_ok_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			response = self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x02)
			self.assertFalse(response.valid)

	def test_oob_values(self):
		pass

	def _test_oob_values(self):
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_snapshot_by_record_number(record_number=-1)
		
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_snapshot_by_record_number(record_number=0x100)

class GenericReportExtendedDataByRecordNumber():
	def __init__(self, subfunction, client_function):
		self.sb = struct.pack('B', subfunction)
		self.badsb = struct.pack('B', subfunction+1)
		self.client_function = client_function

	def assert_single_data_response(self, response):
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x20)

		self.assertEqual(len(dtc.extended_data), 1)
		extended_data = dtc.extended_data[0]

		self.assertTrue(isinstance(extended_data, Dtc.ExtendedData))
		self.assertEqual(extended_data.record_number, 0x99)	

		self.assertEqual(extended_data.raw_data, b'\x01\x02\x03\x04\x05')

	def test_single_data(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b'\x19' + self.sb + b'\x12\x34\x56\x99')
		self.conn.fromuserqueue.put(b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03\x04\x05')

	def _test_single_data(self):
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, record_number=0x99, data_size=5)
		self.assert_single_data_response(response)

	def test_single_data_instance_param(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b'\x19' + self.sb + b'\x12\x34\x56\x99')
		self.conn.fromuserqueue.put(b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03\x04\x05')

	def _test_single_data_instance_param(self):
		response = getattr(self.udsclient, self.client_function).__call__(dtc=Dtc(0x123456), record_number=0x99, data_size=5)
		self.assert_single_data_response(response)

	def test_single_data_config_size(self):
		 self.wait_request_and_respond(b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03\x04\x05')

	def _test_single_data_config_size(self):
		self.udsclient.config['extended_data_size'] = {0x123456 : 5}
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, record_number=0x99)
		self.assert_single_data_response(response)

	def test_single_data_zeropadding_ok(self):
		data = b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03\x04\x05'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_data_zeropadding_ok(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(8):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, record_number=0x99, data_size=5)
			self.assert_single_data_response(response)

	def test_single_data_zeropadding_notok_exception(self):
		data = b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03\x04\x05'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_data_zeropadding_notok_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			with self.assertRaises(InvalidResponseException):
				getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, record_number=0x99, data_size=5)

	def test_single_data_zeropadding_notok_no_exception(self):
		data = b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03\x04\x05'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_single_data_zeropadding_notok_no_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(8):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, record_number=0x99, data_size=5)
			self.assertFalse(response.valid)

	def test_double_data(self):
		 self.wait_request_and_respond(b'\x59'  + self.sb + b'\x12\x34\x56\x20\x10\x01\x02\x03\x11\x04\x05\x06')

	def _test_double_data(self):
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3)
		
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)

		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x20)

		self.assertEqual(len(dtc.extended_data), 2)

		self.assertTrue(isinstance(dtc.extended_data[0], Dtc.ExtendedData))
		self.assertEqual(dtc.extended_data[0].record_number, 0x10)	
		self.assertEqual(dtc.extended_data[0].raw_data, b'\x01\x02\x03')

		self.assertTrue(isinstance(dtc.extended_data[1], Dtc.ExtendedData))
		self.assertEqual(dtc.extended_data[1].record_number, 0x11)	
		self.assertEqual(dtc.extended_data[1].raw_data, b'\x04\x05\x06')


	def test_no_data(self):
		 self.wait_request_and_respond(b'\x59'  + self.sb + b'\x12\x34\x56\x20')

	def _test_no_data(self):
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3)
		
		self.assertEqual(len(response.service_data.dtcs), 1)
		self.assertEqual(response.service_data.dtc_count, 1)
		dtc = response.service_data.dtcs[0]

		self.assertEqual(dtc.id, 0x123456)
		self.assertEqual(dtc.status.get_byte_as_int(), 0x20)
		self.assertEqual(len(dtc.extended_data), 0)

	def test_no_data_zeropadding_ok(self):
		data = b'\x59'  + self.sb + b'\x12\x34\x56\x20'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1) )

	def _test_no_data_zeropadding_ok(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		for i in range(8):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3)
			
			self.assertEqual(len(response.service_data.dtcs), 1)
			self.assertEqual(response.service_data.dtc_count, 1)
			dtc = response.service_data.dtcs[0]

			self.assertEqual(dtc.id, 0x123456)
			self.assertEqual(dtc.status.get_byte_as_int(), 0x20)
			self.assertEqual(len(dtc.extended_data), 0)

	def test_no_data_zeropadding_not_ok_exception(self):
		data = b'\x59'  + self.sb + b'\x12\x34\x56\x20'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1) )

	def _test_no_data_zeropadding_not_ok_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(8):
			with self.assertRaises(InvalidResponseException):
				getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3)

	def test_no_data_zeropadding_not_ok_no_exception(self):
		data = b'\x59'  + self.sb + b'\x12\x34\x56\x20'
		for i in range(8):
			self.wait_request_and_respond(data + b'\x00' * (i+1) )

	def _test_no_data_zeropadding_not_ok_no_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(8):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3)
			self.assertFalse(response.valid)

	def invalid_length_no_response_server_task(self):
		 self.wait_request_and_respond(b'')
		 self.wait_request_and_respond(b'\x59')

	def test_invalid_length_no_response_exception(self):
		self.invalid_length_no_response_server_task()

	def _test_invalid_length_no_response_exception(self):
		for i in range(2):
			with self.assertRaises(InvalidResponseException):
				getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)

	def test_invalid_length_no_response_no_exception(self):
		self.invalid_length_no_response_server_task()

	def _test_invalid_length_no_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(2):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)
			self.assertFalse(response.valid)

	def invalid_length_incomplete_dtc_server_task(self):
		 self.wait_request_and_respond(b'\x59' + self.sb)
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12')
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34')
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34\x56')

	def test_invalid_length_incomplete_dtc_exception(self):
		self.invalid_length_incomplete_dtc_server_task()

	def _test_invalid_length_incomplete_dtc_exception(self):
		for i in range(4):
			with self.assertRaises(InvalidResponseException):
				getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)

	def test_invalid_length_incomplete_dtc_no_exception(self):
		self.invalid_length_incomplete_dtc_server_task()

	def _test_invalid_length_incomplete_dtc_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(4):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)
			self.assertFalse(response.valid)

	def invalid_length_missing_data_server_task(self):
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34\x56\x20\x99')
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34\x56\x20\x99\x01')
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34\x56\x20\x99\x01\x02')

	def test_invalid_length_missing_data_exception(self):
		self.invalid_length_missing_data_server_task()

	def _test_invalid_length_missing_data_exception(self):
		for i in range(3):
			with self.assertRaises(InvalidResponseException):
				getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)

	def test_invalid_length_missing_data_no_exception(self):
		self.invalid_length_missing_data_server_task()

	def _test_invalid_length_missing_data_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(3):
			response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)
			self.assertFalse(response.valid)

	def test_wrong_subfn_response_exception(self):
		 self.wait_request_and_respond(b'\x59' + self.badsb + b'\x12\x34\x56\x20\x99\x01\x02\x03')

	def _test_wrong_subfn_response_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)

	def test_wrong_subfn_response_no_exception(self):
		 self.wait_request_and_respond(b'\x59' + self.badsb + b'\x12\x34\x56\x20\x99\x01\x02\x03')

	def _test_wrong_subfn_response_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_wrong_record_number_response_exception(self):
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34\x56\x20\x98\x01\x02\x03')

	def _test_wrong_record_number_response_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)

	def test_wrong_record_number_response_no_exception(self):
		 self.wait_request_and_respond(b'\x59' + self.sb + b'\x12\x34\x56\x20\x98\x01\x02\x03')

	def _test_wrong_record_number_response_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_wrong_service_response_exception(self):
		 self.wait_request_and_respond(b'\x6F' + self.sb + b'\x12\x34\x56\x20\x98\x01\x02\x03')

	def _test_wrong_service_response_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)

	def test_wrong_service_response_no_exception(self):
		 self.wait_request_and_respond(b'\x6F' + self.sb + b'\x12\x34\x56\x20\x98\x01\x02\x03')

	def _test_wrong_service_response_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x99)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_oob_values(self):
		pass

	def _test_oob_values(self):
		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(dtc=-1, data_size=3, record_number=0x99)
		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x1000000, data_size=3, record_number=0x99)

		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=-1)

		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=3, record_number=0x100)

	def test_oob_values_data_size(self): # validation is made at interpret_response
		self.wait_request_and_respond(b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03')
		self.wait_request_and_respond(b'\x59'  + self.sb + b'\x12\x34\x56\x20\x99\x01\x02\x03')

	def _test_oob_values_data_size(self):
		with self.assertRaises(ValueError):
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, data_size=-1, record_number=0x99)

		with self.assertRaises(ValueError):
			self.udsclient.config['extended_data_size'] = {0x123456 : -1}
			getattr(self.udsclient, self.client_function).__call__(dtc=0x123456, record_number=0x99)

class TestReportDTCExtendedDataRecordByDTCNumber(ClientServerTest, GenericReportExtendedDataByRecordNumber):	# Subfn = 0x6
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericReportExtendedDataByRecordNumber.__init__(self, subfunction=0x06, client_function = 'get_dtc_extended_data_by_dtc_number')

class TestReportNumberOfDTCBySeverityMaskRecord(ClientServerTest):	# Subfn = 0x7
	
	def test_normal_behaviour_param_int(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x07\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x07\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_int(self):
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(response.service_data.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.service_data.dtc_count, 0x1234)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x07\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x07\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_instance(self):
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = Dtc.Status(test_failed=True), severity_mask=Dtc.Severity(check_immediately=True, check_at_next_exit=True))
		self.assertEqual(response.service_data.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.service_data.dtc_count, 0x1234)

	def test_normal_behaviour_harmless_extra_byte(self):
		self.wait_request_and_respond(b"\x59\x07\xFB\x01\x12\x34\x00\x11\x22")

	def _test_normal_behaviour_harmless_extra_byte(self):
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(response.service_data.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.service_data.dtc_count, 0x1234)		

	def test_bad_response_subfn_exception(self):
		self.wait_request_and_respond(b"\x59\x08\xFB\x01\x12\x34")

	def _test_bad_response_subfn_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
	
	def test_bad_response_subfn_no_exception(self):
		self.wait_request_and_respond(b"\x59\x08\xFB\x01\x12\x34")

	def _test_bad_response_subfn_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b"\x6F\x07\xFB\x01\x12\x34")

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b"\x6F\x07\xFB\x01\x12\x34")

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def bad_length_response_server_task(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59\x07")
		self.wait_request_and_respond(b"\x59\x07\xFB")
		self.wait_request_and_respond(b"\x59\x07\xFB\x01")
		self.wait_request_and_respond(b"\x59\x07\xFB\x01\x12")
	
	def test_bad_length_response_exception(self):
		self.bad_length_response_server_task()

	def _test_bad_length_response_exception(self):
		for i in range(5):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

	def test_bad_length_response_no_exception(self):
		self.bad_length_response_server_task()

	def _test_bad_length_response_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(5):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
			self.assertFalse(response.valid)

	def test_oob_value(self):
		pass

	def _test_oob_value(self):
		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x100, severity_mask=0xC0)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = -1, severity_mask=0xC0)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 'a', severity_mask=0xC0)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0x100)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=-1)

		with self.assertRaises(ValueError):
			self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask='a')

class TestReportDTCBySeverityMaskRecord(ClientServerTest):	# Subfn = 0x8

	def client_assert_response(self, response, expect_all_zero_third_dtc=False):
		self.assertEqual(response.service_data.status_availability.get_byte_as_int(), 0xFB)
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.service_data.dtcs), number_of_dtc)
		self.assertEqual(response.service_data.dtc_count, number_of_dtc)

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.service_data.dtcs[0].severity.get_byte_as_int(), 0x80)
		self.assertEqual(response.service_data.dtcs[0].functional_unit, 0x99)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123457)
		self.assertEqual(response.service_data.dtcs[1].status.get_byte_as_int(), 0x60)
		self.assertEqual(response.service_data.dtcs[1].severity.get_byte_as_int(), 0x40)
		self.assertEqual(response.service_data.dtcs[1].functional_unit, 0x88)
		
		if expect_all_zero_third_dtc:
			self.assertEqual(response.service_data.dtcs[2].id, 0)
			self.assertEqual(response.service_data.dtcs[2].status.get_byte_as_int(), 0x00)
			self.assertEqual(response.service_data.dtcs[2].severity.get_byte_as_int(), 0x00)
			self.assertEqual(response.service_data.dtcs[2].functional_unit, 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x08\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60")	

	def _test_normal_behaviour(self):
		response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.client_assert_response(response)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x08\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60")	

	def _test_normal_behaviour_param_instance(self):
		self.udsclient.get_dtc_by_status_severity_mask(status_mask = Dtc.Status(test_failed=True), severity_mask=Dtc.Severity(check_immediately=True, check_at_next_exit=True))

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x56\x60')

	def _test_dtc_duplicate(self):
		response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(len(response.service_data.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.service_data.dtcs[0].severity.get_byte_as_int(), 0x80)
		self.assertEqual(response.service_data.dtcs[0].functional_unit, 0x99)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[1].status.get_byte_as_int(), 0x60)
		self.assertEqual(response.service_data.dtcs[1].severity.get_byte_as_int(), 0x40)
		self.assertEqual(response.service_data.dtcs[1].functional_unit, 0x88)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		data = b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60'
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		for i in range(7):
			response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
			self.client_assert_response(response, expect_all_zero_third_dtc=False)
		
	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		data = b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60'
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		expect_all_zero_third_dtc_values = [False, False,False,False,False,True,True ]
		for i in range(7):
			response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
			self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])
		
	def test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		data = b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60'
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		should_return_invalid = [True, True, True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, None, None, False, None]

		for i in range(7):
			if should_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
			else:
				response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])
	

	def test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		data = b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60'
		for i in range(7):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
		
	def _test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		should_return_invalid = [True, True, True, True, True, False, True]
		expect_all_zero_third_dtc_values = [None, None, None, None, None, True, None]

		for i in range(7):
			if should_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
			else:
				response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_no_dtc(self):
		self.wait_request_and_respond(b'\x59\x08\xFB')

	def _test_no_dtc(self):
		response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(len(response.service_data.dtcs), 0)

	def test_bad_response_subfunction(self):
		self.wait_request_and_respond(b'\x59\x09\xFB')	

	def _test_bad_response_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

	def test_bad_response_service(self):
		self.wait_request_and_respond(b'\x6F\x08\xFB')	

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)			

	def test_bad_response_length(self):
		self.wait_request_and_respond(b'\x59')
		self.wait_request_and_respond(b'\x59\x08')	

	def _test_bad_response_length(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

	def test_oob_value(self):
		pass

	def _test_oob_value(self):
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x100, severity_mask=0xC0)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = -1, severity_mask=0xC0)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 'aaa', severity_mask=0xC0)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0x100)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=-1)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask='aaa')

# Only one DTC must be returned
class TestReportSeverityInformationOfDTC(ClientServerTest):	# Subfn = 0x9

	def client_assert_response(self, response):
		self.assertEqual(response.service_data.status_availability.get_byte_as_int(), 0xFB)
		number_of_dtc = 1
		
		self.assertEqual(len(response.service_data.dtcs), number_of_dtc)
		self.assertEqual(response.service_data.dtc_count, number_of_dtc)

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.service_data.dtcs[0].severity.get_byte_as_int(), 0x80)
		self.assertEqual(response.service_data.dtcs[0].functional_unit, 0x99)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x09\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20")	

	def _test_normal_behaviour(self):
		response = self.udsclient.get_dtc_severity(0x123456)
		self.client_assert_response(response)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x09\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20")	

	def _test_normal_behaviour_param_instance(self):
		self.udsclient.get_dtc_severity(Dtc(0x123456))

	def test_normal_behaviour_zeropadding_no_effect(self):
		data = b'\x59\x09\xFB\x80\x99\x12\x34\x56\x20'
		for i in range(5):
			self.wait_request_and_respond(data + b"\x00" * (i+1))
		
	def _test_normal_behaviour_zeropadding_no_effect(self):
		for i in range(5):
			response = self.udsclient.get_dtc_severity(0x123456)
			self.client_assert_response(response)
		
	def test_normal_behaviour_extrabytes_no_effect(self):
		data = b'\x59\x09\xFB\x80\x99\x12\x34\x56\x20'
		extra_bytes = b'\x12\x34\x56\x78\x9a'

		for i in range(5):
			self.wait_request_and_respond(data + extra_bytes[:i])
		
	def _test_normal_behaviour_extrabytes_no_effect(self):
		for i in range(5):
			response = self.udsclient.get_dtc_severity(0x123456)
			self.client_assert_response(response)
		
	def test_no_dtc(self):
		self.wait_request_and_respond(b'\x59\x09\xFB')

	def _test_no_dtc(self):
		response = self.udsclient.get_dtc_severity(0x123456)
		self.assertEqual(len(response.service_data.dtcs), 0)

	def test_bad_response_subfunction_exception(self):
		self.wait_request_and_respond(b'\x59\x0A\xFB')	

	def _test_bad_response_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_severity(0x123456)

	def test_bad_response_subfunction_no_exception(self):
		self.wait_request_and_respond(b'\x59\x0A\xFB')	

	def _test_bad_response_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_severity(0x123456)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b'\x6F\x09\xFB')	

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_severity(0x123456)

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b'\x6F\x09\xFB')	

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.get_dtc_severity(0x123456)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)	

	def bad_response_length_server_task(self):
		self.wait_request_and_respond(b'\x59')
		self.wait_request_and_respond(b'\x59\x09')
		# 5909FB is valid
		self.wait_request_and_respond(b'\x59\x09\xFB\x80')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99\x12')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99\x12\x34')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99\x12\x34\x56')

	def test_bad_response_length_exception(self):
		self.bad_response_length_server_task()
		
	def _test_bad_response_length_exception(self):
		for i in range(7):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_severity(0x123456)
	def test_bad_response_length_no_exception(self):
		self.bad_response_length_server_task()
		
	def _test_bad_response_length_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(7):
			response = self.udsclient.get_dtc_severity(0x123456)
			self.assertFalse(response.valid)

	def test_oob_value(self):
		pass

	def _test_oob_value(self):
		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_severity(-1)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_severity(0x1000000)

		with self.assertRaises(ValueError):
			self.udsclient.get_dtc_severity('a')

		with self.assertRaises(TypeError):
			self.udsclient.get_dtc_severity()

class GenericTestNoParamRequest_DtcAndStatusMaskResponse():
	def __init__(self, subfunction, client_function):
		self.sb = struct.pack('B', subfunction)
		self.badsb = struct.pack('B', subfunction+1)
		self.client_function = client_function

	def do_client_request(self):
		return getattr(self.udsclient, self.client_function).__call__()
	
	def client_assert_response(self, response, expect_all_zero_fourth_dtc=False):
		self.assertEqual(response.service_data.status_availability.get_byte_as_int(), 0x7F)
		number_of_dtc = 4 if expect_all_zero_fourth_dtc else 3
		
		self.assertEqual(len(response.service_data.dtcs), number_of_dtc)
		self.assertEqual(response.service_data.dtc_count, number_of_dtc)

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x24)
		self.assertEqual(response.service_data.dtcs[0].severity.get_byte_as_int(), 0x00)

		self.assertEqual(response.service_data.dtcs[1].id, 0x234505)
		self.assertEqual(response.service_data.dtcs[1].status.get_byte_as_int(), 0x00)
		self.assertEqual(response.service_data.dtcs[1].severity.get_byte_as_int(), 0x00)


		self.assertEqual(response.service_data.dtcs[2].id, 0xabcd01)
		self.assertEqual(response.service_data.dtcs[2].status.get_byte_as_int(), 0x2F)
		self.assertEqual(response.service_data.dtcs[2].severity.get_byte_as_int(), 0x00)		

		if expect_all_zero_fourth_dtc:
			self.assertEqual(response.service_data.dtcs[3].id, 0)
			self.assertEqual(response.service_data.dtcs[3].status.get_byte_as_int(), 0x00)
			self.assertEqual(response.service_data.dtcs[3].severity.get_byte_as_int(), 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb)
		self.conn.fromuserqueue.put(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F')	

	def _test_normal_behaviour(self):
		self.client_assert_response(self.do_client_request())

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x12\x34\x56\x25')

	def _test_dtc_duplicate(self):
		response = self.do_client_request()
		self.assertEqual(len(response.service_data.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].status.get_byte_as_int(), 0x24)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[1].status.get_byte_as_int(), 0x25)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		data = b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F'

		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		for i in range(5):
			self.client_assert_response(self.do_client_request(), expect_all_zero_fourth_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		data = b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		expect_all_zero_fourth_dtc_values = [False, False, False, True, True]
		for i in range(5):
			self.client_assert_response(self.do_client_request(), expect_all_zero_fourth_dtc=expect_all_zero_fourth_dtc_values[i])

	def normal_behaviour_zeropadding_notok_ignore_allzero_server_task(self):
		data = b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		self.normal_behaviour_zeropadding_notok_ignore_allzero_server_task()

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, False, None]

		for i in range(5):
			if must_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.do_client_request()
			else:
				self.client_assert_response(self.do_client_request(), expect_all_zero_fourth_dtc=expect_all_zero_fourth_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		self.normal_behaviour_zeropadding_notok_ignore_allzero_server_task()

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, False, None]

		for i in range(5):
			response = self.do_client_request()
			if must_return_invalid[i]:
				self.assertFalse(response.valid)
			else:
				self.client_assert_response(response, expect_all_zero_fourth_dtc=expect_all_zero_fourth_dtc_values[i])			

	def normal_behaviour_zeropadding_notok_consider_allzero_server_task(self):
		data = b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		self.normal_behaviour_zeropadding_notok_consider_allzero_server_task()

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, True, None]

		for i in range(5):
			if must_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.do_client_request()
			else:
				response = self.do_client_request()
				self.client_assert_response(response, expect_all_zero_fourth_dtc=expect_all_zero_fourth_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		self.normal_behaviour_zeropadding_notok_consider_allzero_server_task()

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, True, None]

		for i in range(5):
			response = self.do_client_request()
			if must_return_invalid[i]:
				self.assertFalse(response.valid)
			else:
				self.client_assert_response(response, expect_all_zero_fourth_dtc=expect_all_zero_fourth_dtc_values[i])				

	def test_no_dtc(self):
		self.wait_request_and_respond(b"\x59"+self.sb+b"\x7F")	

	def _test_no_dtc(self):
		response = self.do_client_request()
		self.assertEqual(len(response.service_data.dtcs), 0)
		self.assertEqual(response.service_data.dtc_count, 0)

	def test_bad_response_subfunction_exception(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\x7F")

	def _test_bad_response_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.do_client_request()

	def test_bad_response_subfunction_no_exception(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\x7F")

	def _test_bad_response_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.do_client_request()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\x7F")

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.do_client_request()	

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\x7F")

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.do_client_request()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)					

	def test_bad_response_length_exception(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)	

	def _test_bad_response_length_exception(self):
		for i in range(2):
			with self.assertRaises(InvalidResponseException):
				self.do_client_request()

	def test_bad_response_length_no_exception(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)	

	def _test_bad_response_length_no_exception(self):
		for i in range(2):
			self.udsclient.config['exception_on_invalid_response'] = False
			response = self.do_client_request()
			self.assertFalse(response.valid)

class TestReportSupportedDTC(ClientServerTest, GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn =- 0xA
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0xA, client_function = 'get_supported_dtc')

class TestReportFirstTestFailedDTC(ClientServerTest, GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn = 0xB
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0xB, client_function = 'get_first_test_failed_dtc')

class TestReportFirstConfirmedDTC(ClientServerTest, GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn = 0xC
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0xC, client_function = 'get_first_confirmed_dtc')

class TestReportMostRecentTestFailedDTC(ClientServerTest, GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn = 0xD
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0xD, client_function = 'get_most_recent_test_failed_dtc')

class TestReportMostRecentConfirmedDTC(ClientServerTest, GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn = 0xE
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0xE, client_function = 'get_most_recent_confirmed_dtc')

class TestReportMirrorMemoryDTCByStatusMask(ClientServerTest, GenericTestStatusMaskRequest_DtcAndStatusMaskResponse):	# Subfn = 0xF
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestStatusMaskRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0xf, client_function = 'get_mirrormemory_dtc_by_status_mask')
		
class TestReportMirrorMemoryDTCExtendedDataRecordByDTCNumber(ClientServerTest, GenericReportExtendedDataByRecordNumber):	# Subfn = 0x10
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericReportExtendedDataByRecordNumber.__init__(self, subfunction=0x10, client_function = 'get_mirrormemory_dtc_extended_data_by_dtc_number')

class TestReportNumberOfMirrorMemoryDTCByStatusMask(ClientServerTest, GenericTest_RequestStatusMask_ResponseNumberOfDTC):	# Subfn = 0x11
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestStatusMaskRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x11, client_function = 'get_mirrormemory_number_of_dtc_by_status_mask')

class TestReportNumberOfEmissionsRelatedOBDDTCByStatusMask(ClientServerTest, GenericTest_RequestStatusMask_ResponseNumberOfDTC):	# Subfn = 0x12
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestStatusMaskRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x12, client_function = 'get_number_of_emission_dtc_by_status_mask')

class TestReportEmissionsRelatedOBDDTCByStatusMask(ClientServerTest, GenericTestStatusMaskRequest_DtcAndStatusMaskResponse):	# Subfn = 0x13
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestStatusMaskRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x13, client_function = 'get_emission_dtc_by_status_mask')

class TestReportDTCFaultDetectionCounter(ClientServerTest):	# Subfn = 0x14
	
	def do_client_request(self):
		return self.udsclient.get_dtc_fault_counter()

	def client_assert_response(self, response, expect_all_zero_third_dtc=False):
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.service_data.dtcs), number_of_dtc)
		self.assertEqual(response.service_data.dtc_count, number_of_dtc)

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].fault_counter, 0x01)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123457)
		self.assertEqual(response.service_data.dtcs[1].fault_counter, 0x7E)

		if expect_all_zero_third_dtc:
			self.assertEqual(response.service_data.dtcs[2].id, 0)
			self.assertEqual(response.service_data.dtcs[2].fault_counter, 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x14")
		self.conn.fromuserqueue.put(b"\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E")

	def _test_normal_behaviour(self):
		self.client_assert_response(self.do_client_request())

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x56\x7E')

	def _test_dtc_duplicate(self):
		response = self.udsclient.get_dtc_fault_counter()
		self.assertEqual(len(response.service_data.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.service_data.dtcs[0].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[0].fault_counter, 0x01)

		self.assertEqual(response.service_data.dtcs[1].id, 0x123456)
		self.assertEqual(response.service_data.dtcs[1].fault_counter, 0x7E)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		data = b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		for i in range(5):
			self.client_assert_response(self.do_client_request(), expect_all_zero_third_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		data = b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		expect_all_zero_third_dtc_values = [False, False, False, True, True]
		for i in range(5):
			self.client_assert_response(self.do_client_request(), expect_all_zero_third_dtc=expect_all_zero_third_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		data = b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, False, None]

		for i in range(5):
			if must_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.do_client_request()
			else:
				self.client_assert_response(self.do_client_request(), expect_all_zero_third_dtc=expect_all_zero_fourth_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		data = b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True

		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, False, None]

		for i in range(5):
			response = self.do_client_request()
			if must_return_invalid[i]:
				self.assertFalse(response.valid)					
			else:
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_fourth_dtc_values[i])				

	def test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		data = b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, True, None]

		for i in range(5):
			if must_return_invalid[i]:
				with self.assertRaises(InvalidResponseException):
					self.do_client_request()
			else:
				self.client_assert_response(self.do_client_request(), expect_all_zero_third_dtc=expect_all_zero_fourth_dtc_values[i])

	def test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		data = b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E'
		for i in range(5):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_normal_behaviour_zeropadding_notok_consider_allzero_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		
		must_return_invalid = [True, True, True, False, True]
		expect_all_zero_fourth_dtc_values = [None, None, None, True, None]

		for i in range(5):
			response = self.do_client_request()
			if must_return_invalid[i]:
				self.assertFalse(response.valid)					
			else:
				self.client_assert_response(response, expect_all_zero_third_dtc=expect_all_zero_fourth_dtc_values[i])				

	def test_no_dtc(self):
		self.wait_request_and_respond(b"\x59\x14")	

	def _test_no_dtc(self):
		response = self.do_client_request()
		self.assertEqual(len(response.service_data.dtcs), 0)
		self.assertEqual(response.service_data.dtc_count, 0)

	def test_bad_response_subfunction_exception(self):
		self.wait_request_and_respond(b"\x59\x15")	

	def _test_bad_response_subfunction_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.do_client_request()

	def test_bad_response_subfunction_no_exception(self):
		self.wait_request_and_respond(b"\x59\x15")	

	def _test_bad_response_subfunction_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.do_client_request()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)	

	def test_bad_response_service_exception(self):
		self.wait_request_and_respond(b"\x6F\x14")	

	def _test_bad_response_service_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.do_client_request()	

	def test_bad_response_service_no_exception(self):
		self.wait_request_and_respond(b"\x6F\x14")	

	def _test_bad_response_service_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.do_client_request()
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)	

	def bad_response_length_server_task(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59\x14\x12")
		self.wait_request_and_respond(b"\x59\x14\x12\x34")
		self.wait_request_and_respond(b"\x59\x14\x12\x34\x56")
		self.wait_request_and_respond(b"\x59\x14\x12\x34\x56\x01\x12")

	def test_bad_response_length_exception(self):
		self.bad_response_length_server_task()

	def _test_bad_response_length_exception(self):
		for i in range(5):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_fault_counter()

	def test_bad_response_length_no_exception(self):
		self.bad_response_length_server_task()

	def _test_bad_response_length_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		for i in range(5):
			response = self.do_client_request()
			self.assertFalse(response.valid)

class TestReportDTCWithPermanentStatus(ClientServerTest,GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn = 0x15
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x15, client_function = 'get_dtc_with_permanent_status')

