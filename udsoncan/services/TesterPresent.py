from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class TesterPresent(BaseService):
	_sid = 0x3E

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat
							]