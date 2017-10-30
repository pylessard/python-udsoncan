import threading
import queue
import inspect
import struct
import time
import errno

from udsoncan.exceptions import *


class Connection(object):
	def __init__(self, interface, rxid, txid, tpsock=None):
		import isotp
		import socket

		self.interface=interface
		self.rxid=rxid
		self.txid=txid
		self.rxqueue = queue.Queue()
		self.exit_requested = False
		self.opened = False

		self.rxthread = threading.Thread(target=self.rxthread_task)
		self.tpsock = isotp.socket(timeout=0.1) if topsock is None else tpsock


	def open(self):
		self.tpsock.bind(self.interface, rxid=self.rxid, txid=self.txid)
		self.exit_requested = False
		self.rxthread.start()
		self.opened = True
		return self

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def is_open(self):
		return self.tpsock.bound

	def rxthread_task(self):
		while not self.exit_requested:
			try:
				data = self.tpsock.recv()
				if data is not None:
					self.rxqueue.put(data)
			except socket.timeout as e:
				pass
			except Exception as e:
				self.exit_requested = True


	def close(self):
		self.exit_requested = True
		self.tpsock.close()
		self.opened = False

	def send(self, obj):
		if isinstance(obj, Request) or isinstance(obj, Response):
			payload = obj.get_payload()  
		else :
			payload = obj

		self.tpsock.send(payload)

	def wait_frame(self, timeout=2, exception=False):
		if not self.opened:
			if exception:
				raise RuntimeException("Connection is not opened")
			else:
				return None

		timedout = False
		frame = None
		try:
			frame = self.rxqueue.get(block=True, timeout=timeout)

		except queue.Empty:
			timedout = True
			
		if exception and timedout:
			raise TimeoutException("Did not received ISOTP frame in time (timeout=%s sec)" % timeout)

		return frame

	def empty_rxqueue(self):
		while not self.rxqueue.empty():
			self.rxqueue.get()

class Request:
	def __init__(self, service = None, subfunction = None, suppress_positive_response = False, data=None):
		if service is None:
			self.service = None
			self.subfunction = None

		elif isinstance(service, services.BaseService):
			self.service = service.__class__
			self.subfunction = service.subfunction_id()	# service instance are able toe generate the subfunction ID
		elif inspect.isclass(service) and issubclass(service, services.BaseService):
			if subfunction is not None:
				if isinstance(subfunction, int):
					self.service = service
					self.subfunction = subfunction
				else:
					raise ValueError("Given subfunction must be a valid integer")
		elif service is not None:
			raise ValueError("Given service must be a service class or instance")

		self.suppress_positive_response = suppress_positive_response
		
		if data is not None and not isinstance(data, str):
			raise ValueError("data must be a valid string")

		self.data = data

	def get_payload(self):
		if not issubclass(self.service, services.BaseService):
			raise ValueError("Cannot generate a payload. Given service is not a subclass of BaseService")

		if self.service.use_subfunction() and not isinstance(self.subfunction, int):
			raise ValueError("Cannot generate a payload. Given subfunction is not a valid integer")

		requestid = self.service.request_id()	# Return the service ID used to make a client request
			

		payload = struct.pack("B", requestid)
		if self.service.use_subfunction():
			subfunction = self.subfunction
			if self.suppress_positive_response:
				subfunction |= 0x80
			payload += struct.pack("B", subfunction)

		if self.data is not None:
			 payload += self.data

		return payload

	@classmethod
	def from_payload(cls, payload):
		req = cls()

		if len(payload) >= 1:
			req.service = services.cls_from_request_id(payload[0])
			if req.service is not None:		# Invalid service ID will make service None
				offset = 0
				if req.service.use_subfunction():
					offset += 1
					if len(payload) >= offset+1: 
						req.subfunction = int(payload[1]) & 0x7F
						req.suppress_positive_response = True if payload[1] & 0x80 > 0 else False
				if len(payload) > offset+1:
					req.data = payload[offset+1:]
		return req

	def __repr__(self):
		suppress_positive_response = '[SuppressPosResponse] ' if self.suppress_positive_response else ''
		subfunction_name = '(subfunction=%d) ' % self.subfunction if self.service.use_subfunction() else ''
		bytesize = len(self.data) if self.data is not None else 0
		return '<Request: [%s] %s- %d data bytes %sat 0x%08x>' % (self.service.get_name(), subfunction_name, bytesize, suppress_positive_response, id(self))

	def __len__(self):
		try:
			return len(self.get_payload())
		except:
			return 0

