from udsoncan.client import Client
from udsoncan import services, Baudrate
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestLinkContorl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_linkcontrol_verify_fixed(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x01\x11")
		self.conn.fromuserqueue.put(b"\xC7\x01")	# Positive response

	def _test_linkcontrol_verify_fixed(self):
		baudrate = Baudrate(250000, baudtype=Baudrate.Type.Fixed)
		response = self.udsclient.link_control(control_type=1, baudrate=baudrate)

#========================================
	def test_linkcontrol_verify_fixed_from_specific(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x01\x11")
		self.conn.fromuserqueue.put(b"\xC7\x01")	# Positive response

	def _test_linkcontrol_verify_fixed_from_specific(self):
		baudrate = Baudrate(250000, baudtype=Baudrate.Type.Specific)
		response = self.udsclient.link_control(control_type=1, baudrate=baudrate)

#========================================
	def test_linkcontrol_verify_specific(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x02\x12\x34\x56")
		self.conn.fromuserqueue.put(b"\xC7\x02")	# Positive response


	def _test_linkcontrol_verify_specific(self):
		baudrate = Baudrate(0x123456, baudtype=Baudrate.Type.Specific)
		response = self.udsclient.link_control(control_type=2, baudrate=baudrate)

#========================================
	def test_linkcontrol_verify_specific_from_fixed(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x02\x07\xA1\x20")
		self.conn.fromuserqueue.put(b"\xC7\x02")	# Positive response

	def _test_linkcontrol_verify_specific_from_fixed(self):
		baudrate = Baudrate(500000, baudtype=Baudrate.Type.Fixed)
		response = self.udsclient.link_control(control_type=2, baudrate=baudrate)

#========================================
	def test_linkcontrol_custom_control_type(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x87\x55")
		self.conn.fromuserqueue.put(b"\xC7\x55")	# Positive response


	def _test_linkcontrol_custom_control_type(self):
		response = self.udsclient.link_control(control_type=0x55)	

#========================================
	def test_linkcontrol_negative_response(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x7F\x87\x31") 	# Request Out Of Range

	def _test_linkcontrol_negative_response(self):
		with self.assertRaises(NegativeResponseException):
			response = self.udsclient.link_control(control_type=0x55)

#========================================
	def test_linkcontrol_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x00\x22") 	# Request Out Of Range

	def _test_linkcontrol_invalidservice(self):
		with self.assertRaises(InvalidResponseException):
			response = self.udsclient.link_control(control_type=0x55)

#========================================
	def test_linkcontrol_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_linkcontrol_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException):
			response = self.udsclient.link_control(control_type=0x55)

#========================================
	def test_linkcontrol_bad_control_type(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\xC7\x08") # Valid but bad control type

	def _test_linkcontrol_bad_control_type(self):
		with self.assertRaises(UnexpectedResponseException):
			response = self.udsclient.link_control(control_type=0x55)

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type='x')	

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=0x80)

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=1) # Missing Baudrate

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=2) # Missing Baudrate

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=0, baudrate=Baudrate(500000)) # Baudrate is not needed

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=1, baudrate=1) # Baudrate should be Baudrate instance

		with self.assertRaises(ValueError):
			self.udsclient.link_control(control_type=1, baudrate='x') # Baudrate should be Baudrate instance
