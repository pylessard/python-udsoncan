from udsoncan.client import Client
from udsoncan import services, CommunicationType
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestCommunicationControl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

#========================================
	def test_comcontrol_enable_node(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x28\x00\x01")
		self.conn.fromuserqueue.put(b"\x68\x00")	# Positive response


	def _test_comcontrol_enable_node(self):
		control_type = services.CommunicationControl.enableRxAndTx
		com_type = CommunicationType(subnet=CommunicationType.Subnet.node, normal_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)

#========================================
	def test_comcontrol_disable_subnet(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x28\x03\x33")
		self.conn.fromuserqueue.put(b"\x68\x03")	# Positive response


	def _test_comcontrol_disable_subnet(self):
		control_type = services.CommunicationControl.disableRxAndTx
		com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	

#========================================
	def test_comcontrol_negative_response(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.conn.fromuserqueue.put(b"\x68\x7F\x31") 	# Request Out Of Range

	def _test_comcontrol_negative_response(self):
		with self.assertRaises(NegativeResponseException) as handle:
			control_type = services.CommunicationControl.disableRxAndTx
			com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
			response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	

#========================================
	def test_set_params_invalidservice(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.conn.fromuserqueue.put(b"\x00\x22") #Inexistent Service

	def _test_set_params_invalidservice(self):
		with self.assertRaises(InvalidResponseException) as handle:
			control_type = services.CommunicationControl.disableRxAndTx
			com_type = CommunicationType(subnet=5, normal_msg=True, network_management_msg=True)
			response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	

#========================================
	def test_comcontrol_wrongservice(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_comcontrol_wrongservice(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			control_type = services.CommunicationControl.disableRxAndTx
			com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
			response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	

#========================================
	def test_comcontrol_bad_control_type(self):
		request = self.conn.touserqueue.get(timeout=1)
		self.conn.fromuserqueue.put(b"\x68\x08") # Valid but bad control type

	def _test_comcontrol_bad_control_type(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
			response = self.udsclient.communication_control(control_type=9, communication_type=com_type)	

#========================================
	def test_bad_param(self):
		pass

	def _test_bad_param(self):
		valid_com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		with self.assertRaises(ValueError):
			self.udsclient.communication_control(control_type='x', communication_type=valid_com_type)	

		with self.assertRaises(ValueError):
			self.udsclient.communication_control(control_type=0x80, communication_type=valid_com_type)

		with self.assertRaises(ValueError):
			self.udsclient.communication_control(control_type=-1, communication_type=valid_com_type)

		with self.assertRaises(ValueError):
			self.udsclient.communication_control(control_type=0, communication_type='x')