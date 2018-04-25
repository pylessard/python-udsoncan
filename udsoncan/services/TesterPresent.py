from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class TesterPresent(BaseService):
	_sid = 0x3E

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat
							]	

	@classmethod
	def make_request(cls):
		from udsoncan import Request
		return Request(service=cls, subfunction=0)

	@classmethod
	def interpret_response(cls, response):
		if  len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.subfunction_echo = response.data[0]

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(TesterPresent)
			self.subfunction_echo = None
