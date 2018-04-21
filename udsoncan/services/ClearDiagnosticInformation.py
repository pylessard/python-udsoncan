from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ClearDiagnosticInformation(BaseService):
	_sid = 0x14
	_use_subfunction = False
	_no_response_data = True

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]

	def __init__(self, group=0xFFFFFF):
		if not isinstance(group, int):
			raise ValueError("Group of DTC must be a valid integer")
		if group < 0 or group > 0xFFFFFF:
			raise ValueError("Group of DTC must be an integer between 0 and 0xFFFFFF")

		self.group = group