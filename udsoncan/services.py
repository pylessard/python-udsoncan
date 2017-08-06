from udsoncan.sessions import Session

class BaseService:

	@classmethod	
	def request_id(cls):
		return cls._sid

	@classmethod	
	def response_id(cls):
		return cls._sid + 0x40

	def make_payload(self):
		return b""

class ZeroSubFunction:
	id = 0

class DiagnosticSessionControl(BaseService):
	_sid = 0x10
	def __init__(self, session):
		if isinstance(session, int):
			session = Session.from_id(session)
		
		if not issubclass(session, Session):
			raise ValueError("Given parameter is not a valid Session type")

		self.session = session

	@property
	def subfunction_id(self):
		return self.session.id



class ECUReset(BaseService):
	_sid = 0x01
	def __init__(self):
		pass

class SecurityAccess(BaseService):
	_sid = 0x27
	def __init__(self):
		pass

class CommunicationControl(BaseService):
	_sid = 0x28
	def __init__(self):
		pass

class TesterPresent(BaseService):
	_sid = 0x3E
	def __init__(self):
		pass

class AccessTimingParameter(BaseService):
	_sid = 0x83
	def __init__(self):
		pass

class SecuredDataTransmission(BaseService):
	_sid = 0x84
	def __init__(self):
		pass

class ControlDTCSetting(BaseService):
	_sid = 0x85
	def __init__(self):
		pass

class ResponseOnEvent(BaseService):
	_sid = 0x86
	def __init__(self):
		pass

class LinkControl(BaseService):
	_sid = 0x87
	def __init__(self):
		pass

class ReadDataByIdentifier(BaseService):
	_sid = 0x22
	def __init__(self):
		pass

class ReadMemoryByAddress(BaseService):
	_sid = 0x23
	def __init__(self):
		pass

class ReadScalingDataByIdentifier(BaseService):
	_sid = 0x24
	def __init__(self):
		pass

class ReadDataByPeriodicIdentifier(BaseService):
	_sid = 0x2A
	def __init__(self):
		pass

class DynamicallyDefineDataIdentifier(BaseService):
	_sid = 0x2C
	def __init__(self):
		pass

class WriteDataByIdentifier(BaseService):
	_sid = 0x2E
	def __init__(self):
		pass

class WriteMemoryByAddress(BaseService):
	_sid = 0x3D
	def __init__(self):
		pass

class ClearDiagnosticInformation(BaseService):
	_sid = 0x14
	def __init__(self):
		pass

class ReadDTCInformation(BaseService):
	_sid = 0x19
	def __init__(self):
		pass

class InputOutputControlByIdentifier(BaseService):
	_sid = 0x2F
	def __init__(self):
		pass

class RoutineControl(BaseService):
	_sid = 0x31
	def __init__(self):
		pass

class RequestDownload(BaseService):
	_sid = 0x34
	def __init__(self):
		pass

class RequestUpload(BaseService):
	_sid = 0x35
	def __init__(self):
		pass

class TransferData(BaseService):
	_sid = 0x36
	def __init__(self):
		pass

class RequestTransferExit(BaseService):
	_sid = 0x37
	def __init__(self):
		pass
