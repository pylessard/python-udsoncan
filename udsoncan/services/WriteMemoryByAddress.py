from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class WriteMemoryByAddress(BaseService):
	_sid = 0x3D
	_use_subfunction = False

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	def __init__(self, memory_location, data):
		from udsoncan import MemoryLocation
		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('Given memory location must be an instance of MemoryLocation')

		if not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		self.memory_location = memory_location
		self.data = data