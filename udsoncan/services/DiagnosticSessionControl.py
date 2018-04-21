from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class DiagnosticSessionControl(BaseService):
	_sid = 0x10

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
									Response.Code.IncorrectMessageLegthOrInvalidFormat,
									Response.Code.ConditionsNotCorrect
									]
	class Session(BaseSubfunction):
		__pretty_name__ = 'session'	# Only to print "custom session" instead of "custom subfunction"

		defaultSession = 1
		programmingSession = 2
		extendedDiagnosticSession = 3
		safetySystemDiagnosticSession = 4

	def __init__(self, session):
		if not isinstance(session, int):
			raise ValueError("Given session number is not a valid integer")

		if session < 0 or session > 0xFF:
			raise ValueError("Session number must be an integer between 0 and 0xFF")

		self.session = session

	def subfunction_id(self):
		return self.session