from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ReadScalingDataByIdentifier(BaseService):
	_sid = 0x24

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self, config=None):
		
		pass