from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct, math

class InputOutputControlByIdentifier(BaseService):
	_sid = 0x2F
	_use_subfunction = False

	#
	class ControlParam(BaseSubfunction):
		"""
		InputOutputControlByIdentifier defined control parameters as defined by ISO-14229:2006, Annex E
		"""	

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
		"""
		Generates a request for InputOutputControlByIdentifier

		:param did: Data identifier to represent the IO
		:type did: int

		:param control_param: Optional parameter that can be a value defined in :class:`InputOutputControlByIdentifier.ControlParam<udsoncan.services.InputOutputControlByIdentifier.ControlParam>`
		:type control_param: int

		:param values: Optional values to send to the server. This parameter will be given to :ref:`DidCodec<DidCodec>`.encode() method. 
			It can be:
			
				- A list for positional arguments
				- A dict for named arguments
				- An instance of :ref:`IOValues<IOValues>` for mixed arguments

		:type values: list, dict, :ref:`IOValues<IOValues>`

		:param masks: Optional mask record for composite values. The mask definition must be included in ``ioconfig``
			It can be:

				- A list naming the bit mask to set
				- A dict with the mask name as a key and a boolean as the value (True to set the mask, False to clear it)
				- An instance of :ref:`IOMask<IOMask>`
				- A boolean value to set all masks to the same value.
		:type masks: list, dict, :ref:`IOMask<IOMask>`, bool

		:param ioconfig: Definition of DID codecs. Dictionary mapping a DID (int) to a valid :ref:`DidCodec<DidCodec>` class or pack/unpack string. 
			It is possible to use composite :ref:`DidCodec<DidCodec>` by specifying a dict with entries : codec, mask, mask_size.
		:type ioconfig: dict[int] = :ref:`DidCodec<DidCodec>`, dict

		:raises ValueError: If parameters are out of range, missing or wrong type
		:raises ConfigError: If given DID is not defined within ioconfig
		"""	

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

		# This parameter is optional according to standard
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
		"""
		Populates the response ``service_data`` property with an instance of :class:`InputOutputControlByIdentifier.ResponseData<udsoncan.services.InputOutputControlByIdentifier.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`
		
		:param control_param:  Same optional control parameter value given to make_request()
		:type control_param: int
		
		:param tolerate_zero_padding: Ignore trailing zeros in the response data avoiding raising false :class:`InvalidResponseException<udsoncan.exceptions.InvalidResponseException>`.
		:type tolerate_zero_padding: bool

		:param ioconfig: Definition of DID codecs. Dictionary mapping a DID (int) to a valid :ref:`DidCodec<DidCodec>` class or pack/unpack string. 
			It is possible to use composite DidCodec by specifying a dict with entries : codec, mask, mask_size.
		:type ioconfig: dict[int] = :ref:`DidCodec<DidCodec>`, dict

		:raises ValueError: If parameters are out of range, missing or wrong type
		:raises ConfigError: If DID echoed back by the server is not in the ``ioconfig`` definition
		:raises InvalidResponseException: If response data is incomplete or if DID data does not match codec length.
		"""	

		from udsoncan import DidCodec
		min_response_size = 2 if control_param is not None else 1	# Spec specifies that if first byte is a ControlParameter, it must be echoed back by the server

		if len(response.data) < min_response_size:
			raise InvalidResponseException(response, "Response must be at least %d bytes long" % min_response_size)

		response.service_data = cls.ResponseData()
		response.service_data.did_echo = struct.unpack(">H", response.data[0:2])[0]

		did = response.service_data.did_echo
		ioconfig = ServiceHelper.check_io_config(did, ioconfig)	# IO DIDs are defined in client config.
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
				raise InvalidResponseException(response, 'Response from server could not be decoded. Exception is : %s' % e)
			
	class ResponseData(BaseResponseData):
		"""
		.. data:: did_echo

			DID echoed back by the server

		.. data:: control_param_echo

			control_param echoed back by the server

		.. data:: decoded_data

			Value processed by the :ref:`DidCodec<DidCodec>`.decode() method
		"""			
		def __init__(self):
			super().__init__(InputOutputControlByIdentifier)
			self.did_echo = None
			self.control_param_echo = None
			self.decoded_data = None
			