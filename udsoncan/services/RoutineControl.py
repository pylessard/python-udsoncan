from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class RoutineControl(BaseService):
	_sid = 0x31

	class ControlType(BaseSubfunction):
		__pretty_name__ = 'control type'

		startRoutine = 1
		stopRoutine = 2
		requestRoutineResults = 3

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	@classmethod
	def make_request(cls, routine_id, control_type, data=None):
		from udsoncan import Request

		ServiceHelper.validate_int(routine_id, min=0, max=0xFFFF, name='Routine ID')
		ServiceHelper.validate_int(control_type, min=0, max=0x7F, name='Routine control type')
		
		if data is not None:
			if not isinstance(data, bytes):
				raise ValueError('data must be a valid bytes object')

		request = Request(service=cls, subfunction=control_type)
		request.data = struct.pack('>H', routine_id)
		if data is not None:
			request.data += data

		return request

	@classmethod
	def interpret_response(cls, response):
		if len(response.data) < 3: 	
			raise InvalidResponseException(response, "Response data must be at least 3 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.control_type_echo = response.data[0]
		response.service_data.routine_id_echo = struct.unpack(">H", response.data[1:3])[0]
		response.service_data.routine_status_record = response.data[3:] if len(response.data) >3 else b''

	class ResponseData(BaseResponseData):
		def __init__(self):
			super().__init__(RoutineControl)

			self.control_type_echo = None
			self.routine_id_echo = None
			self.routine_status_record = None
			