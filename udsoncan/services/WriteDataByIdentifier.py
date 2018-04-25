from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class WriteDataByIdentifier(BaseService):
	_sid = 0x2E
	_use_subfunction = False

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	@classmethod
	def make_request(cls, did, value, didconfig):
		from udsoncan import Request, DidCodec
		ServiceHelper.validate_int(did, min=0, max=0xFFFF, name='Data Identifier')
		req = Request(cls)
		didconfig = ServiceHelper.check_did_config(did, didconfig=didconfig)	# Make sure all DID are correctly defined in client config
		req.data = struct.pack('>H', did)	# encode DID number
		codec = DidCodec.from_config(didconfig[did])
		req.data += codec.encode(value)

		return req

	@classmethod
	def interpret_response(cls, response):
		if len(response.data) < 2:
			raise InvalidResponseException(response, "Response must be at least 2 bytes long")

		response.service_data = cls.ResponseData()
		response.service_data.did_feedback = struct.unpack(">H", response.data[0:2])[0]

		
	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(WriteDataByIdentifier)

			self.did_feedback = None