# Represent a response to a client Request
class Response:
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
		
		self.service = service

		if data is not None:
			if self.service is not None and not self.service.has_response_data():
				raise ValueError("This service should not have any data in its response.")

			if not isinstance(data, bytes):
				raise ValueError("Given data must be a valid bytes object")

		self.data = data

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
		if not isinstance(self.service, services.BaseService) and not issubclass(self.service, services.BaseService):
			raise ValueError("Cannot make payload from response object. Given service is not a valid service object")

		if not isinstance(self.code, int):
			raise ValueError("Cannot make payload from response object. Given response code is not a valid integer")

		payload = struct.pack("B", self.service.response_id())
		if not self.positive:
			payload += b'\x7F'
		if not self.positive:
			payload += struct.pack('B', self.code)

		if self.data is not None and self.service.has_response_data():
			payload += self.data
		return payload


	# Analyze a TP frame an build a Response object. Used by client
	@classmethod
	def from_payload(cls, payload):
		response = cls()
		if len(payload) >= 1:
			response.service = services.cls_from_response_id(payload[0])
			if response.service is None:
				response.valid = False
				response.invalid_reason = "Payload first byte is not a know service."

			elif len(payload) >= 2 :
				if payload[1] != 0x7F:
					data_start=1
					response.valid = True
					response.code = Response.Code.PositiveResponse
					response.code_name = Response.Code.get_name(Response.Code.PositiveResponse)
					response.positive = True
				else:
					data_start=3
					response.positive = False
					if len(payload) >= 3:
						response.code = payload[2]
						response.code_name = Response.Code.get_name(response.code)
						response.valid = True
					else:
						response.valid = False
						response.invalid_reason=  "Incomplete invalid response code (7Fxx)"
				
				if len(payload) > data_start:
					response.data = payload[data_start:]
			else:
				if response.service.has_response_data():
					response.valid = False
					response.invalid_reason = "Payload must be at least 2 bytes long (service and response)"
				else:
					response.valid = True
					response.code = Response.Code.PositiveResponse
					response.code_name = Response.Code.get_name(Response.Code.PositiveResponse)
					response.positive = True
		else:
			response.valid = False
			response.invalid_reason = "Payload must be at least 2 bytes long (service and response)"
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

#Define how to encode/decode a Data Identifier value to/from abinary payload
class DidCodec:

	def __init__(self, packstr=None):
		self.packstr = packstr

	def encode(self, did_value):
		if self.packstr is None:
			raise NotImplementedError('Cannot encode DID to binary payload. Codec has no "encode" implementation')

		return struct.pack(self.packstr, did_value)

	def decode(self, did_payload):
		if self.packstr is None:
			raise NotImplementedError('Cannot decode DID from binary payload. Codec has no "decode" implementation')

		return struct.unpack(self.packstr, did_payload)

	#Must tells the size of the payload encoded or expected for decoding
	def __len__(self):
		if self.packstr is None:
			raise NotImplementedError('Cannot tell the payload size. Codec has no "__len__" implementation')
		return struct.calcsize(self.packstr)

	@classmethod
	def from_config(cls, didconfig):
		if isinstance(didconfig, cls):
			return didconfig

		if inspect.isclass(didconfig) and issubclass(didconfig, cls):
			return didconfig()

		if isinstance(didconfig, str):
			return cls(packstr = didconfig)

