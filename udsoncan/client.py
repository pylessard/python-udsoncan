from udsoncan import Response, Request, services, DidCodec, Routine, IOMasks, Dtc
from udsoncan.exceptions import *
from udsoncan.configs import default_client_config
import struct
import logging
import math

class DTCServerRepsonseContainer(object):
	def __init__(self):
		self.dtcs = []
		self.dtc_count = 0
		self.dtc_format = None
		self.status_availability = None
		self.dtc_snapshot_map = {}
		self.snapshots = []
		self.extended_data = []

class Client:
	def __init__(self, conn, config=default_client_config, request_timeout = 1, heartbeat  = None):
		self.conn = conn
		self.request_timeout = request_timeout
		self.config = config
		self.heartbeat = heartbeat
		self.logger = logging.getLogger("UdsClient")
		self.last_dtc_status_availability_mask = None

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
		params = self.config['security_algo_params'] if 'security_algo_params' in self.config else None
		key = self.config['security_algo'].__call__(seed, params)
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
		if 'data_identifiers' not in self.config or  not isinstance(self.config['data_identifiers'], dict):
			raise AttributeError('Configuration does not contains a valid data identifier description.')
		didconfig = self.config['data_identifiers']

		for did in didlist:
			if did not in didconfig:
				raise LookupError('Actual data identifier configuration contains no definition for data identifier 0x%04x' % did)

		return didconfig

	def check_io_config(self, didlist):
		didlist = [didlist] if not isinstance(didlist, list) else didlist
		if not 'input_output' in self.config or  not isinstance(self.config['input_output'], dict):
			raise AttributeError('Configuration does not contains an Input/Output section (config[input_output].')
		ioconfigs = self.config['input_output']

		for did in didlist:
			if did not in ioconfigs:
				raise LookupError('Actual Input/Output configuration contains no definition for data identifier 0x%04x' % did)
			if isinstance(ioconfigs[did], dict):
				if 'codec'not in ioconfigs[did]:
					raise LookupError('Configuration for Input/Output identifier 0x%04x is missing a codec')

				if 'mask' in ioconfigs[did]:
					mask_def = ioconfigs[did]['mask']
					for mask_name in mask_def:
						if not isinstance(mask_def[mask_name], int):
							raise ValueError('In Input/Output configuration for did 0x%04x, mask "%s" is not an integer' % (did, mask_name))

						if mask_def[mask_name] < 0:
							raise ValueError('In Input/Output configuration for did 0x%04x, mask "%s" is not a positive integer' % (did, mask_name))

				
				if 'mask_size' in ioconfigs[did]:
					if not isinstance(ioconfigs[did]['mask_size'], int):
						raise ValueError('mask_size in Input/Output configuration for did 0x%04x must be a valid integer' % (did))

					if ioconfigs[did]['mask_size'] < 0:
						raise ValueError('mask_size in Input/Output configuration for did 0x%04x must be greater than 0' % (did))

					if 'mask' in ioconfigs[did]:
						mask_def = ioconfigs[did]['mask']
						for mask_name in mask_def:
							if mask_def[mask_name] > 2**(ioconfigs[did]['mask_size']*8)-1:
								raise ValueError('In Input/Output configuration for did 0x%04x, mask "%s" cannot fit in %d bytes (defined by mask_size)' % (did, mask_name,ioconfigs[did]['mask_size']))

		return ioconfigs

	def read_data_by_identifier_first(self, did):
		values = self.read_data_by_identifier(did, output_fmt='list')
		if len(values) > 0:
			return values[0]

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
		received = {}
		for did in didlist:
			received[did] = False
		
		tolerate_zero_padding = self.config['tolerate_zero_padding'] if 'tolerate_zero_padding' in self.config else True
		while True:
			if len(response.data) <= offset:
				break

			if len(response.data) <= offset +1:
				if tolerate_zero_padding and response.data[-1] == 0:
					break
				raise UnexpectedResponseException(response, "Response given by server is incomplete.")

			did = struct.unpack('>H', response.data[offset:offset+2])[0]
			if did == 0 and did not in didconfig and tolerate_zero_padding:
				if response.data[offset:] == b'\x00' * (len(response.data) - offset):
					break

			if did not in didlist:
				raise UnexpectedResponseException(response, "Server returned a value for data identifier 0x%04x which was not requested" % did)

			if did not in didconfig:
				raise LookupError('Actual data identifier configuration contains no definition for data identifier 0x%04x' % did)
			
			codec = DidCodec.from_config(didconfig[did])
			offset+=2

			if len(response.data) < offset+len(codec):
				raise UnexpectedResponseException(response, "Value fo data identifier 0x%04x was incomplete according to definition in configuration" % did)
			subpayload = response.data[offset:offset+len(codec)]
			offset += len(codec)
			val = codec.decode(subpayload)
			received[did] = True

			if output_fmt in ['list']:
				values.append(val)
			elif output_fmt == 'dict':
				values[did] = val

		notreceived = 0
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

	def clear_dtc(self, group=0xFFFFFF, suppress_positive_response=False):
		service = services.ClearDiagnosticInformation(group)
		request = Request(service, suppress_positive_response=suppress_positive_response)
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
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

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

	def communication_control(self, control_type, communication_type):
		service = services.CommunicationControl(control_type, communication_type)
		req = Request(service)
		req.data = service.communication_type.get_byte()

		response = self.send_request(req)

		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

		received = int(response.data[0])
		expected = service.subfunction_id()

		if received != expected:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (received, expected))

		return response

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

	def transfer_data(self, block_sequence_counter, data=None):
		service = services.TransferData(block_sequence_counter, data)
		request = Request(service)

		request.data = service.data

		response = self.send_request(request)

		if len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes") # Should be catched by response decoder first

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Block sequence number of response (0x%02x) does not match request block sequence number (0x%02x)" % (received, expected))

		if len(response.data) > 1:
			return response.data[1:]
		else:
			return None

	def request_transfer_exit(self, data=None, suppress_positive_response=False):
		service = services.RequestTransferExit(data)
		request = Request(service, suppress_positive_response=suppress_positive_response)
		request.data = service.data

		response = self.send_request(request)

		return response.data

	def link_control(self, control_type, baudrate=None):
		service = services.LinkControl(control_type, baudrate)
		request = Request(service)
		if service.baudrate is not None:
			request.data = service.baudrate.get_bytes()

		response = self.send_request(request)

		if len(response.data) < 1:
			raise InvalidResponseException(response, "Response data must be at least 1 bytes") # Should be catched by response decoder first

		received = int(response.data[0])
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (received, expected))

		return response

	def io_control(self,  did, control_param=None, values=None, masks=None):
		service = services.InputOutputControlByIdentifier( did, control_param=control_param, values=values, masks=masks)
		req = Request(service)
		req.data = b''

		ioconfig = self.check_io_config(service.did)

		req.data += struct.pack('>H', service.did)

		if service.control_param is not None:
			req.data += struct.pack('B', control_param)
		
		codec = DidCodec.from_config(ioconfig[did])
		
		if service.values is not None:
			req.data += codec.encode(*service.values.args, **service.values.kwargs)

		if service.masks is not None: # Skip the masks byte.
			if isinstance(service.masks, bool):
				byte = b'\xFF' if service.masks == True else b'\x00'
				if 'mask_size' in  ioconfig[did]:
					req.data += (byte * ioconfig[did]['mask_size'])
				else:
					raise LookupError('Given mask is boolean value, indicating that all mask should be set to same value, but no mask_size is defined in configuration. Cannot guess how many bits to set.')

			elif isinstance(service.masks, IOMasks):
				if 'mask' not in ioconfig[did]:
					raise ValueError('Cannot apply given mask. Input/Output configuration does not define their position (and size).')
				masks_config = ioconfig[did]['mask']
				given_masks = service.masks.get_dict()

				numeric_val = 0
				for mask_name in given_masks:
					if mask_name not in masks_config:
						raise ValueError('Cannot set mask bit for mask %s. The configuration does not define its position' % (mask_name))	
					
					if given_masks[mask_name] == True:
						numeric_val |= masks_config[mask_name]

				minsize = math.ceil(math.log(numeric_val+1, 2)/8.0)
				size = minsize if 'mask_size' not in ioconfig[did] else ioconfig[did]['mask_size']
				req.data += numeric_val.to_bytes(size, 'big')

		response = self.send_request(req)
		min_response_size = 2 if service.control_param is not None else 1	# Spec specifies that if first by is a ControlParameter, it must be echoed back by the server

		if len(response.data) < min_response_size:
			raise InvalidResponseException(response, "Response must be at least %d bytes long" % d)

		did_fb = struct.unpack(">H", response.data[0:2])[0]

		if did_fb != did:
			raise UnexpectedResponseException(response, "Server returned a response for data identifier 0x%02x while client requested for did 0x%02x" % (did_fb, did))

		next_byte = 2
		if service.control_param is not None:
			if len(response.data) < next_byte:
				raise InvalidResponseException(response, 'Response should include an echoe of the InputOutputControlParameter (0x%02x)' % service.control_param)

			control_param_fb = response.data[next_byte]
			if service.control_param != control_param_fb:
				raise UnexpectedResponseException(response, 'Echo of the InputOutputControlParameter (0x%02x) does not match the value in the request (0x%02x)' % (control_param_fb, service.control_param))	

			next_byte +=1

		if len(response.data) >= next_byte:
			tolerate_zero_padding = self.config['tolerate_zero_padding'] if 'tolerate_zero_padding' in self.config else True
			remaining_data = response.data[next_byte:]
			size_ok = True 
			
			if len(remaining_data) > len(codec):
				if remaining_data[len(codec):] == b'\x00' * (len(remaining_data) - len(codec)):
					if tolerate_zero_padding:
						remaining_data = remaining_data[0:len(codec)]
					else:
						size_ok = False
				else:
					size_ok = False
			elif len(remaining_data) < len(codec):
				size_ok = False

			if not size_ok:
				raise UnexpectedResponseException(response, 'The server did not returned the expected amount of data. Expecting %d bytes, received %d. Trying to decode anyways.' % (len(codec), len(remaining_data)))

			try:
				decoded_data = codec.decode(remaining_data)
			except Exception as e:
				raise UnexpectedResponseException(response, 'Response from server could not be decoded. Exception is : %s' % e)
			
			return decoded_data

