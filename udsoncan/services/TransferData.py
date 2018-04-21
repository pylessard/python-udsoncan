from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class TransferData(BaseService):
	_sid = 0x36

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange,
							Response.Code.TransferDataSuspended,
							Response.Code.GeneralProgrammingFailure,
							Response.Code.WrongBlockSequenceCounter,
							Response.Code.VoltageTooHigh,
							Response.Code.VoltageTooLow
							]

	def __init__(self, block_sequence_counter, data=None):
		if not isinstance(block_sequence_counter, int):
			raise ValueError('block_sequence_counter must be an integer')

		if block_sequence_counter < 0 or block_sequence_counter > 0xFF:
			raise ValueError('block_sequence_counter must be an integer between 0 and 0xFF')

		if data is not None and not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		self.block_sequence_counter = block_sequence_counter
		self.data= data

	def subfunction_id(self):
		return self.block_sequence_counter