class SecurityLevel(object):
	def __init__(self, levelid):
		self.levelid = levelid & 0xFE

class Dtc:
	class Severity:
		NotAvailable = 0
		MaintenanceOnly = 1
		CheckAtNextHalt = 2
		CheckImmediately = 4


	def __init__(self, dtc):

		self.id = dtcid

		self.testFailed = False
		self.testFailedThisOperationCycle = False
		self.pending = False
		self.confirmed = False
		self.testNotCompletedSinceLastClear = False
		self.testFailedSinceLastClear = False
		self.testNotCompletedThisOperationCycle = False
		self.warningIndicatorRequested = False

	def updateStatus(testFailed = None, testFailedThisOperationCycle = None, pending = None, confirmed = None, testNotCompletedSinceLastClear  = None, testFailedSinceLastClear = None, warningIndicatorRequested = None):
		if testFailed is not None:
			self.testFailed	=  testFailed

		if testFailedThisOperationCycle is not None:
			self.testFailedThisOperationCycle	= testFailedThisOperationCycle

		if pending is not None:
			self.pending	= pending

		if confirmed is not None:
			self.confirmed	= confirmed

		if testNotCompletedSinceLastClear is not None:
			self.testNotCompletedSinceLastClear	= testNotCompletedSinceLastClear

		if testFailedSinceLastClear is not None:
			self.testFailedSinceLastClear	= testFailedSinceLastClear

		if testNotCompletedThisOperationCycle is not None:
			self.testNotCompletedThisOperationCycle	= testNotCompletedThisOperationCycle

		if warningIndicatorRequested is not None:
			self.warningIndicatorRequested	= warningIndicatorRequested

	@property
	def status(self):
		byte = 0
		byte |= 0x1 if self.testFailed else 0
		byte |= 0x2 if self.testFailedThisOperationCycle else 0
		byte |= 0x4 if self.pending else 0
		byte |= 0x8 if self.confirmed else 0
		byte |= 0x10 if self.testNotCompletedSinceLastClear else 0
		byte |= 0x20 if self.testFailedSinceLastClear else 0
		byte |= 0x40 if self.testNotCompletedThisOperationCycle else 0
		byte |= 0x80 if self.warningIndicatorRequested else 0

	@status.setter
	def status(self, byte):
		self.testFailed 						= True if byte & 0x01 > 0 else False
		self.testFailedThisOperationCycle 		= True if byte & 0x02 > 0 else False
		self.pending 							= True if byte & 0x04 > 0 else False
		self.confirmed 							= True if byte & 0x08 > 0 else False
		self.testNotCompletedSinceLastClear 	= True if byte & 0x10 > 0 else False
		self.testFailedSinceLastClear 			= True if byte & 0x20 > 0 else False
		self.testNotCompletedThisOperationCycle = True if byte & 0x40 > 0 else False
		self.warningIndicatorRequested 			= True if byte & 0x80 > 0 else False

class AddressAndLengthIdentifier:
	#As defined by ISO-14229:2006, Annex G
	addr_256B = 1
	addr_64KB = 2
	addr_16MB = 3
	addr_4GB = 4
	addr_1024GB = 5

	msize_256 = 1
	msize_64KB = 2
	msize_16MB = 3
	msize_4GB = 4


	@classmethod
	def make(cls, size, addr):
		if not isinstance(size, int) or not isinstance(addr, int):
			raise ValueError('Size and addr must be integers')

		if size < 1 or size > 4:
			raise ValueError('Size must ba an integer between 1 and 4')
		
		if addr < 1 or addr > 5:
			raise ValueError('Addr must ba an integer between 1 and 5')

		return  (size << 4) | (addr)

