from . import BaseService, BaseSubfunction
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

	def __init__(self, control_type, baudrate=None):
		from udsoncan import Baudrate
		if not isinstance(control_type, int):
			raise ValueError('control_type must be an integer')

		if control_type < 0 or control_type > 0x7F:
			raise ValueError('control_type must be an integer between 0 and 0x7F')

		if control_type in [self.ControlType.verifyBaudrateTransitionWithSpecificBaudrate, self.ControlType.verifyBaudrateTransitionWithFixedBaudrate]:
			if baudrate is None:
				raise ValueError('A Baudrate must be provided with control type : "verifyBaudrateTransitionWithSpecificBaudrate" (0x%02x) or "verifyBaudrateTransitionWithFixedBaudrate" (0x%02x)' % (self.ControlType.verifyBaudrateTransitionWithSpecificBaudrate, self.ControlType.verifyBaudrateTransitionWithFixedBaudrate))

			if not isinstance(baudrate, Baudrate):
				raise ValueError('Given baudrate must be an instance of the Baudrate class')
		else:
			if baudrate is not None:
				raise ValueError('The baudrate parameter is only needed when control type is "verifyBaudrateTransitionWithSpecificBaudrate" (0x%02x) or "verifyBaudrateTransitionWithFixedBaudrate" (0x%02x)' % (self.ControlType.verifyBaudrateTransitionWithSpecificBaudrate, self.ControlType.verifyBaudrateTransitionWithFixedBaudrate))

		self.baudrate = baudrate
		self.control_type = control_type
		
		if control_type == self.ControlType.verifyBaudrateTransitionWithSpecificBaudrate:
			self.baudrate = self.baudrate.make_new_type(Baudrate.Type.Specific)

		if control_type == self.ControlType.verifyBaudrateTransitionWithFixedBaudrate and baudrate.baudtype == Baudrate.Type.Specific:
			self.baudrate = self.baudrate.make_new_type(Baudrate.Type.Fixed)


	def subfunction_id(self):
		return self.control_type;
