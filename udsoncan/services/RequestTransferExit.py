from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class RequestTransferExit(BaseService):
	_sid = 0x37
	_use_subfunction = False
	_no_response_data = True

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestSequenceError
							]

	@classmethod
	def make_request(cls, data=None):
		"""
		Generate a request for RequestTransferExit

		:param data: Additional optional data to send to the server
		:type data: bytes

		:raises ValueError: If parameters are out of range or missing
		"""			
		from udsoncan import Request, MemoryLocation
		
		if data is not None and not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		request = Request(service=cls, data=data)
		return request

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response `service_data` property with an instance of `RequestTransferExit.ResponseData`

		:param response: The received response to interpret
		:type response: Response
		"""				
		response.service_data = cls.ResponseData()
		response.service_data.parameter_records = response.data

	class ResponseData(BaseResponseData):
		"""
		.. data:: parameter_records

			bytes object containing optional data provided by the server
		"""		
		def __init__(self):
			super().__init__(RequestTransferExit)
			self.parameter_records = None