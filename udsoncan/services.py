from udsoncan import Response
import inspect
import sys

def cls_from_request_id(given_id):
	return BaseService.from_request_id(given_id)

def cls_from_response_id(given_id):
	return BaseService.from_response_id(given_id)

class BaseService:

	@classmethod	# Returns the service ID used for a client request
	def request_id(cls):
		return cls._sid

	@classmethod	# Returns the service ID used for a server response
	def response_id(cls):
		return cls._sid + 0x40

	# Set the service ID from a server Response payload value
	def set_id_from_response_payload(self, payload):
		if not payload or len(payload) == 0:
			raise ValueError("Response is empty")
		_sid = payload[0] - 0x40

	@classmethod	# Returns an instance of the service identified by the service ID (Request)
	def from_request_id(cls, given_id):
		for name, obj in inspect.getmembers(sys.modules[__name__]):
			if hasattr(obj, "__bases__") and cls in obj.__bases__:
				if obj.request_id() == given_id:
					return obj

	@classmethod	# Returns an instance of the service identified by the service ID (Response)
	def from_response_id(cls, given_id):
		for name, obj in inspect.getmembers(sys.modules[__name__]):
			if hasattr(obj, "__bases__") and cls in obj.__bases__:
				if obj.response_id() == given_id:
					return obj

	#Default subfunction ID for service that does not implements subfunction_id().
	def subfunction_id(self):
		return 0

	@classmethod	# Tells if this service include a subfunction byte
	def use_subfunction(cls):
		if hasattr(cls, '_use_subfunction'):
			return cls._use_subfunction
		else:
			return True
	
	@classmethod	# Tells if this service positive response is different from the single byte 0 Response Code
	def has_custom_positive_response(cls):
		if hasattr(cls, '_custom_positive_response'):
			return cls._custom_positive_response
		else:
			return False

	@classmethod	# Returns the service name. Shortcut that works on class and instances
	def get_name(cls):
		return cls.__name__

	@classmethod	# Tells if the given response code is expected for this service according to UDS standard.
	def is_supported_negative_response(cls, code):
		return code in cls.supported_negative_response

def is_valid_service(service_cls):
	return issubclass(service_cls, BaseService)

class DiagnosticSessionControl(BaseService):
	_sid = 0x10
	_custom_positive_response = True

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
									Response.Code.IncorrectMessageLegthOrInvalidFormat,
									Response.Code.ConditionsNotCorrect
									]

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

class ECUReset(BaseService):
	_sid = 0x11
	_custom_positive_response = True

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
								Response.Code.IncorrectMessageLegthOrInvalidFormat,
								Response.Code.ConditionsNotCorrect,
								Response.Code.SecurityAccessDenied
								]

	hardReset = 1
	keyOffOnReset = 2
	softReset = 3
	enableRapidPowerShutDown = 4
	disableRapidPowerShutDown = 5

	def __init__(self, resettype=None, powerdowntime=None):
		if not isinstance(resettype, int):
			raise ValueError('Reset type must be a integer')
		if resettype < 0 or resettype > 0xFF:
			raise ValueError('Reset type must be a value between 0 and 0x7F')

		if resettype == self.enableRapidPowerShutDown:
			if powerdowntime is None:
				raise ValueError('Power down time must be provided for reset of type enableRapidPowerShutDown')
			
			if not isinstance(powerdowntime, int) or powerdowntime < 0 or powerdowntime > 0xFF:
				raise ValueError('Power down time must be an integer between 0 and 0xFF')
		
		self.resettype = resettype
		self.powerdowntime = powerdowntime

	def subfunction_id(self):
		return self.resettype

class SecurityAccess(BaseService):
	_sid = 0x27

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange,
							Response.Code.InvalidKey,
							Response.Code.ExceedNumberOfAttempts,
							Response.Code.RequiredTimeDelayNotExpired
							]

	class Mode:
		RequestSeed=0
		SendKey=1

	def __init__(self, level, mode=Mode.RequestSeed):
		if mode not in [SecurityAccess.Mode.RequestSeed, SecurityAccess.Mode.SendKey]:
			raise ValueError("Given mode must be either RequestSeed or Send Key ")
		level = int(level)
		if level > 0x7F or level <= 0:
			raise ValueError("Level must be a valid integer between 0 and 0x7F")

		self.level = level
		self.mode = mode

	def subfunction_id(self):
		if self.mode == SecurityAccess.Mode.RequestSeed:
			return (self.level & 0xFE) +1
		elif self.mode == SecurityAccess.Mode.SendKey:
			return (self.level +1) & 0xFE
		else:
			raise ValueError("Cannot generate subfunction ID. Mode is invalid")