class Units:
	#As defined in ISO-14229:2006 Annex C
	class Prefixs:
		class Prefix:
			def __init__(self, id, name, symbol, description=None):
				self.name = name
				self.id = id
				self.symbol = symbol
				self.description = description
		exa		= Prefix(id=0x40, name= 'exa', symbol='E', description='10e18')
		peta	= Prefix(id=0x41, name= 'peta', symbol='P', description='10e15')
		tera	= Prefix(id=0x42, name= 'tera', symbol='T', description='10e12')
		giga	= Prefix(id=0x43, name= 'giga', symbol='G', description='10e9')
		mega	= Prefix(id=0x44, name= 'mega', symbol='M', description='10e6')
		kilo	= Prefix(id=0x45, name= 'kilo', symbol='k', description='10e3')
		hecto	= Prefix(id=0x46, name= 'hecto', symbol='h', description='10e2')
		deca	= Prefix(id=0x47, name= 'deca', symbol='da', description='10e1')
		deci	= Prefix(id=0x48, name= 'deci', symbol='d', description='10e-1')
		centi	= Prefix(id=0x49, name= 'centi', symbol='c', description='10e-2')
		milli	= Prefix(id=0x4A, name= 'milli', symbol='m', description='10e-3')
		micro	= Prefix(id=0x4B, name= 'micro', symbol='m', description='10e-6')
		nano	= Prefix(id=0x4C, name= 'nano', symbol='n', description='10e-9')
		pico	= Prefix(id=0x4D, name= 'pico', symbol='p', description='10e-12')
		femto	= Prefix(id=0x4E, name= 'femto', symbol='f', description='10e-15')
		atto	= Prefix(id=0x4F, name= 'atto', symbol='a', description='10e-18')

	class Unit:
		def __init__(self, id, name, symbol, description=None):
			self.id =id
			self.name = name
			self.symbol = symbol
			self.description = description
	no_unit 			= Unit(id=0x00, name= 'no unit', 					symbol='-', 		description='-')
	meter 				= Unit(id=0x01, name= 'meter', 						symbol='m', 		description='length')
	foor 				= Unit(id=0x02, name= 'foot', 						symbol='ft', 		description='length')
	inch				= Unit(id=0x03, name= 'inch', 						symbol='in', 		description='length')
	yard				= Unit(id=0x04, name= 'yard', 						symbol='yd', 		description='length')
	english_mile		= Unit(id=0x05, name= 'mile (English)',				symbol='mi', 		description='length')
	gram				= Unit(id=0x06, name= 'gram', 						symbol='g', 		description='mass')
	metric_ton			= Unit(id=0x07, name= 'ton (metric)', 				symbol='t', 		description='mass')
	second				= Unit(id=0x08, name= 'second', 					symbol='s', 		description='time')
	minute				= Unit(id=0x09, name= 'minute', 					symbol='min', 		description='time')
	hour				= Unit(id=0x0A, name= 'hour', 						symbol='h', 		description='time')
	day					= Unit(id=0x0B, name= 'day', 						symbol='d', 		description='time')
	year				= Unit(id=0x0C, name= 'year', 						symbol='y', 		description='time')
	ampere				= Unit(id=0x0D, name= 'ampere', 					symbol='A', 		description='current')
	volt				= Unit(id=0x0E, name= 'volt', 						symbol='V', 		description='voltage')
	coulomb				= Unit(id=0x0F, name= 'coulomb', 					symbol='C', 		description='electric charge')
	ohm					= Unit(id=0x10, name= 'ohm', 						symbol='W', 		description='resistance')
	farad				= Unit(id=0x11, name= 'farad', 						symbol='F', 		description='capacitance')
	henry				= Unit(id=0x12, name= 'henry', 						symbol='H', 		description='inductance')
	siemens				= Unit(id=0x13, name= 'siemens', 					symbol='S', 		description='electric conductance')
	weber				= Unit(id=0x14, name= 'weber', 						symbol='Wb', 		description='magnetic flux')
	tesla				= Unit(id=0x15, name= 'tesla', 						symbol='T', 		description='magnetic flux density')
	kelvin				= Unit(id=0x16, name= 'kelvin', 					symbol='K', 		description='thermodynamic temperature')
	Celsius				= Unit(id=0x17, name= 'Celsius', 					symbol='°C', 		description='thermodynamic temperature')
	Fahrenheit			= Unit(id=0x18, name= 'Fahrenheit', 				symbol='°F', 		description='thermodynamic temperature')
	candela				= Unit(id=0x19, name= 'candela', 					symbol='cd', 		description='luminous intensity')
	radian				= Unit(id=0x1A, name= 'radian', 					symbol='rad', 		description='plane angle')
	degree				= Unit(id=0x1B, name= 'degree', 					symbol='°', 		description='plane angle')
	hertz				= Unit(id=0x1C, name= 'hertz', 						symbol='Hz', 		description='frequency')
	joule				= Unit(id=0x1D, name= 'joule', 						symbol='J', 		description='energy')
	Newton				= Unit(id=0x1E, name= 'Newton', 					symbol='N', 		description='force')
	kilopond			= Unit(id=0x1F, name= 'kilopond', 					symbol='kp', 		description='force')
	pound				= Unit(id=0x20, name= 'pound force', 				symbol='lbf', 		description='force')
	watt				= Unit(id=0x21, name= 'watt', 						symbol='W', 		description='power')
	horse				= Unit(id=0x22, name= 'horse power (metric)', 		symbol='hk', 		description='power')
	horse				= Unit(id=0x23, name= 'horse power(UK and US)', 	symbol='hp', 		description='power')
	Pascal				= Unit(id=0x24, name= 'Pascal', 					symbol='Pa', 		description='pressure')
	bar					= Unit(id=0x25, name= 'bar', 						symbol='bar', 		description='pressure')
	atmosphere			= Unit(id=0x26, name= 'atmosphere', 				symbol='atm', 		description='pressure')
	pound				= Unit(id=0x27, name= 'pound', 						symbol='force', 	description='per square inch psi pressure')
	becqerel			= Unit(id=0x28, name= 'becqerel', 					symbol='Bq', 		description='radioactivity')
	lumen				= Unit(id=0x29, name= 'lumen', 						symbol='lm', 		description='light flux')
	lux					= Unit(id=0x2A, name= 'lux', 						symbol='lx', 		description='illuminance')
	liter				= Unit(id=0x2B, name= 'liter', 						symbol='l', 		description='volume')
	gallon				= Unit(id=0x2C, name= 'gallon (British)', 			symbol='-', 		description='volume')
	gallon				= Unit(id=0x2D, name= 'gallon (US liq)', 			symbol='-', 		description='volume')
	cubic				= Unit(id=0x2E, name= 'cubic inch', 				symbol='cu in', 	description='volume')
	meter_per_sec		= Unit(id=0x2F, name= 'meter per seconds', 			symbol='m/s', 		description='speed')
	kmh					= Unit(id=0x30, name= 'kilometre per hour',			symbol='km/h', 		description='speed')
	mph					= Unit(id=0x31, name= 'mile per hour', 				symbol='mph', 		description='speed')
	rps					= Unit(id=0x32, name= 'revolutions per second', 	symbol='rps', 		description='angular velocity')
	rpm					= Unit(id=0x33, name= 'revolutions per minute', 	symbol='rpm', 		description='angular velocity')
	counts				= Unit(id=0x34, name= 'counts', 					symbol='-', 		description='-')
	percent				= Unit(id=0x35, name= 'percent', 					symbol='%', 		description='-')
	mg_per_stroke		= Unit(id=0x36, name= 'milligram per stroke', 		symbol='mg/stroke', description='mass per engine stroke')
	meter_per_sec2		= Unit(id=0x37, name= 'meter per square seconds', 	symbol='m/s2', 		description='acceleration')
	Nm					= Unit(id=0x38, name= 'Newton meter', 				symbol='Nm', 		description='moment')
	liter_per_min		= Unit(id=0x39, name= 'liter per minute', 			symbol='l/min', 	description='flow')
	watt_per_meter2		= Unit(id=0x3A, name= 'watt per square meter', 		symbol='W/m2', 		description='intensity')
	bar_per_sec			= Unit(id=0x3B, name= 'bar per second', 			symbol='bar/s', 	description='pressure change')
	radians_per_sec		= Unit(id=0x3C, name= 'radians per second', 		symbol='rad/s', 	description='angular velocity')
	radians				= Unit(id=0x3D, name= 'radians', 					symbol='per', 		description='square second rad/s2 angular acceleration')
	kilogram_per_meter2	= Unit(id=0x3E, name= 'kilogram per square meter', 	symbol='kg/m2', 	description='-')
	date1 				= Unit(id=0x50, name='Date1', 						symbol='-', 		description = 'Year-Month-Day')
	date2 				= Unit(id=0x51, name='Date2', 						symbol='-', 		description = 'Day/Month/Year')
	date3 				= Unit(id=0x52, name='Date3', 						symbol='-', 		description = 'Month/Day/Year')
	week 				= Unit(id=0x53, name='week', 						symbol='W', 		description = 'calendar week')
	time1 				= Unit(id=0x54, name='Time1', 						symbol='-', 		description = 'UTC Hour/Minute/Second')
	time2 				= Unit(id=0x55, name='Time2', 						symbol='-', 		description = 'Hour/Minute/Second')
	datetime1 			= Unit(id=0x56, name='DateAndTime1', 				symbol='-', 		description = 'Second/Minute/Hour/Day/Month/Year')
	datetime2 			= Unit(id=0x57, name='DateAndTime2', 				symbol='-', 		description = 'Second/Minute/Hour/Day/Month/Year/Local minute offset/Localhour offset')
	datetime3 			= Unit(id=0x58, name='DateAndTime3', 				symbol='-', 		description = 'Second/Minute/Hour/Month/Day/Year')
	datetime4 			= Unit(id=0x59, name='DateAndTime4', 				symbol='-', 		description = 'Second/Minute/Hour/Month/Day/Year/Local minute offset/Localhour offset')


