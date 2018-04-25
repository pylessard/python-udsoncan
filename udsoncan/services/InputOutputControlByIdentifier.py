from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct, math

class InputOutputControlByIdentifier(BaseService):
	_sid = 0x2F
	_use_subfunction = False

	#As defined by ISO-14229:2006, Annex E
	class ControlParam(BaseSubfunction):
		__pretty_name__ = 'control parameter'

		returnControlToECU = 0
		resetToDefault = 1
		freezeCurrentState = 2
		shortTermAdjustment = 3

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	@classmethod
	def make_request(cls, did, control_param=None, values=None, masks=None, ioconfig=None):
		from udsoncan import Request, IOMasks, IOValues, DidCodec
		
		ServiceHelper.validate_int(did, min=0, max=0xffff, name='DID')
		if control_param is not None:
			if not isinstance(control_param, int):
				raise ValueError("control_param  must be a valid integer")

			if control_param < 0 or control_param > 3:
				raise ValueError('control_param must either be returnControlToECU(0), resetToDefault(1), freezeCurrentState(2), shortTermAdjustment(3). %d given.' % control_param)
		
		if values is not None:
			if isinstance(values, list):
				values = IOValues(*values)
			if isinstance(values, dict):
				values = IOValues(**values)

			if not isinstance(values, IOValues):
				raise ValueError("values must be an instance of IOValues")

		if masks is not None:
			if isinstance(masks, list):
				masks = IOMasks(*masks)
			if isinstance(masks, dict):
				masks = IOMasks(**masks)

			if not isinstance(masks, IOMasks) and not isinstance(masks, bool):
				raise ValueError("masks must be an instance of IOMask or a boolean value")

		if values is None and masks is not None:
			raise ValueError('An IOValue must be given if a IOMask is provided.')	

		request = Request(service=cls)		

		request.data = b''
		ioconfig = ServiceHelper.check_io_config(did, ioconfig)	# IO dids are defined in client config.
		request.data += struct.pack('>H', did)

		# This parameters is optional according to standard
		if control_param is not None:
			request.data += struct.pack('B', control_param)
		
		codec = DidCodec.from_config(ioconfig[did])	# Get IO codec from config
		
		if values is not None:
			request.data += codec.encode(*values.args, **values.kwargs)

		if masks is not None: # Skip the masks byte if none is given.
			if isinstance(masks, bool):
				byte = b'\xFF' if masks == True else b'\x00'
				if 'mask_size' in  ioconfig[did]:
					request.data += (byte * ioconfig[did]['mask_size'])
				else:
					raise ConfigError('mask_size', msg='Given mask is boolean value, indicating that all mask should be set to same value, but no mask_size is defined in configuration. Cannot guess how many bits to set.')

			elif isinstance(masks, IOMasks):
				if 'mask' not in ioconfig[did]:
					raise ConfigError('mask', msg='Cannot apply given mask. Input/Output configuration does not define their position (and size).')
				masks_config = ioconfig[did]['mask']
				given_masks = masks.get_dict()

				numeric_val = 0
				for mask_name in given_masks:
					if mask_name not in masks_config:
						raise ConfigError('mask_size', msg='Cannot set mask bit for mask %s. The configuration does not define its position' % (mask_name))	
					
					if given_masks[mask_name] == True:
						numeric_val |= masks_config[mask_name]

				minsize = math.ceil(math.log(numeric_val+1, 2)/8.0)
				size = minsize if 'mask_size' not in ioconfig[did] else ioconfig[did]['mask_size']
				request.data += numeric_val.to_bytes(size, 'big')
		return request


	@classmethod
	def interpret_response(cls, response, control_param=None, tolerate_zero_padding=True, ioconfig=None):
		from udsoncan import DidCodec
		min_response_size = 2 if control_param is not None else 1	# Spec specifies that if first by is a ControlParameter, it must be echoed back by the server

		if len(response.data) < min_response_size:
			raise InvalidResponseException(response, "Response must be at least %d bytes long" % min_response_size)

		response.service_data = cls.ResponseData()
		response.service_data.did_echo = struct.unpack(">H", response.data[0:2])[0]

		did = response.service_data.did_echo
		ioconfig = ServiceHelper.check_io_config(did, ioconfig)	# IO dids are defined in client config.
		codec = DidCodec.from_config(ioconfig[did])	# Get IO codec from config

		next_byte = 2
		if control_param is not None:
			if len(response.data) < next_byte:
				raise InvalidResponseException(response, 'Response should include an echo of the InputOutputControlParameter (0x%02x)' % control_param)
			response.service_data.control_param_echo = response.data[next_byte]
			next_byte +=1

		if len(response.data) >= next_byte:
			remaining_data = response.data[next_byte:]
			
			if len(remaining_data) > len(codec):
				if remaining_data[len(codec):] == b'\x00' * (len(remaining_data) - len(codec)):
					if tolerate_zero_padding:
						remaining_data = remaining_data[0:len(codec)]
			try:
				response.service_data.decoded_data = codec.decode(remaining_data)
			except Exception as e:
				raise UnexpectedResponseException(response, 'Response from server could not be decoded. Exception is : %s' % e)
			
	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(InputOutputControlByIdentifier)
			self.did_echo = None
			self.control_param_echo = None
			self.decoded_data = None
			