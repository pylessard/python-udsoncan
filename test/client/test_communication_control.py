from udsoncan.client import Client
from udsoncan import services, CommunicationType
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestCommunicationControl(ClientServerTest):
	def __init__(self, *args, **kwargs):
		ClientServerTest.__init__(self, *args, **kwargs)

	def test_comcontrol_enable_node(self):
		for i in range(3):
				request = self.conn.touserqueue.get(timeout=0.2)
				self.assertEqual(request, b"\x28\x00\x01")
				self.conn.fromuserqueue.put(b"\x68\x00")	# Positive response

	def _test_comcontrol_enable_node(self):
		control_type = services.CommunicationControl.ControlType.enableRxAndTx
		com_type = CommunicationType(subnet=CommunicationType.Subnet.node, normal_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, control_type)

		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type.get_byte())
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, control_type)

		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type.get_byte_as_int())
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, control_type)



	def test_comcontrol_enable_node_spr(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x28\x80\x01")
		self.conn.fromuserqueue.put('wait')	# Synchronize

	def _test_comcontrol_enable_node_spr(self):
		control_type = services.CommunicationControl.ControlType.enableRxAndTx
		com_type = CommunicationType(subnet=CommunicationType.Subnet.node, normal_msg=True)
		with self.udsclient.suppress_positive_response:
			response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)
			self.assertEqual(response, None)
		self.conn.fromuserqueue.get(timeout=0.2)	#Avoid closing connection prematurely

	def test_comcontrol_disable_subnet(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.assertEqual(request, b"\x28\x03\x33")
		self.conn.fromuserqueue.put(b"\x68\x03")	# Positive response

	def _test_comcontrol_disable_subnet(self):
		control_type = services.CommunicationControl.ControlType.disableRxAndTx
		com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	
		self.assertTrue(response.positive)
		self.assertEqual(response.service_data.control_type_echo, control_type)

	def test_comcontrol_negative_response_exception(self):
		self.wait_request_and_respond(b"\x7F\x28\x31") 	# Request Out Of Range

	def _test_comcontrol_negative_response_exception(self):
		with self.assertRaises(NegativeResponseException) as handle:
			control_type = services.CommunicationControl.ControlType.disableRxAndTx
			com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
			self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	

	def test_comcontrol_negative_response_no_exception(self):
		self.wait_request_and_respond(b"\x7F\x28\x31") 	# Request Out Of Range

	def _test_comcontrol_negative_response_no_exception(self):
		self.udsclient.config['exception_on_negative_response'] = False
		control_type = services.CommunicationControl.ControlType.disableRxAndTx
		com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)				
		self.assertTrue(response.valid)
		self.assertFalse(response.positive)
		
	def test_set_params_invalidservice_exception(self):
		self.wait_request_and_respond(b"\x00\x22") #Inexistent Service

	def _test_set_params_invalidservice_exception(self):
		with self.assertRaises(InvalidResponseException) as handle:
			control_type = services.CommunicationControl.ControlType.disableRxAndTx
			com_type = CommunicationType(subnet=5, normal_msg=True, network_management_msg=True)
			self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	
		
	def test_set_params_invalidservice_no_exception(self):
		request = self.conn.touserqueue.get(timeout=0.2)
		self.conn.fromuserqueue.put(b"\x00\x22") #Inexistent Service

	def _test_set_params_invalidservice_no_exception(self):
		self.udsclient.config['exception_on_invalid_response'] = False
		control_type = services.CommunicationControl.ControlType.disableRxAndTx
		com_type = CommunicationType(subnet=5, normal_msg=True, network_management_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	
		self.assertFalse(response.valid)

	def test_comcontrol_wrongservice_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_comcontrol_wrongservice_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			control_type = services.CommunicationControl.ControlType.disableRxAndTx
			com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
			self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	

	def test_comcontrol_wrongservice_no_exception(self):
		self.wait_request_and_respond(b"\x7E\x22") # Valid but wrong service (Tester Present)

	def _test_comcontrol_wrongservice_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		control_type = services.CommunicationControl.ControlType.disableRxAndTx
		com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		response = self.udsclient.communication_control(control_type=control_type, communication_type=com_type)	
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

	def test_comcontrol_bad_control_type_exception(self):
		self.wait_request_and_respond(b"\x68\x08") # Valid but bad control type

	def _test_comcontrol_bad_control_type_exception(self):
		with self.assertRaises(UnexpectedResponseException) as handle:
			com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
			self.udsclient.communication_control(control_type=9, communication_type=com_type)	

	def test_comcontrol_bad_control_type_no_exception(self):
		self.wait_request_and_respond(b"\x68\x08") # Valid but bad control type

	def _test_comcontrol_bad_control_type_no_exception(self):
		self.udsclient.config['exception_on_unexpected_response'] = False
		com_type = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		response = self.udsclient.communication_control(control_type=9, communication_type=com_type)	
		self.assertTrue(response.valid)
		self.assertTrue(response.unexpected)

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