# ====  ReadDTCInformation


	def get_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCByStatusMask, status_mask=status_mask)

	def get_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)

	def get_number_of_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportNumberOfDTCByStatusMask, status_mask=status_mask)
	
	def get_number_of_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportNumberOfDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)
	
	def get_dtc_severity(self, dtc):
		return self.read_dtc_information(services.ReadDTCInformation.reportSeverityInformationOfDTC, dtc=dtc)

	def read_dtc_information(self, subfunction, status_mask=None, severity_mask=None, dtc_mask=None, dtc=None, snapshot_record_number=None, extended_data_record_number=None):
#===== Process params		
		if status_mask is not None and isinstance(status_mask, Dtc.Status):
			status_mask = status_mask.get_byte_as_int()

		if severity_mask is not None and isinstance(severity_mask, Dtc.Severity):
			severity_mask = severity_mask.get_byte_as_int()

		if dtc is not None and isinstance(dtc, Dtc):
			dtc = dtc.id

#===== Requests
		request_subfn_no_param = [
			services.ReadDTCInformation.reportSupportedDTC,
			services.ReadDTCInformation.reportFirstTestFailedDTC,
			services.ReadDTCInformation.reportFirstConfirmedDTC,
			services.ReadDTCInformation.reportMostRecentTestFailedDTC,
			services.ReadDTCInformation.reportMostRecentConfirmedDTC,
			services.ReadDTCInformation.reportDTCFaultDetectionCounter,
			services.ReadDTCInformation.reportDTCWithPermanentStatus,

			services.ReadDTCInformation.reportDTCSnapshotIdentification	# Not so clear in documentation

			]

		request_subfn_status_mask = [
			services.ReadDTCInformation.reportNumberOfDTCByStatusMask,
			services.ReadDTCInformation.reportDTCByStatusMask,
			services.ReadDTCInformation.reportMirrorMemoryDTCByStatusMask,
			services.ReadDTCInformation.reportNumberOfMirrorMemoryDTCByStatusMask,
			services.ReadDTCInformation.reportNumberOfEmissionsRelatedOBDDTCByStatusMask,
			services.ReadDTCInformation.reportEmissionsRelatedOBDDTCByStatusMask
		]

		request_subfn_mask_record_plus_snapshot_record_number = [
			services.ReadDTCInformation.reportDTCSnapshotRecordByDTCNumber
		]

		request_subfn_snapshot_record_number = [
			services.ReadDTCInformation.reportDTCSnapshotRecordByRecordNumber
		]

		request_subfn_mask_record_plus_extdata_record_number = [
			services.ReadDTCInformation.reportDTCExtendedDataRecordByDTCNumber,
			services.ReadDTCInformation.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber
		]

		request_subfn_severity_plus_status_mask = [
			services.ReadDTCInformation.reportNumberOfDTCBySeverityMaskRecord,
			services.ReadDTCInformation.reportDTCBySeverityMaskRecord
		]

		request_subfn_mask_record = [
			services.ReadDTCInformation.reportSeverityInformationOfDTC		
			]

