from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ControlDTCSetting(BaseService):
	_sid = 0x85

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]
	class SettingType(BaseSubfunction):
		__pretty_name__ = 'setting type'

		on = 1
		off = 2
		vehicleManufacturerSpecific = (0x40, 0x5F)	# To be able to print textual name for logging only.
		systemSupplierSpecific = (0x60, 0x7E)		# To be able to print textual name for logging only.

	def __init__(self, setting_type, data = None):

		if not isinstance(setting_type, int):
			raise ValueError('setting_type must be an integer')

		if setting_type < 0 or setting_type > 0x7F:
			raise ValueError('setting_type must be an integer between 0 and 0x7F')

		if data is not None:
			if not isinstance(data, bytes):
				raise ValueError('data must be a valid bytes object')

		self.setting_type = setting_type
		self.data = data

	def subfunction_id(self):
		return self.setting_type
