from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class TransferData(BaseService):
	_sid = 0x36
	_use_subfunction = False

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
		"""
		Generates a request for TransferData

		:param sequence_number: Corresponds to an 8bit counter that should increment for each new block transferred.
			Allowed values are from 0 to 0xFF
		:type sequence_number: int

		:param data: Optional additional data to send to the server
		:type data: bytes

		:raises ValueError: If parameters are out of range, missing or wrong type
		"""		
		from udsoncan import Request, MemoryLocation
		
		ServiceHelper.validate_int(sequence_number, min=0, max=0xFF, name='Block sequence counter')	# Not a subfunction!

		if data is not None and not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		request = Request(service=cls)
		request.data = struct.pack('B', sequence_number)

		if data is not None:
			request.data += data
		return request

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response ``service_data`` property with an instance of :class:`TransferData.ResponseData<udsoncan.services.TransferData.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`

		:raises InvalidResponseException: If length of ``response.data`` is too short
		"""		
		if len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.sequence_number_echo = response.data[0]
		response.service_data.parameter_records = response.data[1:] if len(response.data) > 1 else b''

	class ResponseData(BaseResponseData):
		"""
		.. data:: sequence_number_echo

			Requests subfunction echoed back by the server

		.. data:: parameter_records

			Optional additional data associated with the response.
		"""		
		def __init__(self):
			super().__init__(TransferData)
			self.sequence_number_echo = None
			self.parameter_records = None
