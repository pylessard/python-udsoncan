import isotp
import threading
import queue
import inspect
import struct
import time
import socket
import errno

from udsoncan.exceptions import *
import inspect


class Connection(object):
	def __init__(self, interface, rxid, txid, tpsock=None):
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
	def __init__(self, service = None, subfunction = None, suppress_positive_response = False):
		if isinstance(service, services.BaseService):
			self.service = service.__class__
			self.subfunction = service.subfunction_id()	# service instance are able toe generate the subfunction ID
		elif inspect.isclass(service) and issubclass(service, services.BaseService):
			if subfunction is not None:
				self.service = service
				self.subfunction = subfunction
		elif service is not None:
			raise ValueError("Given service must be a service class or instance")

		self.suppress_positive_response = suppress_positive_response
		self.data = None

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

		GeneralSecurityViolation 			= 0x38 + 0
		SecuredModeRequested 				= 0x38 + 1
		InsufficientProtection 				= 0x38 + 2
		TerminationWithSignatureRequested 	= 0x38 + 3
		AccessDenied 						= 0x38 + 4
		VersionNotSupported 				= 0x38 + 5
		SecuredLinkNotSupported 			= 0x38 + 6
		CertificateNotAvailable 			= 0x38 + 7
		AuditTrailInformationNotAvailable 	= 0x38 + 8



		@classmethod
		def get_name(cls, given_id):
			if given_id is None:
				return ""

			for member in inspect.getmembers(cls):
				if isinstance(member[1], int):
					if member[1] == given_id:
						return member[0]
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
		self.positive = False
		self.response_code = None
		self.response_code_name = ""
		self.valid = False

		self.data = data
		self.service = service

		if code is not None:
			self.response_code=code
			self.response_code_name = Response.Code.get_name(code)
			if not Response.Code.is_negative(code):
				self.positive=True

	#Used by server
	def get_payload(self):
		if not isinstance(self.service, services.BaseService) and not issubclass(self.service, services.BaseService):
			raise ValueError("Cannot make payload from response object. Given service is not a valid service object")

		if not isinstance(self.response_code, int):
			raise ValueError("Cannot make payload from response object. Given response code is not a valid integer")

		payload = struct.pack("B", self.service.response_id())
		if not self.positive:
			payload += b'\x7F'
		if not self.positive or self.positive and not self.service.has_custom_positive_response():
			payload += struct.pack('B', self.response_code)

		if self.data is not None:
			payload += self.data
		return payload


	#Analyze a TP frame an build a Response object
	@classmethod
	def from_payload(cls, payload):
		response = cls()
		if len(payload) >= 1:
			response.service = services.cls_from_response_id(payload[0])
			if len(payload) >= 2 :
				if payload[1] != 0x7F:
					data_start=1 if response.service.has_custom_positive_response() else 2
					response.response_code = Response.Code.PositiveResponse
					response.response_code_name = Response.Code.get_name(Response.Code.PositiveResponse)
					response.positive = True
					response.valid = True
				else:
					data_start=3
					response.positive = False
					if len(payload) >= 3:
						response.response_code = payload[2]
						response.response_code_name = Response.Code.get_name(response.response_code)
						response.valid = True
				
				if len(payload) > data_start:
					response.data = payload[data_start:]
			else:
				response.valid = False
		else:
			response.valid = False
		return response

	def __repr__(self):
		responsename = Response.Code.get_name(Response.Code.PositiveResponse) if self.positive else 'NegativeResponse(%s)' % self.response_code_name
		bytesize = len(self.data) if self.data is not None else 0
		return '<%s: [%s] - %d data bytes at 0x%08x>' % (responsename, self.service.get_name(), bytesize, id(self))

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