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
		__pretty_name__ = 'session'	# Only to print "custom session" instead of "custom subfunction"

		defaultSession = 1
		programmingSession = 2
		extendedDiagnosticSession = 3
		safetySystemDiagnosticSession = 4

	@classmethod
	def make_request(cls, session):
		from udsoncan import Request
		ServiceHelper.validate_int(session, min=0, max=0xFF, name='Session number')
		return Request(service=cls, subfunction=session)

	@classmethod
	def interpret_response(cls, response):
		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.session_echo = response.data[0]
		response.service_data.session_param_records = response.data[1:] if len(response.data) > 1 else b''

		return response

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(DiagnosticSessionControl)
			self.session_echo = None
			self.session_param_records = None