from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class RequestUpload(BaseService):
	_sid = 0x35
	_use_subfunction = False

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.UploadDownloadNotAccepted
							]

	def __init__(self, memory_location, dfi=None):
		from udsoncan import DataFormatIdentifier, MemoryLocation
		
		if dfi is None:
			dfi = DataFormatIdentifier()

		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		if not isinstance(dfi, DataFormatIdentifier):
			raise ValueError('dfi must be an instance of DataFormatIdentifier')

		self.memory_location = memory_location
		self.dfi = dfi