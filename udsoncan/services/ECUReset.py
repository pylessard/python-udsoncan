from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ECUReset(BaseService):
	_sid = 0x11

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
								Response.Code.IncorrectMessageLegthOrInvalidFormat,
								Response.Code.ConditionsNotCorrect,
								Response.Code.SecurityAccessDenied
								]

	class ResetType(BaseSubfunction):
		__pretty_name__ = 'reset type' # Only to print "custom reset type" instead of "custom subfunction"

		hardReset = 1
		keyOffOnReset = 2
		softReset = 3
		enableRapidPowerShutDown = 4
		disableRapidPowerShutDown = 5

	def __init__(self, resettype=None, powerdowntime=None):
		if not isinstance(resettype, int):
			raise ValueError('Reset type must be a integer')
		if resettype < 0 or resettype > 0xFF:
			raise ValueError('Reset type must be a value between 0 and 0x7F')

		if resettype == self.ResetType.enableRapidPowerShutDown:
			if powerdowntime is None:
				raise ValueError('Power down time must be provided for reset of type enableRapidPowerShutDown')
			
			if not isinstance(powerdowntime, int) or powerdowntime < 0 or powerdowntime > 0xFF:
				raise ValueError('Power down time must be an integer between 0 and 0xFF')
		
		self.resettype = resettype
		self.powerdowntime = powerdowntime

	def subfunction_id(self):
		return self.resettype