class Routine:
	DeployLoopRoutineID	= 0xE200
	EraseMemory	= 0xFF00
	CheckProgrammingDependencies = 0xFF01
	EraseMirrorMemoryDTCs = 0xFF02

	@classmethod
	def name_from_id(cls, routine_id):
		#As defined by ISO-14229:2006, Annex F
		if not isinstance(routine_id, int) or routine_id < 0 or routine_id > 0xFFFF:
			raise ValueError('Routine ID must be a valid integer between 0 and 0xFFFF')

		if routine_id >= 0x0000 and routine_id <= 0x00FF:
			return 'ISOSAEReserved'
		if routine_id >= 0x0100 and routine_id <= 0x01FF:
			return 'TachographTestIds'
		if routine_id >= 0x0200 and routine_id <= 0xDFFF:
			return 'VehicleManufacturerSpecific'
		if routine_id >= 0xE000 and routine_id <= 0xE1FF:
			return 'OBDTestIds'
		if routine_id == 0xE200:
			return 'DeployLoopRoutineID'
		if routine_id >= 0xE201 and routine_id <= 0xE2FF:
			return 'SafetySystemRoutineIDs'
		if routine_id >= 0xE300 and routine_id <= 0xEFFF:
			return 'ISOSAEReserved'
		if routine_id >= 0xF000 and routine_id <= 0xFEFF:
			return 'SystemSupplierSpecific'
		if routine_id == 0xFF00:
			return 'EraseMemory'
		if routine_id == 0xFF01:
			return 'CheckProgrammingDependencies'
		if routine_id == 0xFF02:
			return 'EraseMirrorMemoryDTCs'
		if routine_id >= 0xFF03 and routine_id <= 0xFFFF:
			return 'ISOSAEReserved'

