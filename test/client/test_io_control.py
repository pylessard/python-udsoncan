from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *
from udsoncan import DidCodec
from udsoncan import IOValues, IOMasks
import struct

from test.ClientServerTest import ClientServerTest

class StubbedCodec(DidCodec):
	def encode(self, did_value):
		return struct.pack('B', did_value+1)

	def decode(self, did_payload):
		return struct.unpack('B', did_payload)[0] - 1

	def __len__(self):
		return 1

class StubbedCompositeCodec(DidCodec):
	def encode(self, IAC_pintle, rpm, pedalA, pedalB, EGR_duty):
		pedal = (pedalA << 4) | pedalB
		return struct.pack('>BHBB', IAC_pintle, rpm, pedal, EGR_duty)

	def decode(self, payload):
		vals = struct.unpack('>BHBB', payload)
		return {
			'IAC_pintle': vals[0],
			'rpm' 		: vals[1],
			'pedalA' 	: (vals[2] >> 4) & 0xF,
			'pedalB' 	: vals[2] & 0xF,
			'EGR_duty' 	: vals[3]
		}

	def __len__(self):
		return 5		

class TestIOControl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def postClientSetUp(self):
		self.udsclient.config["input_output"] = {
			0x132 : StubbedCodec,
			0x456 : '<HH',
			0x155 : {
				'codec' : StubbedCompositeCodec,
				'mask' : {
					'IAC_pintle': 0x80,
					'rpm' 		: 0x40,
					'pedalA' 	: 0x20,
					'pedalB' 	: 0x10,
					'EGR_duty'	: 0x08
				},
				'mask_size' : 2
			}
		}

