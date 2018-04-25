from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class DynamicallyDefineDataIdentifier(BaseService):
	_sid = 0x2C

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self, config=None):
		
		raise NotImplementedError('Service is not implemented')