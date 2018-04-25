from . import *
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

	@classmethod
	def normalize_communication_type(self, communication_type):
		from udsoncan import CommunicationType

		if not isinstance(communication_type, CommunicationType) and not isinstance(communication_type, int):
			raise ValueError('communication_type must either be a CommunicationType object or an integer')

		if isinstance(communication_type, int):
			communication_type = CommunicationType.from_byte(communication_type)

		return communication_type

	@classmethod
	def make_request(cls, control_type, communication_type):
		from udsoncan import Request

		ServiceHelper.validate_int(control_type, min=0, max=0x7F, name='Control type')

		communication_type = cls.normalize_communication_type(communication_type)
		request = Request(service=cls, subfunction=control_type)
		request.data = communication_type.get_byte()

		return request

	@classmethod
	def interpret_response(cls, response):
		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

		response.service_data = cls.ResponseData()
		response.service_data.control_type_echo = response.data[0]

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(CommunicationControl)
			self.control_type_echo = None