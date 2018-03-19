from udsoncan.client import Client
from udsoncan import services
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
		self.assertEqual(response.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.dtc_count, 0x1234)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_instance(self):
		response = getattr(self.udsclient, self.client_function).__call__(Dtc.Status(test_failed_this_operation_cycle = True, confirmed = True, test_not_completed_since_last_clear = True, test_not_completed_this_operation_cycle = True))
		self.assertEqual(response.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.dtc_count, 0x1234)

	def test_normal_behaviour_harmless_extra_byte(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x01\x12\x34\x00\x11\x22")

	def _test_normal_behaviour_harmless_extra_byte(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(response.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.dtc_count, 0x1234)		

	def test_bad_response_subfn(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59"+self.badsb+b"\xFB\x01\x12\x34")

	def _test_bad_response_subfn(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

	def test_bad_response_service(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x6F"+self.sb+b"\xFB\x01\x12\x34")

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)			


	def test_bad_length_response(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB")
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01")
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x01\x12")

	def _test_bad_length_response(self):
		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

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


	def do_client_fixed_dtc(self, expect_all_zero_third_dtc=False):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(response.status_availability, 0xFB)
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.dtcs), number_of_dtc)
		self.assertEqual(response.dtc_count, number_of_dtc)

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.dtcs[0].severity.get_byte_as_int(), 0x00)

		self.assertEqual(response.dtcs[1].id, 0x123457)
		self.assertEqual(response.dtcs[1].status.get_byte_as_int(), 0x60)
		self.assertEqual(response.dtcs[1].severity.get_byte_as_int(), 0x00)
		
		if expect_all_zero_third_dtc:
			self.assertEqual(response.dtcs[2].id, 0)
			self.assertEqual(response.dtcs[2].status.get_byte_as_int(), 0x00)
			self.assertEqual(response.dtcs[2].severity.get_byte_as_int(), 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x12\x34\x56\x20\x12\x34\x57\x60")	

	def _test_normal_behaviour(self):
		self.do_client_fixed_dtc()

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b"\x59"+self.sb+b"\xFB\x12\x34\x56\x20\x12\x34\x56\x60")

	def _test_dtc_duplicate(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(len(response.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x20)

		self.assertEqual(response.dtcs[1].id, 0x123456)
		self.assertEqual(response.dtcs[1].status.get_byte_as_int(), 0x60)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb+b"\x5A")
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB\x12\x34\x56\x20\x12\x34\x57\x60")	

	def _test_normal_behaviour_param_instance(self):
		getattr(self.udsclient, self.client_function).__call__(Dtc.Status(test_failed_this_operation_cycle = True, confirmed = True, test_not_completed_since_last_clear = True, test_not_completed_this_operation_cycle = True))

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00\x00')
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

	def test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\xFB\x12\x34\x56\x20\x12\x34\x57\x60\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_no_dtc(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59"+self.sb+b"\xFB")	

	def _test_no_dtc(self):
		response = getattr(self.udsclient, self.client_function).__call__(0x5A)
		self.assertEqual(len(response.dtcs), 0)

	def test_bad_response_subfunction(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59"+self.badsb+b"\xFB")	

	def _test_bad_response_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

	def test_bad_response_service(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x6F"+self.sb+b"\xFB")	

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)			

	def test_bad_response_length(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59")

		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59"+self.sb)	

	def _test_bad_response_length(self):
		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__(0x5A)

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
	def do_client_fixed_dtc(self, expect_all_zero_third_dtc=False):
		response = self.udsclient.get_dtc_snapshot_identification()
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.dtcs), number_of_dtc)
		self.assertEqual(response.dtc_count, number_of_dtc)

		self.assertEqual(response.dtcs[0].id, 0x123456)		
		self.assertEqual(len(response.dtcs[0].snapshots), 2)
		self.assertEqual(response.dtcs[0].snapshots[0], 1)
		self.assertEqual(response.dtcs[0].snapshots[1], 2)

		self.assertEqual(response.dtcs[1].id, 0x789abc)		
		self.assertEqual(len(response.dtcs[1].snapshots), 1)
		self.assertEqual(response.dtcs[1].snapshots[0], 3)
		
		if expect_all_zero_third_dtc:
			self.assertEqual(response.dtcs[2].id, 0)		
			self.assertEqual(len(response.dtcs[2].snapshots), 1)
			self.assertEqual(response.dtcs[2].snapshots[0], 0)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x03")
		self.conn.fromuserqueue.put(b"\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03")	

	def _test_normal_behaviour(self):
		self.do_client_fixed_dtc()

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00\x00')
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

	def test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12\x34\x56\x02\x78\x9a\xbc\x03\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_no_dtc(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59\x03")	

	def _test_no_dtc(self):
		response = response = self.udsclient.get_dtc_snapshot_identification()
		self.assertEqual(len(response.dtcs), 0)

	def test_bad_response_subfunction(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59\x04")	

	def _test_bad_response_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			response = self.udsclient.get_dtc_snapshot_identification()

	def test_bad_response_service(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x6F\x03")	

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			response = self.udsclient.get_dtc_snapshot_identification()

	def test_bad_response_length(self):
		self.wait_request_and_respond(b'\x59')	
		self.wait_request_and_respond(b'\x59\x03\x12')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56')	
		self.wait_request_and_respond(b'\x59\x03\x12\x34\x56\x01\x12')	

	def _test_bad_response_length(self):
		for i in range(5):
			with self.assertRaises(InvalidResponseException):
				response = self.udsclient.get_dtc_snapshot_identification()

class TestReportDTCSnapshotRecordByDTCNumber(ClientServerTest):	# Subfn = 0x4
	pass

class TestReportDTCSnapshotRecordByRecordNumber(ClientServerTest):	# Subfn = 0x5
	pass

class TestReportDTCExtendedDataRecordByDTCNumber(ClientServerTest):	# Subfn = 0x6
	pass

class TestReportNumberOfDTCBySeverityMaskRecord(ClientServerTest):	# Subfn = 0x7
	
	def test_normal_behaviour_param_int(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x07\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x07\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_int(self):
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(response.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.dtc_count, 0x1234)

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x07\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x07\xFB\x01\x12\x34")

	def _test_normal_behaviour_param_instance(self):
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = Dtc.Status(test_failed=True), severity_mask=Dtc.Severity(check_immediately=True, check_at_next_exit=True))
		self.assertEqual(response.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.dtc_count, 0x1234)

	def test_normal_behaviour_harmless_extra_byte(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59\x07\xFB\x01\x12\x34\x00\x11\x22")

	def _test_normal_behaviour_harmless_extra_byte(self):
		response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(response.dtc_format, Dtc.Format.ISO14229_1)
		self.assertEqual(response.dtc_count, 0x1234)		

	def test_bad_response_subfn(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x59\x08\xFB\x01\x12\x34")

	def _test_bad_response_subfn(self):
		with self.assertRaises(UnexpectedResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

	def test_bad_response_service(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x6F\x07\xFB\x01\x12\x34")

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)


	def test_bad_length_response(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59\x07")
		self.wait_request_and_respond(b"\x59\x07\xFB")
		self.wait_request_and_respond(b"\x59\x07\xFB\x01")
		self.wait_request_and_respond(b"\x59\x07\xFB\x01\x12")

	def _test_bad_length_response(self):
		with self.assertRaises(InvalidResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

		with self.assertRaises(InvalidResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

		with self.assertRaises(InvalidResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

		with self.assertRaises(InvalidResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

		with self.assertRaises(InvalidResponseException):
			response = self.udsclient.get_number_of_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)

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

	def do_client_fixed_dtc(self, expect_all_zero_third_dtc=False):
		response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(response.status_availability, 0xFB)
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.dtcs), number_of_dtc)
		self.assertEqual(response.dtc_count, number_of_dtc)

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.dtcs[0].severity.get_byte_as_int(), 0x80)
		self.assertEqual(response.dtcs[0].functional_unit, 0x99)

		self.assertEqual(response.dtcs[1].id, 0x123457)
		self.assertEqual(response.dtcs[1].status.get_byte_as_int(), 0x60)
		self.assertEqual(response.dtcs[1].severity.get_byte_as_int(), 0x40)
		self.assertEqual(response.dtcs[1].functional_unit, 0x88)
		
		if expect_all_zero_third_dtc:
			self.assertEqual(response.dtcs[2].id, 0)
			self.assertEqual(response.dtcs[2].status.get_byte_as_int(), 0x00)
			self.assertEqual(response.dtcs[2].severity.get_byte_as_int(), 0x00)
			self.assertEqual(response.dtcs[2].functional_unit, 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x08\xC0\x01")
		self.conn.fromuserqueue.put(b"\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60")	

	def _test_normal_behaviour(self):
		self.do_client_fixed_dtc()

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
		self.assertEqual(len(response.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.dtcs[0].severity.get_byte_as_int(), 0x80)
		self.assertEqual(response.dtcs[0].functional_unit, 0x99)

		self.assertEqual(response.dtcs[1].id, 0x123456)
		self.assertEqual(response.dtcs[1].status.get_byte_as_int(), 0x60)
		self.assertEqual(response.dtcs[1].severity.get_byte_as_int(), 0x40)
		self.assertEqual(response.dtcs[1].functional_unit, 0x88)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00')
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

	def test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x08\xFB\x80\x99\x12\x34\x56\x20\x40\x88\x12\x34\x57\x60\x00\x00\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_no_dtc(self):
		self.wait_request_and_respond(b'\x59\x08\xFB')

	def _test_no_dtc(self):
		response = self.udsclient.get_dtc_by_status_severity_mask(status_mask = 0x01, severity_mask=0xC0)
		self.assertEqual(len(response.dtcs), 0)

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

	def do_client_fixed_dtc(self):
		response = self.udsclient.get_dtc_severity(0x123456)
		self.assertEqual(response.status_availability, 0xFB)
		number_of_dtc = 1
		
		self.assertEqual(len(response.dtcs), number_of_dtc)
		self.assertEqual(response.dtc_count, number_of_dtc)

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x20)
		self.assertEqual(response.dtcs[0].severity.get_byte_as_int(), 0x80)
		self.assertEqual(response.dtcs[0].functional_unit, 0x99)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x09\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20")	

	def _test_normal_behaviour(self):
		self.do_client_fixed_dtc()

	def test_normal_behaviour_param_instance(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x09\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20")	

	def _test_normal_behaviour_param_instance(self):
		self.udsclient.get_dtc_severity(Dtc(0x123456))

	def test_normal_behaviour_zeropadding_no_effect(self):
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x00")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x00\x00")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x00\x00\x00")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x00\x00\x00\x00")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x00\x00\x00\x00\x00")
		
	def _test_normal_behaviour_zeropadding_no_effect(self):
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()

	def test_normal_behaviour_extrabytes_no_effect(self):
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x12")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x12\x34")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x12\x34\x56")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x12\x34\x56\x78")
		self.wait_request_and_respond(b"\x59\x09\xFB\x80\x99\x12\x34\x56\x20\x12\x34\x56\x78\x9a")
		
	def _test_normal_behaviour_extrabytes_no_effect(self):
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()
		self.do_client_fixed_dtc()		

	def test_no_dtc(self):
		self.wait_request_and_respond(b'\x59\x09\xFB')

	def _test_no_dtc(self):
		response = self.udsclient.get_dtc_severity(0x123456)
		self.assertEqual(len(response.dtcs), 0)

	def test_bad_response_subfunction(self):
		self.wait_request_and_respond(b'\x59\x0A\xFB')	

	def _test_bad_response_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_severity(0x123456)

	def test_bad_response_service(self):
		self.wait_request_and_respond(b'\x6F\x09\xFB')	

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_severity(0x123456)			

	def test_bad_response_length(self):
		self.wait_request_and_respond(b'\x59')
		self.wait_request_and_respond(b'\x59\x09')
		# 5909FB is valid
		self.wait_request_and_respond(b'\x59\x09\xFB\x80')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99\x12')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99\x12\x34')
		self.wait_request_and_respond(b'\x59\x09\xFB\x80\x99\x12\x34\x56')

	def _test_bad_response_length(self):
		for i in range(7):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.get_dtc_severity(0x123456)

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
	
	def do_client_fixed_dtc(self, expect_all_zero_fourth_dtc=False):
		response = getattr(self.udsclient, self.client_function).__call__()
		self.assertEqual(response.status_availability, 0x7F)
		number_of_dtc = 4 if expect_all_zero_fourth_dtc else 3
		
		self.assertEqual(len(response.dtcs), number_of_dtc)
		self.assertEqual(response.dtc_count, number_of_dtc)

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x24)
		self.assertEqual(response.dtcs[0].severity.get_byte_as_int(), 0x00)

		self.assertEqual(response.dtcs[1].id, 0x234505)
		self.assertEqual(response.dtcs[1].status.get_byte_as_int(), 0x00)
		self.assertEqual(response.dtcs[1].severity.get_byte_as_int(), 0x00)


		self.assertEqual(response.dtcs[2].id, 0xabcd01)
		self.assertEqual(response.dtcs[2].status.get_byte_as_int(), 0x2F)
		self.assertEqual(response.dtcs[2].severity.get_byte_as_int(), 0x00)		

		if expect_all_zero_fourth_dtc:
			self.assertEqual(response.dtcs[3].id, 0)
			self.assertEqual(response.dtcs[3].status.get_byte_as_int(), 0x00)
			self.assertEqual(response.dtcs[3].severity.get_byte_as_int(), 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19"+self.sb)
		self.conn.fromuserqueue.put(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F')	

	def _test_normal_behaviour(self):
		self.do_client_fixed_dtc()

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x12\x34\x56\x25')

	def _test_dtc_duplicate(self):
		response = getattr(self.udsclient, self.client_function).__call__()
		self.assertEqual(len(response.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte_as_int(), 0x24)

		self.assertEqual(response.dtcs[1].id, 0x123456)
		self.assertEqual(response.dtcs[1].status.get_byte_as_int(), 0x25)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00\x00')
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=True)
		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=True)	

	def test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=False)

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59'+self.sb+b'\x7F\x12\x34\x56\x24\x23\x45\x05\x00\xAB\xCD\x01\x2F\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_fourth_dtc=True)	

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_no_dtc(self):
		self.wait_request_and_respond(b"\x59"+self.sb+b"\x7F")	

	def _test_no_dtc(self):
		response = getattr(self.udsclient, self.client_function).__call__()
		self.assertEqual(len(response.dtcs), 0)
		self.assertEqual(response.dtc_count, 0)

	def test_bad_response_subfunction(self):
		self.wait_request_and_respond(b"\x59"+self.badsb+b"\x7F")	

	def _test_bad_response_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__()

	def test_bad_response_service(self):
		self.wait_request_and_respond(b"\x6F"+self.sb+b"\x7F")	

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			getattr(self.udsclient, self.client_function).__call__()		

	def test_bad_response_length(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59"+self.sb)	

	def _test_bad_response_length(self):
		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__()

		with self.assertRaises(InvalidResponseException):
			getattr(self.udsclient, self.client_function).__call__()

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
		

class TestReportMirrorMemoryDTCExtendedDataRecordByDTCNumber(ClientServerTest):	# Subfn = 0x10
	pass

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
	
	def do_client_fixed_dtc(self, expect_all_zero_third_dtc=False):
		response = self.udsclient.get_dtc_fault_counter()
		number_of_dtc = 3 if expect_all_zero_third_dtc else 2
		
		self.assertEqual(len(response.dtcs), number_of_dtc)
		self.assertEqual(response.dtc_count, number_of_dtc)

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].fault_counter, 0x01)

		self.assertEqual(response.dtcs[1].id, 0x123457)
		self.assertEqual(response.dtcs[1].fault_counter, 0x7E)

		if expect_all_zero_third_dtc:
			self.assertEqual(response.dtcs[2].id, 0)
			self.assertEqual(response.dtcs[2].fault_counter, 0x00)

	def test_normal_behaviour(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x19\x14")
		self.conn.fromuserqueue.put(b"\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E")

	def _test_normal_behaviour(self):
		self.do_client_fixed_dtc()

	def test_dtc_duplicate(self):
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x56\x7E')

	def _test_dtc_duplicate(self):
		response = self.udsclient.get_dtc_fault_counter()
		self.assertEqual(len(response.dtcs), 2)	# We want both of them. Server should avoid duplicate

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].fault_counter, 0x01)

		self.assertEqual(response.dtcs[1].id, 0x123456)
		self.assertEqual(response.dtcs[1].fault_counter, 0x7E)

	def test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_ok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = True
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

	def test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00\x00')
	
	def _test_normal_behaviour_zeropadding_ok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = True
		self.udsclient.config['ignore_all_zero_dtc'] = False
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)
		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

	def test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_ignore_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = True
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=False)

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00')
		self.wait_request_and_respond(b'\x59\x14\x12\x34\x56\x01\x12\x34\x57\x7E\x00\x00\x00\x00\x00')

	def _test_normal_behaviour_zeropadding_notok_consider_allzero(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		self.udsclient.config['ignore_all_zero_dtc'] = False
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()
		
		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()

		self.do_client_fixed_dtc(expect_all_zero_third_dtc=True)	

		with self.assertRaises(InvalidResponseException):
			self.do_client_fixed_dtc()	

	def test_no_dtc(self):
		self.wait_request_and_respond(b"\x59\x14")	

	def _test_no_dtc(self):
		response = self.udsclient.get_dtc_fault_counter()
		self.assertEqual(len(response.dtcs), 0)
		self.assertEqual(response.dtc_count, 0)

	def test_bad_response_subfunction(self):
		self.wait_request_and_respond(b"\x59\x15")	

	def _test_bad_response_subfunction(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_fault_counter()

	def test_bad_response_service(self):
		self.wait_request_and_respond(b"\x6F\x14")	

	def _test_bad_response_service(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.get_dtc_fault_counter()		

	def test_bad_response_length(self):
		self.wait_request_and_respond(b"\x59")
		self.wait_request_and_respond(b"\x59\x14\x12")
		self.wait_request_and_respond(b"\x59\x14\x12\x34")
		self.wait_request_and_respond(b"\x59\x14\x12\x34\x56")
		self.wait_request_and_respond(b"\x59\x14\x12\x34\x56\x01\x12")

	def _test_bad_response_length(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_fault_counter()

		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_fault_counter()
		
		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_fault_counter()

		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_fault_counter()

		with self.assertRaises(InvalidResponseException):
			self.udsclient.get_dtc_fault_counter()

class TestReportDTCWithPermanentStatus(ClientServerTest,GenericTestNoParamRequest_DtcAndStatusMaskResponse):	# Subfn = 0x15
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)
		GenericTestNoParamRequest_DtcAndStatusMaskResponse.__init__(self, subfunction=0x15, client_function = 'get_dtc_with_permanent_status')

