from udsoncan.Response import Response
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
				if obj.response_id() == int(given_id):
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
	@classmethod
	def has_response_data(cls):
		if hasattr(cls, '_no_response_data'):
			return False if cls._no_response_data else True
		else:
			return True

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
		if level > 0x7F or level < 0:
			raise ValueError("Level must be a valid integer between 0 and 0x7F")

		self.level = level
		self.mode = mode

	def subfunction_id(self):
		if self.mode == SecurityAccess.Mode.RequestSeed:
			return self.level if self.level % 2 == 1 else self.level-1
		elif self.mode == SecurityAccess.Mode.SendKey:
			return self.level if self.level % 2 == 0 else self.level+1
		else:
			raise ValueError("Cannot generate subfunction ID. Mode is invalid")

class CommunicationControl(BaseService):
	_sid = 0x28

	enableRxAndTx = 0
	enableRxAndDisableTx = 1
	disableRxAndEnableTx = 2
	disableRxAndTx = 3



	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]
	def __init__(self, control_type, communication_type):
		from udsoncan import CommunicationType

		if not isinstance(control_type, int):
			raise ValueError('control_type must be an integer')

		if control_type < 0 or control_type > 0x7F:
			raise ValueError('control_type must be an integer between 0 and 0x7F')

		if not isinstance(communication_type, CommunicationType) and not isinstance(communication_type, int):
			raise ValueError('communication_type must either be a CommunicationType object or an integer')

		if isinstance(communication_type, int):
			communication_type = CommunicationType.from_byte(communication_type)

		self.communication_type = communication_type
		self.control_type = control_type

	def subfunction_id(self):
		return self.control_type

class TesterPresent(BaseService):
	_sid = 0x3E

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat
							]

class AccessTimingParameter(BaseService):
	_sid = 0x83

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

		if request_record is not None and access_type != self.setTimingParametersToGivenValues :
			raise ValueError('request_record can only be set when access_type is setTimingParametersToGivenValues"')

		if request_record is None and access_type == self.setTimingParametersToGivenValues :
			raise ValueError('A request_record must be provided when access_type is "setTimingParametersToGivenValues"')

		if request_record is not None:
			if not isinstance(request_record, bytes):
				raise ValueError("request_record must be a valid bytes objects")

		self.access_type  = access_type
		self.request_record = request_record

	def subfunction_id(self):
		return self.access_type

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
	_use_subfunction = False
	_no_response_data = True

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange
							]

	def __init__(self, group=0xFFFFFF):
		if not isinstance(group, int):
			raise ValueError("Group of DTC must be a valid integer")
		if group < 0 or group > 0xFFFFFF:
			raise ValueError("Group of DTC must be an integer between 0 and 0xFFFFFF")

		self.group = group

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

	#As defined by ISO-14229:2006, Annex E
	returnControlToECU = 0
	resetToDefault = 1
	freezeCurrentState = 2
	shortTermAdjustment = 3

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self):
		pass

class RoutineControl(BaseService):
	_sid = 0x31

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

	def __init__(self, routine_id, control_type):
		if not isinstance(routine_id, int):
			raise ValueError("Routine ID must be a valid integer")
		if routine_id < 0 or routine_id > 0xFFFF:
			raise ValueError("Routine ID  must be an integer between 0 and 0xFFFF")

		if not isinstance(control_type, int):
			raise ValueError("Routine control type must be a valid integer")
		if control_type < 0 or control_type > 0x7F:
			raise ValueError("Routine control type must be an integer between 0 and 0x7F")

		self.routine_id = routine_id
		self.control_type = control_type


	def subfunction_id(self):
		return self.control_type;

class RequestDownload(BaseService):
	_sid = 0x34
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

class RequestTransferExit(BaseService):
	_sid = 0x37
	_use_subfunction = False
	_no_response_data = True

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestSequenceError
							]

	def __init__(self, data=None):
		if data is not None and not isinstance(data, bytes):
			raise ValueError('data must be a bytes object')

		self.data= data
