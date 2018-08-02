from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class DiagnosticSessionControl(BaseService):
	_sid = 0x10

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
									Response.Code.IncorrectMessageLegthOrInvalidFormat,
									Response.Code.ConditionsNotCorrect
									]
	class Session(BaseSubfunction):
		"""
		DiagnosticSessionControl defined subfunctions
		"""		
		__pretty_name__ = 'session'	

		defaultSession = 1
		programmingSession = 2
		extendedDiagnosticSession = 3
		safetySystemDiagnosticSession = 4

	@classmethod
	def make_request(cls, session):
		"""
		Generates a request for DiagnosticSessionControl service

		:param session: Service subfunction. Allowed values are from 0 to 0x7F
		:type session: int

		:raises ValueError: If parameters are out of range, missing or wrong type
		"""

		from udsoncan import Request
		ServiceHelper.validate_int(session, min=0, max=0x7F, name='Session number')
		return Request(service=cls, subfunction=session)

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response ``service_data`` property with an instance of :class:`DiagnosticSessionControl.ResponseData<udsoncan.services.DiagnosticSessionControl.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`

		:raises InvalidResponseException: If length of ``response.data`` is too short
		"""

		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.session_echo = response.data[0]
		response.service_data.session_param_records = response.data[1:] if len(response.data) > 1 else b''

		return response

	class ResponseData(BaseResponseData):
		"""
		.. data:: session_echo

			Request subfunction echoed back by the server

		.. data:: session_param_records

			Additional data associated with the response.
		"""		
		def __init__(self):
			super().__init__(DiagnosticSessionControl)
			self.session_echo = None
			self.session_param_records = None