# ===== Responses
		response_subfn_dtc_availability_mask_plus_dtc_record = [
			services.ReadDTCInformation.reportDTCByStatusMask,
			services.ReadDTCInformation.reportSupportedDTC,
			services.ReadDTCInformation.reportFirstTestFailedDTC,
			services.ReadDTCInformation.reportFirstConfirmedDTC,
			services.ReadDTCInformation.reportMostRecentTestFailedDTC,
			services.ReadDTCInformation.reportMostRecentConfirmedDTC,
			services.ReadDTCInformation.reportMirrorMemoryDTCByStatusMask,
			services.ReadDTCInformation.reportEmissionsRelatedOBDDTCByStatusMask,
			services.ReadDTCInformation.reportDTCWithPermanentStatus
		]

		response_subfn_number_of_dtc = [
			services.ReadDTCInformation.reportNumberOfDTCByStatusMask,
			services.ReadDTCInformation.reportNumberOfDTCBySeverityMaskRecord,
			services.ReadDTCInformation.reportNumberOfMirrorMemoryDTCByStatusMask,
			services.ReadDTCInformation.reportNumberOfEmissionsRelatedOBDDTCByStatusMask,
		]

		response_subfn_dtc_availability_mask_plus_dtc_record_with_severity = [
			services.ReadDTCInformation.reportDTCBySeverityMaskRecord,
			services.ReadDTCInformation.reportSeverityInformationOfDTC
		]