class DataIdentifier:
	BootSoftwareIdentification					= 0xF180
	ApplicationSoftwareIdentification			= 0xF181
	ApplicationDataIdentification				= 0xF182
	BootSoftwareFingerprint						= 0xF183
	ApplicationSoftwareFingerprint				= 0xF184
	ApplicationDataFingerprint					= 0xF185
	ActiveDiagnosticSession						= 0xF186
	VehicleManufacturerSparePartNumber			= 0xF187
	VehicleManufacturerECUSoftwareNumber		= 0xF188
	VehicleManufacturerECUSoftwareNumber		= 0xF188
	VehicleManufacturerECUSoftwareVersionNumber	= 0xF189
	SystemSupplierIdentifier					= 0xF18A
	ECUManufacturingDate						= 0xF18B
	ECUSerialNumber								= 0xF18C
	SupportedFunctionalUnits					= 0xF18D
	VehicleManufacturerKitAssemblyPartNumber	= 0xF18E
	ISOSAEReservedStandardized					= 0xF18F
	VIN											= 0xF190
	VehicleManufacturerECUHardwareNumber		= 0xF191
	SystemSupplierECUHardwareNumber				= 0xF192
	SystemSupplierECUHardwareVersionNumber		= 0xF193
	SystemSupplierECUSoftwareNumber				= 0xF194
	SystemSupplierECUSoftwareVersionNumber		= 0xF195
	ExhaustRegulationOrTypeApprovalNumber		= 0xF196
	SystemNameOrEngineType						= 0xF197
	RepairShopCodeOrTesterSerialNumber			= 0xF198
	ProgrammingDate								= 0xF199
	CalibrationRepairShopCodeOrCalibrationEquipmentSerialNumber	= 0xF19A
	CalibrationDate								= 0xF19B
	CalibrationEquipmentSoftwareNumber			= 0xF19C
	ECUInstallationDate							= 0xF19D
	ODXFile										= 0xF19E
	Entity										= 0xF19F

	@classmethod
	def name_from_id(cls, did):
		#As defined by ISO-14229:2006, Annex F
		if not isinstance(did, int) or did < 0 or did > 0xFFFF:
			raise ValueError('Data IDentifier must be a valid integer between 0 and 0xFFFF')

		if did >= 0x0000 and did <= 0x00FF:
			return 'ISOSAEReserved'
		if did >= 0x0100 and did <= 0xEFFF:
			return 'VehicleManufacturerSpecific'
		if did >= 0xF000 and did <= 0xF00F:
			return 'NetworkConfigurationDataForTractorTrailerApplicationDataIdentifier'
		if did >= 0xF010 and did <= 0xF0FF:
			return 'VehicleManufacturerSpecific'
		if did >= 0xF100 and did <= 0xF17F:
			return 'IdentificationOptionVehicleManufacturerSpecificDataIdentifier'

		if did == 0xF180:
			return 'BootSoftwareIdentificationDataIdentifier'
		if did == 0xF181:
			return 'ApplicationSoftwareIdentificationDataIdentifier'
		if did == 0xF182:
			return 'ApplicationDataIdentificationDataIdentifier'
		if did == 0xF183:
			return 'BootSoftwareFingerprintDataIdentifier'
		if did == 0xF184:
			return 'ApplicationSoftwareFingerprintDataIdentifier'
		if did == 0xF185:
			return 'ApplicationDataFingerprintDataIdentifier'
		if did == 0xF186:
			return 'ActiveDiagnosticSessionDataIdentifier'
		if did == 0xF187:
			return 'VehicleManufacturerSparePartNumberDataIdentifier'
		if did == 0xF188:
			return 'VehicleManufacturerECUSoftwareNumberDataIdentifier'
		if did == 0xF188:
			return 'VehicleManufacturerECUSoftwareNumberDataIdentifier'
		if did == 0xF189:
			return 'VehicleManufacturerECUSoftwareVersionNumberDataIdentifier'
		if did == 0xF18A:
			return 'SystemSupplierIdentifierDataIdentifier'
		if did == 0xF18B:
			return 'ECUManufacturingDateDataIdentifier'
		if did == 0xF18C:
			return 'ECUSerialNumberDataIdentifier'
		if did == 0xF18D:
			return 'SupportedFunctionalUnitsDataIdentifier'
		if did == 0xF18E:
			return 'VehicleManufacturerKitAssemblyPartNumberDataIdentifier'
		if did == 0xF18F:
			return 'ISOSAEReservedStandardized'
		if did == 0xF190:
			return 'VINDataIdentifier'
		if did == 0xF191:
			return 'VehicleManufacturerECUHardwareNumberDataIdentifier'
		if did == 0xF192:
			return 'SystemSupplierECUHardwareNumberDataIdentifier'
		if did == 0xF193:
			return 'SystemSupplierECUHardwareVersionNumberDataIdentifier'
		if did == 0xF194:
			return 'SystemSupplierECUSoftwareNumberDataIdentifier'
		if did == 0xF195:
			return 'SystemSupplierECUSoftwareVersionNumberDataIdentifier'
		if did == 0xF196:
			return 'ExhaustRegulationOrTypeApprovalNumberDataIdentifier'
		if did == 0xF197:
			return 'SystemNameOrEngineTypeDataIdentifier'
		if did == 0xF198:
			return 'RepairShopCodeOrTesterSerialNumberDataIdentifier'
		if did == 0xF199:
			return 'ProgrammingDateDataIdentifier'
		if did == 0xF19A:
			return 'CalibrationRepairShopCodeOrCalibrationEquipmentSerialNumberDataIdentifier'
		if did == 0xF19B:
			return 'CalibrationDateDataIdentifier'
		if did == 0xF19C:
			return 'CalibrationEquipmentSoftwareNumberDataIdentifier'
		if did == 0xF19D:
			return 'ECUInstallationDateDataIdentifier'
		if did == 0xF19E:
			return 'ODXFileDataIdentifier'
		if did == 0xF19F:
			return 'EntityDataIdentifier'

		if did >= 0xF1A0 and did <= 0xF1EF:
			return 'IdentificationOptionVehicleManufacturerSpecific'
		if did >= 0xF1F0 and did <= 0xF1FF:
			return 'IdentificationOptionSystemSupplierSpecific'
		if did >= 0xF200 and did <= 0xF2FF:
			return 'PeriodicDataIdentifier'	
		if did >= 0xF300 and did <= 0xF3FF:
			return 'DynamicallyDefinedDataIdentifier'
		if did >= 0xF400 and did <= 0xF4FF:
			return 'OBDDataIdentifier'
		if did >= 0xF500 and did <= 0xF5FF:
			return 'OBDDataIdentifier'
		if did >= 0xF600 and did <= 0xF6FF:
			return 'OBDMonitorDataIdentifier'
		if did >= 0xF700 and did <= 0xF7FF:
			return 'OBDMonitorDataIdentifier'
		if did >= 0xF800 and did <= 0xF8FF:
			return 'OBDInfoTypeDataIdentifier'
		if did >= 0xF900 and did <= 0xF9FF:
			return 'TachographDataIdentifier'
		if did >= 0xFA00 and did <= 0xFA0F:
			return 'AirbagDeploymentDataIdentifier'
		if did >= 0xFA10 and did <= 0xFAFF:
			return 'SafetySystemDataIdentifier'
		if did >= 0xFB00 and did <= 0xFCFF:
			return 'ReservedForLegislativeUse'
		if did >= 0xFD00 and did <= 0xFEFF:
			return 'SystemSupplierSpecific'
		if did >= 0xFF00 and did <= 0xFFFF:
			return 'ISOSAEReserved'