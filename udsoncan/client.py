from udsoncan import Response, Request, services, DidCodec, Routine
from udsoncan.exceptions import *
from udsoncan.configs import default_client_config
import struct
import logging

class Client:
	def __init__(self, conn, config=default_client_config, request_timeout = 1, heartbeat  = None):
		self.conn = conn
		self.request_timeout = request_timeout
		self.config = config
		self.heartbeat = heartbeat
		self.logger = logging.getLogger("UdsClient")

	def __enter__(self):
		self.open()
		return self
	
	def __exit__(self, type, value, traceback):
		self.close()

	def open(self):
		if not self.conn.is_open():
			self.conn.open()

	def close(self):
		self.conn.close()

## 	DiagnosticSessionControl
	def change_session(self, newsession):
		service = services.DiagnosticSessionControl(newsession)
		req = Request(service)
		#No service params
		response = self.send_request(req)

		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) is not for the requested subfunction (0x%02x)" % (received, expected))

		if len(response.data) > 1:
			return response.data[1:]
		return None

##  SecurityAccess
	def request_seed(self, level):
		service = services.SecurityAccess(level, mode=services.SecurityAccess.Mode.RequestSeed)
		req = Request(service)
		response = self.send_request(req)
		
		if len(response.data) < 2:
			raise InvalidResponseException(response, "Response data must be at least 2 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Seed received from server (0x%02x) is not for the requested subfunction (0x%02x)" % (received, expected))

		return response.data[1:]

	def send_key(self, level, key):
		service = services.SecurityAccess(level, mode=services.SecurityAccess.Mode.SendKey)
		req = Request(service)
		req.data = key
		response = self.send_request(req)
		
		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) is not for the requested subfunction (0x%02x)" % (received, expected))

		return response.positive
		
	def unlock_security_access(self, level):
		if 'security_algo' not in self.config or not callable(self.config['security_algo']):
			raise NotImplementedError("Client configuration does not provide a security algorithm")
		
		seed = self.request_seed(level)
		key = self.config['security_algo'].__call__(seed)
		return self.send_key(level, key)

	def tester_present(self, suppress_positive_response=False):
		service = services.TesterPresent()
		if not isinstance(suppress_positive_response, bool):
			raise ValueError("suppress_positive_response must be a boolean value")
		req = Request(service, suppress_positive_response=suppress_positive_response)
		response = self.send_request(req)

		if not suppress_positive_response:
			if response.data is None or len(response.data) < 1:
				raise InvalidResponseException(response, "Response data must be at least 1 bytes")

			received = int(response.data[0])
			expected = service.subfunction_id()
			if received != expected:
				raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) is not for the requested subfunction (0x%02x)" % (received, expected))

		return True

	def check_did_config(self, didlist):
		didlist = [didlist] if not isinstance(didlist, list) else didlist
		if not 'data_identifiers' in self.config or  not isinstance(self.config['data_identifiers'], dict):
			raise AttributeError('Configuration does not contains a valid data identifier description.')
		didconfig = self.config['data_identifiers']

		for did in didlist:
			if did not in didconfig:
				raise LookupError('Actual data identifier configuration contains no definition for data identifier %d' % did)

		return didconfig

	def read_data_by_identifier(self, dids, output_fmt='dict'):
		service = services.ReadDataByIdentifier(dids)
		self.logger.info("Reading data identifier %s", dids)
		req = Request(service)
		didlist = [service.dids] if not isinstance(service.dids, list) else service.dids

		didconfig = self.check_did_config(didlist)
		req.data = struct.pack('>'+'H'*len(didlist), *didlist)
		response = self.send_request(req)

		if output_fmt in ['list']:
			values = []
		elif output_fmt == 'dict':
			values = {}
		else:
			raise ValueError("Output format cannot be %s. Use list or dict" % output_fmt)

		offset = 0
		done = False
		received = {}
		for did in didlist:
			received[did] = False

		while True:
			if len(response.data) <= offset:
				break

			if len(response.data) <= offset +1:
				raise UnexpectedResponseException(response, "Response given by server is incomplete.")

			did = struct.unpack('>H', response.data[offset:offset+2])[0]
			
			if did not in didlist:
				raise UnexpectedResponseException(response, "Server returned a value for data identifier 0x%x which was not requested" % did)

			if did not in didconfig:
				raise LookupError('Actual data identifier configuration contains no definition for data identifier 0x%x' % did)
			
			codec = DidCodec.from_config(didconfig[did])
			offset+=2

			if len(response.data) < offset+len(codec):
				raise UnexpectedResponseException(response, "Value fo data identifier 0x%x was incomplete according to definition in configuration" % did)
			subpayload = response.data[offset:offset+len(codec)]
			offset += len(codec)
			val = codec.decode(subpayload)
			received[did] = True

			if output_fmt in ['list']:
				values.append(val)
			elif output_fmt == 'dict':
				values[did] = val

		notreceived = 0;
		for k in received:
			notreceived += 1 if k == False else 0

		if notreceived > 0:
			raise UnexpectedResponseException(response, "%d data identifier values have not been received by the server" % notreceived)

		return values

	def write_data_by_identifier(self, did, value):
		service = services.WriteDataByIdentifier(did)
		self.logger.info("Writing data identifier %s", did)
		req = Request(service)
		
		didconfig = self.check_did_config(did)
		req.data = struct.pack('>H', service.did)

		codec = DidCodec.from_config(didconfig[did])
		req.data += codec.encode(value)
		response = self.send_request(req)

		if len(response.data) < 2:
			raise InvalidResponseException(response, "Response must be at least 2 bytes long")

		did_fb = struct.unpack(">H", response.data[0:2])[0]

		if did_fb != did:
			raise UnexpectedResponseException(response, "Server returned a response for data identifier 0x%02x while client requested for did 0x%02x" % (did_fb, did))
			
		return True

	def ecu_reset(self, resettype, powerdowntime=None):
		service = services.ECUReset(resettype, powerdowntime)
		self.logger.info("Requesting ECU reset of type 0x%02x" % (resettype))
		req = Request(service)
		if powerdowntime is not None:
			if resettype == services.ECUReset.enableRapidPowerShutDown:
				req.data =struct.pack('B', service.powerdowntime)
			else:
				raise ValueError("Power down time is only used when reset type is enableRapidShutdown")
		
		response = self.send_request(req)

		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise UnexpectedResponseException(response, "Response data must be at least 1 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) is not for the requested subfunction (0x%02x)" % (received, expected))

		return True

	def clear_dtc(self, group=0xFFFFFF):
		service = services.ClearDiagnosticInformation(group)
		request = Request(service)
		group = service.group  # Service object can filter that value

		hb = (group >> 16) & 0xFF
		mb = (group >> 8) & 0xFF
		lb = (group >> 0) & 0xFF 

		request.data = struct.pack("BBB", hb,mb,lb)
		response = self.send_request(request)
		return True

	def start_routine(self, routine_id, data=None):
		self.logger.info("Sending request to start %s routine" % (Routine.name_from_id(routine_id)))
		return self.routine_control(routine_id, services.RoutineControl.startRoutine, data)

	def stop_routine(self, routine_id, data=None):
		self.logger.info("Sending request to stop %s routine" % (Routine.name_from_id(routine_id)))
		return self.routine_control(routine_id, services.RoutineControl.stopRoutine, data)

	def get_routine_result(self, routine_id, data=None):
		self.logger.info("Sending request to get results of %s routine" % (Routine.name_from_id(routine_id)))
		return self.routine_control(routine_id, services.RoutineControl.requestRoutineResults, data)

	def routine_control(self, routine_id, control_type, data=None):
		service = services.RoutineControl(routine_id, control_type)
		req = Request(service)

		req.data = struct.pack('>H', routine_id)

		if data is not None:
			req.data += data

		response = self.send_request(req)

		if len(response.data) < 3: 	
			raise InvalidResponseException(response, "Response data must be at least 3 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (received, expected))

		received = struct.unpack(">H", response.data[1:3])[0]
		expected = service.routine_id

		if received != expected:
			raise UnexpectedResponseException(response, "Response received from server (ID = 0x%02x) is not for the requested routine ID (0x%02x)" % (received, expected))

		return response

	def read_extended_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.readExtendedTimingParameterSet)

	def read_active_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.readCurrentlyActiveTimingParameters)

	def set_timing_parameters(self, params):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.setTimingParametersToGivenValues, request_record=params)
	
	def reset_default_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.setTimingParametersToDefaultValues)
		
	def access_timing_parameter(self, access_type, request_record=None):
		service = services.AccessTimingParameter(access_type, request_record)
		request = Request(service)

		if service.request_record is not None:
			request.data += service.request_record

		response = self.send_request(request)

		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 2 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Access Type of response (0x%02x) does not match request access type (0x%02x)" % (received, expected))

		if response.data is not None and service.access_type not in [services.AccessTimingParameter.readExtendedTimingParameterSet, services.AccessTimingParameter.readCurrentlyActiveTimingParameters]:
			self.logger.warning("Server returned data altough none were asked")

		if len(response.data) > 1:
			return response.data[1:]
		else:
			return None

	def request_download(self, memory_location, dfi=None):
		return self.request_upload_download(services.RequestDownload, memory_location, dfi)

	def request_upload(self, memory_location, dfi=None):
		return self.request_upload_download(services.RequestUpload, memory_location, dfi)

	def request_upload_download(self, service_cls, memory_location, dfi=None):
		if service_cls not in [services.RequestDownload, services.RequestUpload]:
			raise ValueError('services must eitehr be RequestDownload or RequestUpload')

		service = service_cls(memory_location=memory_location, dfi=dfi)
		req = Request(service)

		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		req.data=b""
		req.data += service.dfi.get_byte()
		req.data += service.memory_location.ali.get_byte()
		req.data += service.memory_location.get_address_bytes()
		req.data += service.memory_location.get_memorysize_bytes()

		response = self.send_request(req)

		if len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		lfid = int(response.data[0]) >> 4

		if lfid > 8:
			raise NotImplementedError('This client does not support number bigger than %d bits' % (8*8))

		if len(response.data) < lfid+1:
			raise InvalidResponseException(response, "Length of data (%d) is too short to contains the number of block of given length (%d)" % (len(response.data), lfid))
		
		todecode = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
		for i in range(1,lfid+1):
			todecode[-i] = response.data[lfid+1-i]

		return struct.unpack('>q', todecode)[0]

	def send_request(self, request, timeout=-1, validate_response=True):
		if timeout is not None and timeout < 0:
			timeout = self.request_timeout
		self.conn.empty_rxqueue()
		self.logger.debug("Sending request to server")
		self.conn.send(request)

		if not request.suppress_positive_response:
			self.logger.debug("Waiting for server response")
			payload = self.conn.wait_frame(timeout=timeout, exception=True)
			response = Response.from_payload(payload)
			self.logger.info("Response received from server")

			if not response.valid:
				self.logger.error("Invalid response gotten by server")
				if validate_response:
					raise InvalidResponseException(response)
					
			if response.service.response_id() != request.service.response_id():
				msg = "Response gotten from server has a service ID different than the one of the request. Received=%s, Expected=%s" % (response.service.response_id() , request.service.response_id() )
				self.logger.error(msg)
				raise UnexpectedResponseException(response, details=msg)
			
			if not response.positive:
				self.logger.warning("Server responded with Negative response %s" % response.code_name)
				if not request.service.is_supported_negative_response(response.code):
					self.logger.warning("Given response (%s) is not a supported negative response code according to UDS standard." % response.code_name)	
				if validate_response:
					raise NegativeResponseException(response)

			return response