# ==== Config
		tolerate_zero_padding = self.config['tolerate_zero_padding'] if 'tolerate_zero_padding' in self.config else True
		ignore_all_zero_dtc = self.config['ignore_all_zero_dtc'] if 'ignore_all_zero_dtc' in self.config else True

# ==== Craft Request
		service = services.ReadDTCInformation(subfunction)
		req = Request(service)

		if service.subfunction in request_subfn_no_param:
			pass
		elif service.subfunction in request_subfn_status_mask:
			if status_mask is None:
				raise ValueError('status_mask must be provided for subfunction 0x%02x' % service.subfunction)
				
			if not isinstance(status_mask, int) or status_mask < 0 or status_mask > 0xFF:
				raise ValueError('status_mask must be a Dtc.Status instance or an integer between 0 and 0xFF')

			req.data = struct.pack('B', (status_mask & 0xFF))
		elif service.subfunction in request_subfn_mask_record_plus_snapshot_record_number:
			pass
		elif service.subfunction in request_subfn_snapshot_record_number:
			pass
		elif service.subfunction in request_subfn_mask_record_plus_extdata_record_number:
			pass
		elif service.subfunction in request_subfn_severity_plus_status_mask:

			if status_mask is None:
				raise ValueError('status_mask must be provided for subfunction 0x%02x' % service.subfunction)
				
			if not isinstance(status_mask, int) or status_mask < 0 or status_mask > 0xFF:
				raise ValueError('status_mask must be a Dtc.Status instance or an integer between 0 and 0xFF')

			if severity_mask is None:
				raise ValueError('severity_mask must be provided for subfunction 0x%02x' % service.subfunction)
				
			if not isinstance(severity_mask, int) or severity_mask < 0 or severity_mask > 0xFF:
				raise ValueError('severity_mask must be a Dtc.Severity instance or an integer between 0 and 0xFF')

			req.data = struct.pack('B', (severity_mask & 0xFF))
			req.data += struct.pack('B', (status_mask & 0xFF))
		elif service.subfunction in request_subfn_mask_record:
			if dtc is None:
				raise ValueError('A dtc value must be provided for subfunction 0x%02x' % service.subfunction)

			if not isinstance(dtc, int) or dtc < 0 or dtc > 0xFFFFFF:
				raise ValueError('dtc parameter must be an instance of Dtcor an integer between 0 and 0xFFFFFF')

			req.data = b''
			req.data += struct.pack('B', (dtc >> 16) & 0xFF)
			req.data += struct.pack('B', (dtc >> 8) & 0xFF)
			req.data += struct.pack('B', (dtc >> 0) & 0xFF)

