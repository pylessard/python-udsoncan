from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ReadDataByIdentifier(BaseService):
	_sid = 0x22
	_use_subfunction = False


	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]	

	def __init__(self, dids):
		if not isinstance(dids, int) and not isinstance(dids, list):
			raise ValueError("Data Identifier must either be an integer or a list of integer")

		if isinstance(dids, int):
			if dids < 0 or dids > 0xFFFF:
				raise ValueError("Data Identifier must be set between 0 and 0xFFFF")
		if isinstance(dids, list):
			for did in dids:
				if not isinstance(did, int) or did < 0 or did > 0xFFFF:
					raise ValueError("Data Identifier must be set between 0 and 0xFFFF")

		self.dids = dids