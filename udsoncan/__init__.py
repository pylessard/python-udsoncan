import isotp
import threading
import queue
import inspect
import struct
import time

from udsoncan.exceptions import *


class Connection(object):
	def __init__(self, interface, rxid, txid):
		self.interface=interface
		self.rxid=rxid
		self.txid=txid
		self.rxqueue = queue.Queue()
		self.exit_requested = False

		self.rxthread = threading.Thread(target=self.rxthread_task)
		self.tpsock = isotp.socket(timeout=0.1)

	def open(self):
		self.tpsock.bind(self.interface, rxid=self.rxid, txid=self.txid)
		self.rxthread.start()

	def is_open(self):
		return self.tpsock.bound

	def rxthread_task(self):
		while not self.exit_requested:
			try:
				data = self.tpsock.recv()
				if data is not None:
					self.rxqueue.put(data)
			except:
				self.exit_requested = True

	def close(self):
		self.exit_requested = True
		self.tpsock.close()

	def send(self, obj):
		if isinstance(obj, Request) or isinstance(obj, Response):
			payload = obj.get_payload()  
		else :
			payload = obj

		self.tpsock.send(payload)

	def wait_frame(self, timeout=5, exception=False):
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
	def __init__(self, service = None, subfunction = None, suppressPosResponse = False):
		if isinstance(service, services.BaseService):
			self.service = service.__class__
			self.subfunction = service.subfunction_id()	# service instance are able toe generate the subfunction ID
		elif inspect.isclass(service) and issubclass(service, services.BaseService):
			if subfunction is not None:
				self.service = service
				self.subfunction = subfunction
		elif service is not None:
			raise ValueError("Given service must be a service class or instance")

		self.suppressPosResponse = suppressPosResponse
		self.service_data = None

	def get_payload(self):
		if not issubclass(self.service, services.BaseService):
			raise ValueError("Cannot generate a payload. Given service is not a subclass of BaseService")

		if not isinstance(self.subfunction, int):
			raise ValueError("Cannot generate a payload. Given subfunction is not a valid integer")

		requestid = self.service.request_id()	# Return the service ID used to make a client request
		subfunction = self.subfunction	

		if self.suppressPosResponse:
			subfunction |= 0x80
		payload = struct.pack("BB", requestid, subfunction)
		if self.service_data is not None:
			 payload += self.service_data

		return payload

	@classmethod
	def from_payload(cls, payload):
		req = cls()
		if len(payload) >= 2:
			req.service = services.cls_from_request_id(payload[0])
			req.subfunction = int(payload[1]) & 0x7F
			req.suppressPosResponse = True if payload[1] & 0x80 > 0 else False
			if len(payload) > 2:
				req.service_data = payload[2:]
		return req


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

		@classmethod
		def get_name(cls, given_id):
			if given_id is None:
				return ""

			for member in inspect.getmembers(cls):
				if isinstance(member[1], int):
					if member[1] == given_id:
						return member[0]

	def __init__(self, service = None, code = None, payload=None):
		self.positive = False
		self.response_code = None
		self.response_code_name = ""
		self.valid = False

		self.payload = payload
		self.service = service

		if code is not None:
			self.response_code=code
			self.response_code_name = Response.Code.get_name(code)
			if code == Response.Code.PositiveResponse:
				self.positive=True

	#Used by server
	def get_payload(self):
		payload = struct.pack("B", self.service.response_id())
		if not self.positive:
			payload += b'\x7F'
		payload += struct.pack('B', self.response_code)

		if self.payload is not None:
			payload += self.payload
		return payload


	#Analyze a TP frame an build a Response object
	@classmethod
	def from_payload(cls, payload):
		response = cls()
		if len(payload) >= 1:
			if payload[0] != 0x7F:
				response.service = services.cls_from_response_id(payload[0])
				response.response_code = Response.Code.PositiveResponse
				response.response_code_name = Response.Code.get_name(Response.Code.PositiveResponse)
				response.positive = True
				response.valid = True
				response.service_data = b""
			else:
				if len(payload) >= 2:
					response.service = services.cls_from_response_id(payload[1])
					response.positive = False
					if len(response) >= 3:
						response.response_code = response[2]
						response.response_code_name = Response.Code.get_name(self.response_code)
						response.valid = True
						if len(payload) >= 4:
							response.service_data = payload[4:len(payload)-4]
		else:
			response.valid = False
		return response


class SecurityLevel(object):
	def __init__(self, levelid):
		self.levelid = levelid & 0xFE