#As defined by ISO-14229:2006, section 12.2.5.2 (Example #1)
	def test_io_control_single_reset(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x32\x01")
		self.conn.fromuserqueue.put(b"\x6F\x01\x32\x01\x4B")	# Positive response

	def _test_io_control_single_reset(self):
		response = self.udsclient.io_control(control_param=1, did=0x132)	# Reset to default
		self.assertEqual(response.service_data.control_param_echo, 1)	
		self.assertEqual(response.service_data.did_echo, 0x132)	
		self.assertEqual(response.service_data.decoded_data, 0x4A)	# 0x4B-1 as defined by codec decode method

	def test_io_control_single_reset_spr_no_effect(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x32\x01")
		self.conn.fromuserqueue.put(b"\x6F\x01\x32\x01\x4B")	# Positive response

	def _test_io_control_single_reset_spr_no_effect(self):
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.io_control(control_param=1, did=0x132)	# Reset to default
			self.assertEqual(response.service_data.control_param_echo, 1)	
			self.assertEqual(response.service_data.did_echo, 0x132)	
			self.assertEqual(response.service_data.decoded_data, 0x4A)	# 0x4B-1 as defined by codec decode method

	def test_io_control_no_control_param(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x32\x78")
		self.conn.fromuserqueue.put(b"\x6F\x01\x32\x4B")

	def _test_io_control_no_control_param(self):
		response = self.udsclient.io_control(did=0x132, values=[0x77]) # No control_param, skip directly to data	
		self.assertEqual(response.service_data.control_param_echo, None)	
		self.assertEqual(response.service_data.did_echo, 0x132)	
		self.assertEqual(response.service_data.decoded_data, 0x4A)	# 0x4B-1 as defined by codec decode method

	def test_io_control_with_repsonse_record(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x04\x56\x03\x11\x01\x22\x02")
		self.conn.fromuserqueue.put(b"\x6F\x04\x56\x03\x33\x03\x44\x04")	# Positive response with 0x333 and 0x444 as response data

	def _test_io_control_with_repsonse_record(self):
		response = self.udsclient.io_control(control_param=3, did=0x456, values=IOValues(0x111,0x222))	# Short Term Adjustment
		self.assertEqual(response.service_data.decoded_data, (0x333, 0x444))	

	def test_io_control_with_repsonse_record_zero_padding_tolerated(self):
		data = b'\x6F\x04\x56\x03\x33\x03\x44\x04'

		for i in range(3):
			self.wait_request_and_respond(data + b'\x00' * (i+1))
		
	def _test_io_control_with_repsonse_record_zero_padding_tolerated(self):
		self.udsclient.config['tolerate_zero_padding'] = True

		for i in range(3):
			response = self.udsclient.io_control(control_param=3, did=0x456, values=IOValues(0x111,0x222))	
			self.assertEqual(response.service_data.control_param_echo, 3)
			self.assertEqual(response.service_data.did_echo, 0x456)
			self.assertEqual(response.service_data.decoded_data, (0x333, 0x444))

	def test_io_control_with_repsonse_record_zero_padding_not_tolerated_exception(self):
		data = b'\x6F\x04\x56\x03\x33\x03\x44\x04'
		for i in range(3):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_io_control_with_repsonse_record_zero_padding_not_tolerated_exception(self):
		self.udsclient.config['tolerate_zero_padding'] = False
		for i in range(3):
			with self.assertRaises(InvalidResponseException):
				self.udsclient.io_control(control_param=3, did=0x456, values=IOValues(0x111,0x222))	

	def test_io_control_with_repsonse_record_zero_padding_not_tolerated_no_exception(self):
		data = b'\x6F\x04\x56\x03\x33\x03\x44\x04'
		for i in range(3):
			self.wait_request_and_respond(data + b'\x00' * (i+1))

	def _test_io_control_with_repsonse_record_zero_padding_not_tolerated_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		self.udsclient.config['tolerate_zero_padding'] = False
		
		for i in range(3):
			response = self.udsclient.io_control(control_param=3, did=0x456, values=IOValues(0x111,0x222))	
			self.assertFalse(response.valid)

	def test_io_control_composite_did_dict(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x55\x03\x07\x12\x34\x45\x99\x00\xA0")
		self.conn.fromuserqueue.put(b"\x6F\x01\x55\x03\x07\x02\xEE\x12\x59")

	def _test_io_control_composite_did_dict(self):
		values = {'IAC_pintle': 0x07, 'rpm': 0x1234, 'pedalA': 0x4, 'pedalB' : 0x5,  'EGR_duty': 0x99}
		response = self.udsclient.io_control(control_param=3, did=0x155, values=values, masks=['IAC_pintle', 'pedalA'])	# Short Term Adjustment
		expected_values = {
			'IAC_pintle': 0x07,
			'rpm' 		: 0x2EE,
			'pedalA' 	: 0x1,
			'pedalB' 	: 0x2,
			'EGR_duty' 	: 0x59
		}
		self.assertEqual(response.service_data.did_echo, 0x155)	
		self.assertEqual(response.service_data.control_param_echo, 3)	
		self.assertEqual(response.service_data.decoded_data, expected_values)	

	def test_io_control_composite_did_list(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x55\x03\x07\x12\x34\x45\x99\x00\xA0")
		self.conn.fromuserqueue.put(b"\x6F\x01\x55\x03\x07\x02\xEE\x12\x59")	

	def _test_io_control_composite_did_list(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]
		response = self.udsclient.io_control(control_param=3, did=0x155, values=values, masks=['IAC_pintle', 'pedalA'])	# Short Term Adjustment
		expected_values = {
			'IAC_pintle': 0x07,
			'rpm' 		: 0x2EE,
			'pedalA' 	: 0x1,
			'pedalB' 	: 0x2,
			'EGR_duty' 	: 0x59
		}
		self.assertEqual(response.service_data.did_echo, 0x155)	
		self.assertEqual(response.service_data.control_param_echo, 3)	
		self.assertEqual(response.service_data.decoded_data, expected_values)	

	def test_io_control_non_existent_mask_error(self):
		pass

	def _test_io_control_non_existent_mask_error(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]
		with self.assertRaises(ConfigError):
			self.udsclient.io_control(control_param=3, did=0x155, values=values, masks=['xxxx'])	# mask xxxx does not exist in config
	
	def test_io_control_mask_all_set1(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x55\x03\x07\x12\x34\x45\x99\xFF\xFF")
		self.conn.fromuserqueue.put(b"\x6F\x01\x55\x03\x07\x02\xEE\x12\x59")	

	def _test_io_control_mask_all_set1(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]
		self.udsclient.io_control(control_param=3, did=0x155, values=values, masks=True)	# Short Term Adjustment

	def test_io_control_mask_all_set0(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x55\x03\x07\x12\x34\x45\x99\x00\x00")
		self.conn.fromuserqueue.put(b"\x6F\x01\x55\x03\x07\x02\xEE\x12\x59")	

	def _test_io_control_mask_all_set0(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]
		self.udsclient.io_control(control_param=3, did=0x155, values=values, masks=False)	# Short Term Adjustment

	def test_io_control_no_mask(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x2F\x01\x55\x03\x07\x12\x34\x45\x99")
		self.conn.fromuserqueue.put(b"\x6F\x01\x55\x03\x07\x02\xEE\x12\x59")	

	def _test_io_control_no_mask(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]
		self.udsclient.io_control(control_param=3, did=0x155, values=values)	# Short Term Adjustment


	def test_io_control_bad_mask_size(self):
		pass

	def _test_io_control_bad_mask_size(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]
		with self.assertRaises(ValueError):
			self.udsclient.config['input_output'][0x155]['mask_size'] = -1  # Bad value
			self.udsclient.io_control(control_param=3, did=0x155, values=values)	

		with self.assertRaises(ValueError):
			self.udsclient.config['input_output'][0x155]['mask_size'] = None   # Bad value
			self.udsclient.io_control(control_param=3, did=0x155, values=values) 

		with self.assertRaises(ConfigError):
			del self.udsclient.config['input_output'][0x155]['mask_size']
			self.udsclient.io_control(control_param=3, did=0x155, values=values, masks=True) # Set mask, no size defined

	def test_io_control_bad_mask(self):
		pass

	def _test_io_control_bad_mask(self):
		values = [0x07, 0x1234, 0x4, 0x5, 0x99]

		with self.assertRaises(ValueError):
			self.udsclient.config['input_output'][0x155]['mask']['pedalA'] = -1  # Bad value
			self.udsclient.io_control(control_param=3, did=0x155, values=values)	

		with self.assertRaises(ValueError):
			self.udsclient.config['input_output'][0x155]['mask']['pedalA'] = 0x10000  # Bigger than max_size (2)
			self.udsclient.io_control(control_param=3, did=0x155, values=values) 

	def test_io_control_bad_values(self):
		pass

	def _test_io_control_bad_values(self):
		with self.assertRaises(ValueError):
			self.udsclient.io_control(control_param=3, did=0x155, values=1)

		with self.assertRaises(ValueError):
			self.udsclient.io_control(control_param=3, did=0x155, values='asd') 

	def test_io_control_bad_control_param(self):
		pass

	def _test_io_control_bad_control_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.io_control(control_param=-1, did=0x155, values=1)

		with self.assertRaises(ValueError):
			self.udsclient.io_control(control_param=0x100, did=0x155, values='asd') 

	def test_io_control_bad_response_too_much_data_exception(self):
		self.wait_request_and_respond(b"\x6F\x01\x32\x01\x4B\xAA")	# Last byte is extra

	def _test_io_control_bad_response_too_much_data_exception(self):
		with self.assertRaises(InvalidResponseException):
			self.udsclient.io_control(control_param=1, did=0x132)	

	def test_io_control_bad_response_too_much_data_no_exception(self):
		self.wait_request_and_respond(b"\x6F\x01\x32\x01\x4B\xAA")	# Last byte is extra

	def _test_io_control_bad_response_too_much_data_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		response = self.udsclient.io_control(control_param=1, did=0x132)
		self.assertFalse(response.valid)

	def test_io_control_bad_response_wrong_control_param_exception(self):
		self.wait_request_and_respond(b"\x6F\x01\x32\x04\x4B")	# 0x04 should be 0x03

	def _test_io_control_bad_response_wrong_control_param_exception(self):
		with self.assertRaises(UnexpectedResponseException):
			self.udsclient.io_control(control_param=3, did=0x132)	

	def test_io_control_bad_response_wrong_control_param_no_exception(self):
		self.wait_request_and_respond(b"\x6F\x01\x32\x04\x4B")	# 0x04 should be 0x03

	def _test_io_control_bad_response_wrong_control_param_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		response = self.udsclient.io_control(control_param=3, did=0x132)
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)
