from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct


class ReadDataByIdentifier(BaseService):
	_sid = 0x22
	_use_subfunction = False


	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]	
	
	@classmethod
	def validate_didlist_input(cls, dids):
		if not isinstance(dids, int) and not isinstance(dids, list):
			raise ValueError("Data Identifier must either be an integer or a list of integer")

		if isinstance(dids, int):
			ServiceHelper.validate_int(dids, min=0, max=0xFFFF, name='Data Identifier')
		
		if isinstance(dids, list):
			for did in dids:
				ServiceHelper.validate_int(did, min=0, max=0xFFFF, name='Data Identifier')


		return [dids] if not isinstance(dids, list) else dids

	@classmethod
	def make_request(cls, didlist, didconfig):
		from udsoncan import Request
		didlist = cls.validate_didlist_input(didlist)

		req = Request(cls)
		ServiceHelper.check_did_config(didlist, didconfig)
		req.data = struct.pack('>'+'H'*len(didlist), *didlist) #Encode list of DID

		return req

	@classmethod
	def interpret_response(cls, response, didlist, didconfig, tolerate_zero_padding=True):
		from udsoncan import DidCodec

		didlist = cls.validate_didlist_input(didlist)
		didconfig = ServiceHelper.check_did_config(didlist, didconfig)
		
		response.service_data = cls.ResponseData()
		response.service_data.values = {}

		# Parsing algorithm to extract DID value
		offset = 0
		while True:
			if len(response.data) <= offset:
				break	# Done

			if len(response.data) <= offset +1:
				if tolerate_zero_padding and response.data[-1] == 0:	# One extra byte, but its a 0 and we accept that. So we're done
					break
				raise InvalidResponseException(response, "Response given by server is incomplete.")

			did = struct.unpack('>H', response.data[offset:offset+2])[0]	# Get the DID number
			if did == 0 and did not in didconfig and tolerate_zero_padding: # We read two zeros and that is not a DID bu we accept that. So we're done.
				if response.data[offset:] == b'\x00' * (len(response.data) - offset):
					break

			if did not in didconfig:	# Already checked in check_did_config. Paranoid check
				raise ConfigError(key=did, msg='Actual data identifier configuration contains no definition for data identifier 0x%04x' % did)
			
			codec = DidCodec.from_config(didconfig[did])
			offset+=2

			if len(response.data) < offset+len(codec):
				raise UnexpectedResponseException(response, "Value fo data identifier 0x%04x was incomplete according to definition in configuration" % did)

			subpayload = response.data[offset:offset+len(codec)]
			offset += len(codec)	# Codec must define a __len__ function that metches the encoded payload length.
			val = codec.decode(subpayload)
			response.service_data.values[did] = val

		return response

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(ReadDataByIdentifier)

			self.values = None