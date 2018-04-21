from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class AccessTimingParameter(BaseService):
	_sid = 0x83

	class AccessType(BaseSubfunction):
		__pretty_name__ = 'access type'

		readExtendedTimingParameterSet = 1
		setTimingParametersToDefaultValues = 2
		readCurrentlyActiveTimingParameters = 3
		setTimingParametersToGivenValues = 4

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]	

	def __init__(self, access_type, request_record=None):
		if not isinstance(access_type, int):
			raise ValueError('access_type must be an integer')

		if access_type < 0 or access_type > 0x7F:
			raise ValueError('access_type must be an integer between 0 and 0x7F')

		if request_record is not None and access_type != self.AccessType.setTimingParametersToGivenValues :
			raise ValueError('request_record can only be set when access_type is setTimingParametersToGivenValues"')

		if request_record is None and access_type == self.AccessType.setTimingParametersToGivenValues :
			raise ValueError('A request_record must be provided when access_type is "setTimingParametersToGivenValues"')

		if request_record is not None:
			if not isinstance(request_record, bytes):
				raise ValueError("request_record must be a valid bytes objects")

		self.access_type  = access_type
		self.request_record = request_record

	def subfunction_id(self):
		return self.access_type
