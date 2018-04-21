from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class RequestTransferExit(BaseService):
	_sid = 0x37
	_use_subfunction = False
	_no_response_data = True

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestSequenceError
							]

	def __init__(self, data=None):
		if data is not None and not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		self.data= data