from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class CommunicationControl(BaseService):
	_sid = 0x28

	class ControlType(BaseSubfunction):
		"""
		CommunicationControl defined subfunctions
		"""		
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

		if not isinstance(communication_type, CommunicationType) and not isinstance(communication_type, int) and not isinstance(communication_type, bytes):
			raise ValueError('communication_type must either be a CommunicationType object or an integer')

		if isinstance(communication_type, int) or isinstance(communication_type, bytes):
			communication_type = CommunicationType.from_byte(communication_type)

		return communication_type

	@classmethod
	def make_request(cls, control_type, communication_type):
		"""
		Generates a request for CommunicationControl

		:param control_type: Service subfunction. Allowed values are from 0 to 0x7F
		:type control_type: int

		:param communication_type: The communication type requested.
		:type communication_type: :ref:`CommunicationType <CommunicationType>`, int, bytes

		:raises ValueError: If parameters are out of range, missing or wrong type
		"""		
		from udsoncan import Request

		ServiceHelper.validate_int(control_type, min=0, max=0x7F, name='Control type')

		communication_type = cls.normalize_communication_type(communication_type)
		request = Request(service=cls, subfunction=control_type)
		request.data = communication_type.get_byte()

		return request

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response ``service_data`` property with an instance of :class:`CommunicationControl.ResponseData<udsoncan.services.CommunicationControl.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`

		:raises InvalidResponseException: If length of ``response.data`` is too short
		"""		
		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

		response.service_data = cls.ResponseData()
		response.service_data.control_type_echo = response.data[0]

	class ResponseData(BaseResponseData):
		"""
		.. data:: control_type_echo

			Request subfunction echoed back by the server
		"""		
		def __init__(self):
			super().__init__(CommunicationControl)
			self.control_type_echo = None