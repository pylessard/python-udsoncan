from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ControlDTCSetting(BaseService):
	_sid = 0x85

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]
	class SettingType(BaseSubfunction):
		"""
		ControlDTCSetting defined subfunctions
		"""

		__pretty_name__ = 'setting type'

		on = 1
		off = 2
		vehicleManufacturerSpecific = (0x40, 0x5F)	# To be able to print textual name for logging only.
		systemSupplierSpecific = (0x60, 0x7E)		# To be able to print textual name for logging only.

	@classmethod
	def make_request(cls, setting_type, data = None):
		"""
		Generates a request for ControlDTCSetting

		:param setting_type: Service subfunction. Allowed values are from 0 to 0x7F
		:type setting_type: int

		:param data: Optional additional data sent with the request called `DTCSettingControlOptionRecord`
		:type data: bytes

		:raises ValueError: If parameters are out of range, missing or wrong type
		"""		
		from udsoncan import Request

		ServiceHelper.validate_int(setting_type, min=0, max=0x7F, name='Setting type')
		if data is not None:
			if not isinstance(data, bytes):
				raise ValueError('data must be a valid bytes object')

		return Request(service=cls, subfunction=setting_type, data=data)

	@classmethod
	def interpret_response(cls, response):
		"""
		Populates the response ``service_data`` property with an instance of :class:`ControlDTCSetting.ResponseData<udsoncan.services.ControlDTCSetting.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`

		:raises InvalidResponseException: If length of ``response.data`` is too short
		"""		
		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

		response.service_data = cls.ResponseData()
		response.service_data.setting_type_echo = response.data[0]

	class ResponseData(BaseResponseData):
		"""
		.. data:: setting_type_echo

			Request subfunction echoed back by the server
		"""		
		def __init__(self):
			super().__init__(ControlDTCSetting)
			self.setting_type_echo = None
