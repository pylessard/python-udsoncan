from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class LinkControl(BaseService):
	_sid = 0x87

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange
							]
	class ControlType(BaseSubfunction):
		__pretty_name__ = 'control type'

		verifyBaudrateTransitionWithFixedBaudrate = 1
		verifyBaudrateTransitionWithSpecificBaudrate = 2
		transitionBaudrate = 3

	@classmethod
	def make_request(cls, control_type, baudrate=None):
		from udsoncan import Request, Baudrate
		
		ServiceHelper.validate_int(control_type, min=0, max=0x7F, name='Control type')

		if control_type in [cls.ControlType.verifyBaudrateTransitionWithSpecificBaudrate, cls.ControlType.verifyBaudrateTransitionWithFixedBaudrate]:
			if baudrate is None:
				raise ValueError('A Baudrate must be provided with control type : "verifyBaudrateTransitionWithSpecificBaudrate" (0x%02x) or "verifyBaudrateTransitionWithFixedBaudrate" (0x%02x)' % (cls.ControlType.verifyBaudrateTransitionWithSpecificBaudrate, cls.ControlType.verifyBaudrateTransitionWithFixedBaudrate))

			if not isinstance(baudrate, Baudrate):
				raise ValueError('Given baudrate must be an instance of the Baudrate class')
		else:
			if baudrate is not None:
				raise ValueError('The baudrate parameter is only needed when control type is "verifyBaudrateTransitionWithSpecificBaudrate" (0x%02x) or "verifyBaudrateTransitionWithFixedBaudrate" (0x%02x)' % (cls.ControlType.verifyBaudrateTransitionWithSpecificBaudrate, cls.ControlType.verifyBaudrateTransitionWithFixedBaudrate))

		if control_type == cls.ControlType.verifyBaudrateTransitionWithSpecificBaudrate:
			baudrate = baudrate.make_new_type(Baudrate.Type.Specific)

		if control_type == cls.ControlType.verifyBaudrateTransitionWithFixedBaudrate and baudrate.baudtype == Baudrate.Type.Specific:
			baudrate = baudrate.make_new_type(Baudrate.Type.Fixed)

		request = Request(service=cls, subfunction=control_type)
		if baudrate is not None:
			request.data = baudrate.get_bytes()
		return request

	@classmethod
	def interpret_response(cls, response):
		if len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes") 

		response.service_data = cls.ResponseData()
		response.service_data.control_type_echo = response.data[0]

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(LinkControl)
			self.control_type_echo = None
