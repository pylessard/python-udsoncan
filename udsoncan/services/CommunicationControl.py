from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class CommunicationControl(BaseService):
	_sid = 0x28

	class ControlType(BaseSubfunction):
		__pretty_name__ = 'control type' 

		enableRxAndTx = 0
		enableRxAndDisableTx = 1
		disableRxAndEnableTx = 2
		disableRxAndTx = 3

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]

	def __init__(self, control_type, communication_type):
		from udsoncan import CommunicationType

		if not isinstance(control_type, int):
			raise ValueError('control_type must be an integer')

		if control_type < 0 or control_type > 0x7F:
			raise ValueError('control_type must be an integer between 0 and 0x7F')

		if not isinstance(communication_type, CommunicationType) and not isinstance(communication_type, int):
			raise ValueError('communication_type must either be a CommunicationType object or an integer')

		if isinstance(communication_type, int):
			communication_type = CommunicationType.from_byte(communication_type)

		self.communication_type = communication_type
		self.control_type = control_type

	def subfunction_id(self):
		return self.control_type