from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ReadMemoryByAddress(BaseService):
	_sid = 0x23
	_use_subfunction = False

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	@classmethod
	def make_request(cls, memory_location):
		"""
		Generate a request for ReadMemoryByAddress

		:param memory_location: The address and the size of the memory block to read.
		:type memory_location: :ref:`MemoryLocation <HelperClass_MemoryLocation>`

		:raises ValueError: If parameters are out of range or missing
		"""		
		from udsoncan import Request, MemoryLocation

		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('Given memory location must be an instance of MemoryLocation')

		request =  Request(service=cls)
		request.data = b''
		request.data += memory_location.alfid.get_byte() # AddressAndLengthFormatIdentifier
		request.data += memory_location.get_address_bytes()
		request.data += memory_location.get_memorysize_bytes()

		return request

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response `service_data` property with an instance of `ReadMemoryByAddress.ResponseData`

		:param response: The received response to interpret
		:type response: Response

		:raises InvalidResponseException: If length of response.data is too small
		"""		
		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

		response.service_data = cls.ResponseData()
		response.service_data.memory_block = response.data

	class ResponseData(BaseResponseData):
		"""
		.. data:: memory_block

			bytes object reflecting the content of the read memory
		"""
		def __init__(self):
			super().__init__(ReadMemoryByAddress)
			self.memory_block = None