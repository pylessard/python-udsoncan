from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class SecurityAccess(BaseService):
	_sid = 0x27

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange,
							Response.Code.InvalidKey,
							Response.Code.ExceedNumberOfAttempts,
							Response.Code.RequiredTimeDelayNotExpired
							]

	class Mode:
		RequestSeed=0
		SendKey=1

	def __init__(self, level, mode=Mode.RequestSeed):
		if mode not in [SecurityAccess.Mode.RequestSeed, SecurityAccess.Mode.SendKey]:
			raise ValueError("Given mode must be either RequestSeed or Send Key ")
		level = int(level)
		if level > 0x7F or level < 0:
			raise ValueError("Level must be a valid integer between 0 and 0x7F")

		self.level = level
		self.mode = mode

	def subfunction_id(self):
		if self.mode == SecurityAccess.Mode.RequestSeed:
			return self.level if self.level % 2 == 1 else self.level-1
		elif self.mode == SecurityAccess.Mode.SendKey:
			return self.level if self.level % 2 == 0 else self.level+1
		else:
			raise ValueError("Cannot generate subfunction ID. Mode is invalid")