# ==== Get response
		response = self.send_request(req)
		user_response = DTCServerRepsonseContainer()
		
		if len(response.data) < 1:
			raise InvalidResponseException(response, 'Response must be at least 1 byte long (echo of subfunction)')

# ==== Parse and validate response
		response_subfn = int(response.data[0])

		if response_subfn != service.subfunction:
			raise UnexpectedResponseException(response, 'Echo of ReadDTCInformation subfunction gotten from server(0x%02x) does not match the value in the request subfunction (0x%02x)' % (response_subfn, service.subfunction))	

		
		if service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record or service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:

			if service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record:
				dtc_size = 4
			elif service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:
				dtc_size = 6


			if len(response.data) < 2:
				raise InvalidResponseException(response, 'Response must be at least 2 byte long (echo of subfunction and DTCStatusAvailabilityMask)')

			user_response.status_availability = response.data[1]

			actual_byte = 2

			while True:
				if len(response.data) <= actual_byte:
					break
				elif len(response.data) < actual_byte+dtc_size:
					missing_bytes = len(response.data)-actual_byte
					if tolerate_zero_padding and response.data[actual_byte:] == b'\x00'*missing_bytes:
						break
					else:
						if service.subfunction != services.ReadDTCInformation.reportSeverityInformationOfDTC or actual_byte == 2: 
							raise InvalidResponseException(response, 'Incomplete DTC record. Missing %d bytes to response to complete the record' % (missing_bytes))
				else:
					dtc_bytes = response.data[actual_byte:actual_byte+dtc_size]
					if dtc_bytes == b'\x00'*dtc_size and ignore_all_zero_dtc:
						pass # ignore
					else:						
						dtcid = 0
						if service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record:
							dtcid |= int(dtc_bytes[0]) << 16
							dtcid |= int(dtc_bytes[1]) << 8
							dtcid |= int(dtc_bytes[2]) << 0

							dtc = Dtc(dtcid)
							dtc.status.set_byte(dtc_bytes[3])
						elif service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:
							
							dtcid |= int(dtc_bytes[2]) << 16
							dtcid |= int(dtc_bytes[3]) << 8
							dtcid |= int(dtc_bytes[4]) << 0

							dtc = Dtc(dtcid)
							dtc.severity.set_byte(dtc_bytes[0])
							dtc.functional_unit = dtc_bytes[1]
							dtc.status.set_byte(dtc_bytes[5])

						user_response.dtcs.append(dtc)

				actual_byte += dtc_size

			user_response.dtc_count = len(user_response.dtcs)

		elif service.subfunction in response_subfn_number_of_dtc:
			if len(response.data) < 5:
				raise InvalidResponseException(response, 'Response must be exactly 5 bytes long ')

			user_response.status_availability = response.data[1]
			user_response.dtc_format = response.data[2]

			if Dtc.Format.get_name(user_response.dtc_format) is None:
				self.logger.warning('Unknown DTC Format Identifier 0x%02x. Value should be between 0 and 3' % user_response.dtc_format)

			user_response.dtc_count = struct.unpack('>H', response.data[3:5])[0]


		return user_response


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
				msg = "Response gotten from server has a service ID different than the one of the request. Received=0x%02x, Expected=0x%02x" % (response.service.response_id() , request.service.response_id() )
				self.logger.error(msg)
				raise UnexpectedResponseException(response, details=msg)
			
			if not response.positive:
				self.logger.warning("Server responded with Negative response %s" % response.code_name)
				if not request.service.is_supported_negative_response(response.code):
					self.logger.warning("Given response (%s) is not a supported negative response code according to UDS standard." % response.code_name)	
				if validate_response:
					raise NegativeResponseException(response)

			return response