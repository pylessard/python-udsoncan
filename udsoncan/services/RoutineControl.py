from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

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

	def __init__(self, routine_id, control_type, data=None):
		if not isinstance(routine_id, int):
			raise ValueError("Routine ID must be a valid integer")
		if routine_id < 0 or routine_id > 0xFFFF:
			raise ValueError("Routine ID  must be an integer between 0 and 0xFFFF")

		if not isinstance(control_type, int):
			raise ValueError("Routine control type must be a valid integer")
		if control_type < 0 or control_type > 0x7F:
			raise ValueError("Routine control type must be an integer between 0 and 0x7F")

		if data is not None:
			if not isinstance(data, bytes):
				raise ValueError('data must be a valid bytes object')

		self.routine_id = routine_id
		self.control_type = control_type
		self.data = data


	def subfunction_id(self):
		return self.control_type;