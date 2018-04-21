from . import BaseService, BaseSubfunction
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

	def __init__(self, memory_location):
		from udsoncan import MemoryLocation
		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('Given memory location must be an instance of MemoryLocation')

		self.memory_location = memory_location