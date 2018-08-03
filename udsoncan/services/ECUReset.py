from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ECUReset(BaseService):
	_sid = 0x11

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
								Response.Code.IncorrectMessageLegthOrInvalidFormat,
								Response.Code.ConditionsNotCorrect,
								Response.Code.SecurityAccessDenied
								]

	class ResetType(BaseSubfunction):
		"""
		ECUReset defined subfunctions
		"""		
		__pretty_name__ = 'reset type' # Only to print "custom reset type" instead of "custom subfunction"

		hardReset = 1
		keyOffOnReset = 2
		softReset = 3
		enableRapidPowerShutDown = 4
		disableRapidPowerShutDown = 5

	@classmethod
	def make_request(cls, reset_type):
		"""
		Generates a request for ECUReset

		:param reset_type: Service subfunction. Allowed values are from 0 to 0x7F
		:type reset_type: int

		:raises ValueError: If parameters are out of range, missing or wrong type
		"""		
		from udsoncan import Request
		ServiceHelper.validate_int(reset_type, min=0, max=0x7F, name='Reset type')
		return Request(service=cls, subfunction=reset_type)
		

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response ``service_data`` property with an instance of :class:`ECUReset.ResponseData<udsoncan.services.ECUReset.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`

		:raises InvalidResponseException: If length of ``response.data`` is too short
		"""

		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		response.service_data = cls.ResponseData()
		response.service_data.reset_type_echo = response.data[0]

		if response.service_data.reset_type_echo == cls.ResetType.enableRapidPowerShutDown:
			if len(response.data) < 2:
				raise InvalidResponseException(response, 'Response data is missing a second byte for rest type "enableRapidPowerShutDown"')

			response.service_data.powerdown_time = response.data[1]

	class ResponseData(BaseResponseData):
		"""
		.. data:: reset_type_echo

			Request subfunction echoed back by the server

		.. data:: powerdown_time

			Amount of time, in seconds, before the power down sequence is executed. Should be provided only when reset type is enableRapidPowerShutDown
		"""		
		def __init__(self):
			super().__init__(ECUReset)

			self.reset_type_echo = None
			self.powerdown_time = None


