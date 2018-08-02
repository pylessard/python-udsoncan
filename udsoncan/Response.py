import inspect
import struct

class Response:
	"""
	Represents a server Response to a client Request

	:param service: The service implied by this response.
	:type service: class

	:param code: The response code
	:type code: int

	:param data: The response data encoded after the service and response code
	:type data: bytes

	.. data:: valid 

		(boolean) True if the response content is valid. Only ``invalid_reason`` is guaranteed to have a meaningful value if this value is False

	.. data:: invalid_reason 
	
		(string) String explaining why the response is invalid.
	
	.. data:: service 

		(class) The response target :ref:`service<Services>` class

	.. data:: positive 

		(boolean) True if the response code is 0 (PositiveResponse), False otherwise

	.. data:: code 

		(int) The response code. 

	.. data:: code_name 

		(string) The response code name.
	

	.. data:: data
		
		(bytes) The response data. All the payload content, except the service number and the response code
	

	.. data:: service_data

		(object) The content of ``data`` interpreted by a service; can be any type of content.
		

	.. data:: original_payload 
		
		(bytes) When the response is built with `Response.from_payload`, this property contains a copy of the payload used. None otherwise.

	.. data:: unexpected 

		(boolean) Indicates that the response was unexpected. Set by an external source such as the :ref:`Client<Client>` object

	"""
	class Code:
		PositiveResponse = 0
		GeneralReject = 0x10
		ServiceNotSupported = 0x11
		SubFunctionNotSupported = 0x12
		IncorrectMessageLegthOrInvalidFormat = 0x13
		ResponseTooLong = 0x14
		BusyRepeatRequest = 0x21
		ConditionsNotCorrect = 0x22
		RequestSequenceError = 0x24
		NoResponseFromSubnetComponent = 0x25
		FailurePreventsExecutionOfRequestedAction = 0x26
		RequestOutOfRange = 0x31
		SecurityAccessDenied = 0x33
		InvalidKey = 0x35
		ExceedNumberOfAttempts = 0x36
		RequiredTimeDelayNotExpired = 0x37
		UploadDownloadNotAccepted = 0x70
		TransferDataSuspended = 0x71
		GeneralProgrammingFailure = 0x72
		WrongBlockSequenceCounter = 0x73
		RequestCorrectlyReceived_ResponsePending = 0x78
		SubFunctionNotSupportedInActiveSession = 0x7E
		ServiceNotSupportedInActiveSession = 0x7F
		RpmTooHigh = 0x81
		RpmTooLow = 0x82
		EngineIsRunning = 0x83
		EngineIsNotRunning = 0x84
		EngineRunTimeTooLow = 0x85
		TemperatureTooHigh = 0x86
		TemperatureTooLow = 0x87
		VehicleSpeedTooHigh = 0x88
		VehicleSpeedTooLow = 0x89
		ThrottlePedalTooHigh = 0x8A
		ThrottlePedalTooLow = 0x8B
		TransmissionRangeNotInNeutral = 0x8C
		TransmissionRangeNotInGear = 0x8D
		ISOSAEReserved = 0x8E
		BrakeSwitchNotClosed = 0x8F
		ShifterLeverNotInPark = 0x90
		TorqueConverterClutchLocked = 0x91
		VoltageTooHigh = 0x92
		VoltageTooLow = 0x93

		#Defined by ISO-15764. Offset of 0x38 is defined within UDS standard (ISO-14229)
		GeneralSecurityViolation 			= 0x38 + 0
		SecuredModeRequested 				= 0x38 + 1
		InsufficientProtection 				= 0x38 + 2
		TerminationWithSignatureRequested 	= 0x38 + 3
		AccessDenied 						= 0x38 + 4
		VersionNotSupported 				= 0x38 + 5
		SecuredLinkNotSupported 			= 0x38 + 6
		CertificateNotAvailable 			= 0x38 + 7
		AuditTrailInformationNotAvailable 	= 0x38 + 8

		#Returns the name of the response code as a string
		@classmethod
		def get_name(cls, given_id):
			if given_id is None:
				return ""

			for member in inspect.getmembers(cls):
				if isinstance(member[1], int):
					if member[1] == given_id:
						return member[0]
			return str(given_id)
		
		#Tells if a code is a negative code
		@classmethod
		def is_negative(cls, given_id):
			if given_id in [None, cls.PositiveResponse]:
				return False

			for member in inspect.getmembers(cls):
				if isinstance(member[1], int):
					if member[1] == given_id:
						return True
			return False	


	def __init__(self, service = None, code = None, data=None):
		from udsoncan import services
		if service is None:
			self.service = None
		elif isinstance(service, services.BaseService):
			self.service = service.__class__
		elif inspect.isclass(service) and issubclass(service, services.BaseService):
			self.service = service
		elif service is not None:
			raise ValueError("Given service must be a service class or instance")

		self.positive = False
		self.code = None
		self.code_name = ""
		self.valid = False
		self.invalid_reason = "Object not initialized"
		self.service_data = None
		self.original_payload = None
		self.unexpected = False
		
		self.service = service

		if data is not None:
			if not isinstance(data, bytes):
				raise ValueError("Given data must be a valid bytes object")

		self.data = data if data is not None else b''

		if code is not None:
			if not isinstance(code, int):
				raise ValueError("Response code must be a valid integer")
			elif code < 0 or code > 0xFF:
				raise ValueError("Response code must be an integer between 0 and 0xFF")
			self.code=code
			self.code_name = Response.Code.get_name(code)
			if not Response.Code.is_negative(code):
				self.positive=True

		if self.service is not None and self.code is not None:
			self.valid = True
			self.invalid_reason = ""

	#Used by server
	def get_payload(self):
		"""
		Generates a payload to be given to the underlying protocol.
		This method is meant to be used by a UDS server

		:return: A payload to be sent through the underlying protocol
		:rtype: bytes
		"""
		from udsoncan import services
		if not isinstance(self.service, services.BaseService) and not issubclass(self.service, services.BaseService):
			raise ValueError("Cannot make payload from response object. Given service is not a valid service object")

		if not isinstance(self.code, int):
			raise ValueError("Cannot make payload from response object. Given response code is not a valid integer")
		
		payload  = b''
		if self.positive:
			payload += struct.pack("B", self.service.response_id())
		else:
			payload += b'\x7F'
			payload += struct.pack("B", self.service.request_id())
			payload += struct.pack('B', self.code)

		if self.data is not None and self.service.has_response_data():
			payload += self.data
		return payload


	# Analyzes a TP frame and builds a Response object. Used by client
	@classmethod
	def from_payload(cls, payload):
		"""
		Creates a ``Response`` object from a payload coming from the underlying protocol.
		This method is meant to be used by a UDS client

		:param payload: The payload of data to parse
		:type payload: bytes

		:return: A :ref:`Response<Response>` object with populated fields
		:rtype: :ref:`Response<Response>`
		"""
		from udsoncan import services
		response = cls()
		response.original_payload = payload # may be useful for debugging

		if len(payload) < 1:
			response.valid = False
			response.invalid_reason = "Payload is empty"
			return response


		if payload[0] != 0x7F:	# Positive
			response.service = services.cls_from_response_id(payload[0])
			if response.service is None:
				response.valid = False
				response.invalid_reason = "Payload first byte is not a know service response ID."
				return response

			data_start=1
			response.positive = True
			if len(payload) < 2 and response.service.has_response_data() :
				response.valid = False
				response.positive = False
				response.invalid_reason = "Payload must be at least 2 bytes long (service and response)"
				return response

			response.code = Response.Code.PositiveResponse
			response.code_name = Response.Code.get_name(Response.Code.PositiveResponse)

		else:	# Negative response
			response.positive = False
			data_start=3
			
			if len(payload) < 2 :
				response.valid = False
				response.invalid_reason=  "Incomplete invalid response service (7Fxx)"	
				return response
			response.service = services.cls_from_request_id(payload[1])	#Request id, not response id
			
			if response.service is None:
				response.valid = False
				response.invalid_reason = "Payload second byte is not a known service request ID."
				return response
			
			if len(payload) < 3:
				response.valid=False
				response.invalid_reason=  "Response code missing"
				return response

			response.code = int(payload[2])
			response.code_name = Response.Code.get_name(response.code)

		response.valid = True
		if len(payload) > data_start:
			response.data = payload[data_start:]
		return response

	def __repr__(self):
		responsename = Response.Code.get_name(Response.Code.PositiveResponse) if self.positive else 'NegativeResponse(%s)' % self.code_name
		bytesize = len(self.data) if self.data is not None else 0
		return '<%s: [%s] - %d data bytes at 0x%08x>' % (responsename, self.service.get_name(), bytesize, id(self))

	def __len__(self):
		try:
			return len(self.get_payload())
		except:
			return 0