class CommunicationControl(BaseService):
	_sid = 0x28
	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]
	def __init__(self):
		pass

class TesterPresent(BaseService):
	_sid = 0x3E

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat
							]

class AccessTimingParameter(BaseService):
	_sid = 0x83

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]	
	def __init__(self):
		pass

class SecuredDataTransmission(BaseService):
	_sid = 0x84

	class Code:
		GeneralSecurityViolation 			= Response.Code.GeneralSecurityViolation			- 0x38
		SecuredModeRequested 				= Response.Code.SecuredModeRequested				- 0x38
		InsufficientProtection 				= Response.Code.InsufficientProtection				- 0x38
		TerminationWithSignatureRequested 	= Response.Code.TerminationWithSignatureRequested	- 0x38
		AccessDenied 						= Response.Code.AccessDenied						- 0x38
		VersionNotSupported 				= Response.Code.VersionNotSupported					- 0x38
		SecuredLinkNotSupported 			= Response.Code.SecuredLinkNotSupported				- 0x38
		CertificateNotAvailable 			= Response.Code.CertificateNotAvailable				- 0x38
		AuditTrailInformationNotAvailable 	= Response.Code.AuditTrailInformationNotAvailable	- 0x38

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.GeneralSecurityViolation,
							Response.Code.SecuredModeRequested,
							Response.Code.InsufficientProtection,
							Response.Code.TerminationWithSignatureRequested,
							Response.Code.AccessDenied,
							Response.Code.VersionNotSupported,
							Response.Code.SecuredLinkNotSupported,
							Response.Code.CertificateNotAvailable,
							Response.Code.AuditTrailInformationNotAvailable
							]

	def __init__(self):
		pass

class ControlDTCSetting(BaseService):
	_sid = 0x85

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]

	def __init__(self):
		pass

class ResponseOnEvent(BaseService):
	_sid = 0x86

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]

	def __init__(self):
		pass

class LinkControl(BaseService):
	_sid = 0x87

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange
							]

	def __init__(self):
		pass

def assert_dids_value(dids):
	if not isinstance(dids, int) and not isinstance(dids, list):
		raise ValueError("Data Identifier must either be an integer or a list of integer")

	if isinstance(dids, int):
		if dids < 0 or dids > 0xFFFF:
			raise ValueError("Data Identifier must be set between 0 and 0xFFFF")
	if isinstance(dids, list):
		for did in dids:
			if not isinstance(did, int) or did < 0 or did > 0xFFFF:
				raise ValueError("Data Identifier must be set between 0 and 0xFFFF")

class ReadDataByIdentifier(BaseService):
	_sid = 0x22
	_use_subfunction = False
	_custom_positive_response = True


	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]	

	def __init__(self, dids):
		assert_dids_value(dids)

		self.dids = dids

class WriteDataByIdentifier(BaseService):
	_sid = 0x2E
	_use_subfunction = False
	_custom_positive_response = True

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	def __init__(self, did):
		if not isinstance(did, int):
			raise ValueError('Data Identifier must be an integer value')
		assert_dids_value(did)
		self.did = did

class ReadMemoryByAddress(BaseService):
	_sid = 0x23

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self):
		pass

class ReadScalingDataByIdentifier(BaseService):
	_sid = 0x24

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self):
		pass

class ReadDataByPeriodicIdentifier(BaseService):
	_sid = 0x2A

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self):
		pass

class DynamicallyDefineDataIdentifier(BaseService):
	_sid = 0x2C

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self):
		pass

class WriteMemoryByAddress(BaseService):
	_sid = 0x3D

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	def __init__(self):
		pass

class ClearDiagnosticInformation(BaseService):
	_sid = 0x14

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]

	def __init__(self):
		pass

class ReadDTCInformation(BaseService):
	_sid = 0x19

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestOutOfRange
							]

	def __init__(self):
		pass

class InputOutputControlByIdentifier(BaseService):
	_sid = 0x2F

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self):
		pass

class RoutineControl(BaseService):
	_sid = 0x31

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestSequenceError,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.GeneralProgrammingFailure
							]

	def __init__(self):
		pass

class RequestDownload(BaseService):
	_sid = 0x34

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.UploadDownloadNotAccepted
							]

	def __init__(self):
		pass

class RequestUpload(BaseService):
	_sid = 0x35

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied,
							Response.Code.UploadDownloadNotAccepted
							]

	def __init__(self):
		pass

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

	def __init__(self):
		pass

class RequestTransferExit(BaseService):
	_sid = 0x37

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestSequenceError
							]

	def __init__(self):
		pass
