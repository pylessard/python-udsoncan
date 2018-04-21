from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class WriteDataByIdentifier(BaseService):
	_sid = 0x2E
	_use_subfunction = False

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	def __init__(self, did):
		if not isinstance(did, int):
			raise ValueError('Data Identifier must be an integer value')
		
		if did < 0 or did > 0xFFFF:
			raise ValueError("Data Identifier must be set between 0 and 0xFFFF")

		self.did = did