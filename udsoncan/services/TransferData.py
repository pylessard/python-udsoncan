from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class TransferData(BaseService):
	_sid = 0x36

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange,
							Response.Code.TransferDataSuspended,
							Response.Code.GeneralProgrammingFailure,
							Response.Code.WrongBlockSequenceCounter,
							Response.Code.VoltageTooHigh,
							Response.Code.VoltageTooLow
							]

	@classmethod
	def make_request(cls, sequence_number, data=None):
		from udsoncan import Request, MemoryLocation
		
		ServiceHelper.validate_int(sequence_number, min=0, max=0xFF, name='Block sequence counter')

		if data is not None and not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		request = Request(service=cls, subfunction=sequence_number, data=data)
		return request

	@classmethod
	def interpret_response(cls, response):
		if len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.sequence_number_echo = response.data[0]
		response.service_data.parameter_records = response.data[1:] if len(response.data) > 1 else b''

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(TransferData)
			self.sequence_number_echo = None
			self.parameter_records = None
