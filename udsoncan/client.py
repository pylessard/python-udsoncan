from udsoncan import Response, Request, services, DidCodec, Routine, IOMasks, Dtc
from udsoncan.exceptions import *
from udsoncan.configs import default_client_config
import struct
import logging
import math
import binascii

# This object is returned for every ReadDiagnosticInformation subfunction and 
# contains the response data from the server. Every subfunctions partly-populate this object.
# It gives some consistency in return format across the 21 subfunctions.
class DTCServerRepsonseContainer(object):
	def __init__(self):
		self.dtcs = []
		self.dtc_count = 0
		self.dtc_format = None
		self.status_availability = None
		self.dtc_snapshot_map = {}
		self.extended_data = []


class Client:
	def __init__(self, conn, config=default_client_config, request_timeout = 1, heartbeat  = None):
		self.conn = conn
		self.request_timeout = request_timeout
		self.config = dict(config) # Makes a copy of given configuration
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
		# No additional data
		response = self.send_request(req)

		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		received = response.data[0]
		expected = service.subfunction_id()
		if received != expected:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received, expected))

		if len(response.data) > 1:
			return response.data[1:]
		return b''

##  SecurityAccess
	def request_seed(self, level):
		service = services.SecurityAccess(level, mode=services.SecurityAccess.Mode.RequestSeed)
		req = Request(service)
		# No additional data

		response = self.send_request(req)
		
		if len(response.data) < 2:
			raise InvalidResponseException(response, "Response data must be at least 2 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()	# Should be the given level with LSB set to 1
		if received != expected:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received, expected))

		return response.data[1:]

	def send_key(self, level, key):
		service = services.SecurityAccess(level, mode=services.SecurityAccess.Mode.SendKey)
		req = Request(service)
		req.data = key
		response = self.send_request(req)
		
		if len(response.data) < 1: 	# Should not happen as response decoder will raise an exception.
			raise InvalidResponseException(response, "Response data must be at least 1 bytes")

		received = int(response.data[0])
		expected = service.subfunction_id()	# Should be the given level with LSB set to 0
		if received != expected:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received, expected))

		return response.positive
	
	# successively request a seed, compute the key and sends it.	
	def unlock_security_access(self, level):
		if 'security_algo' not in self.config or not callable(self.config['security_algo']):
			raise NotImplementedError("Client configuration does not provide a security algorithm")
		
		seed = self.request_seed(level)
		params = self.config['security_algo_params'] if 'security_algo_params' in self.config else None
		key = self.config['security_algo'].__call__(seed, params)
		return self.send_key(level, key)

	# Sends a TesterPresent request to keep the session active.
	def tester_present(self, suppress_positive_response=False):
		service = services.TesterPresent()
		if not isinstance(suppress_positive_response, bool):
			raise ValueError("suppress_positive_response must be a boolean value")
		req = Request(service, suppress_positive_response=suppress_positive_response)
		response = self.send_request(req)
		# No additional data

		if not suppress_positive_response:
			if response.data is None or len(response.data) < 1:
				raise InvalidResponseException(response, "Response data must be at least 1 bytes")

			received = int(response.data[0])
			expected = service.subfunction_id()
			if received != expected:
				raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received, expected))

		return None

	# Make sure that the actual client configuration contains valid definition for given Data Identifiers
	def check_did_config(self, didlist):
		didlist = [didlist] if not isinstance(didlist, list) else didlist
		if 'data_identifiers' not in self.config or  not isinstance(self.config['data_identifiers'], dict):
			raise AttributeError('Configuration does not contains a valid data identifier description.')
		didconfig = self.config['data_identifiers']

		for did in didlist:
			if did not in didconfig:
				raise LookupError('Actual data identifier configuration contains no definition for data identifier 0x%04x' % did)

		return didconfig

	# Make sure that the actual client configuration contains valid definition for given Input/Output Data Identifiers
	def check_io_config(self, didlist):
		didlist = [didlist] if not isinstance(didlist, list) else didlist
		if not 'input_output' in self.config or  not isinstance(self.config['input_output'], dict):
			raise AttributeError('Configuration does not contains an Input/Output section (config[input_output].')
		ioconfigs = self.config['input_output']

		for did in didlist:
			if did not in ioconfigs:
				raise LookupError('Actual Input/Output configuration contains no definition for data identifier 0x%04x' % did)
			if isinstance(ioconfigs[did], dict):	# IO Control services has that concept of composite DID. We define them with dicts.
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

	# Returns the fir DID read if more than one is given.
	def read_data_by_identifier_first(self, did):
		values = self.read_data_by_identifier(did, output_fmt='list')
		if len(values) > 0:
			return values[0]

	# Perform a ReadDataByIdentifier request.
	def read_data_by_identifier(self, dids, output_fmt='dict'):
		service = services.ReadDataByIdentifier(dids)
		self.logger.info("Reading data identifier %s", dids)
		req = Request(service)
		didlist = [service.dids] if not isinstance(service.dids, list) else service.dids

		didconfig = self.check_did_config(didlist)	# Make sure all DID are correctly defined in client config
		req.data = struct.pack('>'+'H'*len(didlist), *didlist) #Encode list of DID
		response = self.send_request(req)

		if output_fmt in ['list']:
			values = []
		elif output_fmt == 'dict':
			values = {}
		else:
			raise ValueError("Output format cannot be %s. Use list or dict" % output_fmt)

		# Parsing algorith to extract DID value
		offset = 0
		received = {}
		for did in didlist:
			received[did] = False
		
		while True:
			if len(response.data) <= offset:
				break	# Done

			if len(response.data) <= offset +1:
				if self.config['tolerate_zero_padding'] and response.data[-1] == 0:	# One extra byte, but its a 0 and we accept that. So we're done
					break
				raise UnexpectedResponseException(response, "Response given by server is incomplete.")

			did = struct.unpack('>H', response.data[offset:offset+2])[0]	# Get the DID number
			if did == 0 and did not in didconfig and self.config['tolerate_zero_padding']: # We read two zeros and that is not a DID bu we accept that. So we're done.
				if response.data[offset:] == b'\x00' * (len(response.data) - offset):
					break

			if did not in didlist:	# We didn't request that DID. Server is confused
				raise UnexpectedResponseException(response, "Server returned a value for data identifier 0x%04x which was not requested" % did)

			if did not in didconfig:	# Already checked in check_did_config. Paranoid check
				raise LookupError('Actual data identifier configuration contains no definition for data identifier 0x%04x' % did)
			
			codec = DidCodec.from_config(didconfig[did])
			offset+=2

			if len(response.data) < offset+len(codec):
				raise UnexpectedResponseException(response, "Value fo data identifier 0x%04x was incomplete according to definition in configuration" % did)

			subpayload = response.data[offset:offset+len(codec)]
			offset += len(codec)	# Codec must define a __len__ function that metches the encoded payload length.
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

	# PErforms a WriteDataByIdentifier request.
	def write_data_by_identifier(self, did, value):
		service = services.WriteDataByIdentifier(did)
		self.logger.info("Writing data identifier %s", did)
		req = Request(service)
		
		didconfig = self.check_did_config(did)		# Make sure DID is configured in client configuration
		req.data = struct.pack('>H', service.did)	# encode DID number

		codec = DidCodec.from_config(didconfig[did])
		req.data += codec.encode(value)
		response = self.send_request(req)

		if len(response.data) < 2:
			raise InvalidResponseException(response, "Response must be at least 2 bytes long")

		did_fb = struct.unpack(">H", response.data[0:2])[0]

		if did_fb != did:
			raise UnexpectedResponseException(response, "Server returned a response for data identifier 0x%02x while client requested for did 0x%02x" % (did_fb, did))
		
		return None

	# Performs a ECUReset service request
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

		return None

	# Performs a ClearDTC service request. 
	def clear_dtc(self, group=0xFFFFFF, suppress_positive_response=False):
		service = services.ClearDiagnosticInformation(group)
		request = Request(service, suppress_positive_response=suppress_positive_response)
		group = service.group  # Service object can filter that value

		hb = (group >> 16) & 0xFF
		mb = (group >> 8) & 0xFF
		lb = (group >> 0) & 0xFF 

		request.data = struct.pack("BBB", hb,mb,lb)
		response = self.send_request(request)

		return None

	# Performs a RoutineControl Service request
	def start_routine(self, routine_id, data=None):
		self.logger.info("Sending request to start %s routine" % (Routine.name_from_id(routine_id)))
		return self.routine_control(routine_id, services.RoutineControl.startRoutine, data)

	# Performs a RoutineControl Service request
	def stop_routine(self, routine_id, data=None):
		self.logger.info("Sending request to stop %s routine" % (Routine.name_from_id(routine_id)))
		return self.routine_control(routine_id, services.RoutineControl.stopRoutine, data)

	# Performs a RoutineControl Service request
	def get_routine_result(self, routine_id, data=None):
		self.logger.info("Sending request to get results of %s routine" % (Routine.name_from_id(routine_id)))
		return self.routine_control(routine_id, services.RoutineControl.requestRoutineResults, data)

	# Performs a RoutineControl Service request
	def routine_control(self, routine_id, control_type, data=None):
		service = services.RoutineControl(routine_id, control_type)
		req = Request(service)

		req.data = struct.pack('>H', service.routine_id)

		# Data can be optionally be given to server. Implementation specific
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

		return response.data

	# Performs an AccessTimingParameter service request
	def read_extended_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.readExtendedTimingParameterSet)

	# Performs an AccessTimingParameter service request
	def read_active_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.readCurrentlyActiveTimingParameters)

	# Performs an AccessTimingParameter service request
	def set_timing_parameters(self, params):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.setTimingParametersToGivenValues, request_record=params)
	
	# Performs an AccessTimingParameter service request
	def reset_default_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.setTimingParametersToDefaultValues)
	
	# Performs an AccessTimingParameter service request
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
			return b''

	# Performs a CommunicationControl service request
	def communication_control(self, control_type, communication_type):
		service = services.CommunicationControl(control_type, communication_type)
		req = Request(service)
		req.data = service.communication_type.get_byte()  # subnet and message type

		response = self.send_request(req)

		if len(response.data) < 1: 	
			raise InvalidResponseException(response, "Response data must be at least 1 byte")

		received = int(response.data[0])
		expected = service.subfunction_id()

		if received != expected:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (received, expected))

		return None

	#Performs a RequestDownload service request
	def request_download(self, memory_location, dfi=None):
		return self.request_upload_download(services.RequestDownload, memory_location, dfi)

	#Performs a RequestUpload service request
	def request_upload(self, memory_location, dfi=None):
		return self.request_upload_download(services.RequestUpload, memory_location, dfi)

	# Common code for both RequestDownload and RequestUpload services
	def request_upload_download(self, service_cls, memory_location, dfi=None):
		if service_cls not in [services.RequestDownload, services.RequestUpload]:
			raise ValueError('services must eitehr be RequestDownload or RequestUpload')

		service = service_cls(memory_location=memory_location, dfi=dfi)
		req = Request(service)

		# If user does not specify a byte format, we apply the one in client configuration.
		if 'server_address_format' in self.config:
			service.memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			service.memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		req.data=b""
		req.data += service.dfi.get_byte()	# Data Format Identifier
		req.data += service.memory_location.alfid.get_byte()	# AddressAndLengthFormatIdentifier
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
			remaining_data = response.data[next_byte:]
			size_ok = True 
			
			if len(remaining_data) > len(codec):
				if remaining_data[len(codec):] == b'\x00' * (len(remaining_data) - len(codec)):
					if self.config['tolerate_zero_padding']:
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

	def control_dtc_setting(self, setting_type, data=None):
		service = services.ControlDTCSetting(setting_type, data)
		req = Request(service)

		if service.data is not None:
			req.data = service.data

		response = self.send_request(req)

		if len(response.data) < 1:
			raise InvalidResponseException(response, 'Response data must be at least 1 byte, received %d bytes' % len(response.data))

		received = response.data[0]
		expected = service.setting_type

		if received != expected:
			raise UnexpectedResponseException(response, "Setting type of response (0x%02x) does not match request control type (0x%02x)" % (received, expected))

		return response

	def read_memory_by_address(self, memory_location):
		service = services.ReadMemoryByAddress(memory_location)

		if 'server_address_format' in self.config:
			service.memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			service.memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		req = Request(service)

		req.data = b''
		req.data += service.memory_location.alfid.get_byte() # AddressAndLengthFormatIdentifier
		req.data += service.memory_location.get_address_bytes()
		req.data += service.memory_location.get_memorysize_bytes()

		response = self.send_request(req)

		if len(response.data) < memory_location.memorysize:
			raise UnexpectedResponseException(response, 'Data block given by the server is too short. Client requested for %d bytes but only received %d bytes' % (memory_location.memorysize, len(response.data)))

		if len(response.data) > memory_location.memorysize:
			extra_bytes = len(response.data) - memory_location.memorysize
			if response.data[memory_location.memorysize:] == b'\x00' * extra_bytes and self.config['tolerate_zero_padding']:
				response.data = response.data[0:memory_location.memorysize]	# trim exceeding zeros
			else:
				raise UnexpectedResponseException(response, 'Data block given by the server is too long. Client requested for %d bytes but received %d bytes' % (memory_location.memorysize, len(response.data)))

		return response.data

	def write_memory_by_address(self, memory_location, data):
		service = services.WriteMemoryByAddress(memory_location, data)

		if 'server_address_format' in self.config:
			service.memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			service.memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		req = Request(service)

		if len(service.data) != service.memory_location.memorysize:
			self.logger.warning('WriteMemoryByAddress: data block length (%d bytes) does not match MemoryLocation size (%d bytes)' % (len(service.data, service.memory_location.memorysize)))

		alfid_byte 			= service.memory_location.alfid.get_byte()   # AddressAndLengthFormatIdentifier
		address_bytes 		= service.memory_location.get_address_bytes()
		memorysize_bytes 	=  service.memory_location.get_memorysize_bytes()

		req.data = alfid_byte + address_bytes + memorysize_bytes + service.data

		response = self.send_request(req)

		expected_response_size = len(alfid_byte) + len(address_bytes) + len(memorysize_bytes)
		if len(response.data) < expected_response_size:
			raise InvalidResponseException(response, 'Repsonse should be at least %d bytes' % (expected_response_size))

		offset = 0
		# We make sure that the echo from the server matches the request we sent.
		response_alfid_byte = response.data[offset:offset+len(alfid_byte)]
		offset += len(alfid_byte)
		if response_alfid_byte != alfid_byte:
			raise UnexpectedResponseException(response, 'AddressAndLengthFormatIdentifier echoed back by the server (%s) does not match the one requested by the client (%s)' % (binascii.hexlify(response_alfid_byte), binascii.hexlify(alfid_byte)) )
		
		response_address_bytes = response.data[offset:offset+len(address_bytes)]
		offset+=len(address_bytes)
		if response_address_bytes != address_bytes:
			raise UnexpectedResponseException(response, 'Address echoed back by the server (%s) does not match the one requested by the client (%s)' % (binascii.hexlify(response_address_bytes), binascii.hexlify(address_bytes)) )

		response_memorysize_bytes = response.data[offset:offset+len(memorysize_bytes)]
		offset+=len(memorysize_bytes)
		if response_memorysize_bytes != memorysize_bytes:
			raise UnexpectedResponseException(response, 'Memory size echoed back by the server (%s) does not match the one requested by the client (%s)' % (binascii.hexlify(response_memorysize_bytes), binascii.hexlify(memorysize_bytes)) )

		return response

# ====  ReadDTCInformation
	def get_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCByStatusMask, status_mask=status_mask)

	def get_emission_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportEmissionsRelatedOBDDTCByStatusMask, status_mask=status_mask)

	def get_mirrormemory_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportMirrorMemoryDTCByStatusMask, status_mask=status_mask)

	def get_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)

	def get_number_of_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportNumberOfDTCByStatusMask, status_mask=status_mask)
	
	def get_mirrormemory_number_of_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportNumberOfMirrorMemoryDTCByStatusMask, status_mask=status_mask)
	
	def get_number_of_emission_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportNumberOfEmissionsRelatedOBDDTCByStatusMask, status_mask=status_mask)

	def get_number_of_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		return self.read_dtc_information(services.ReadDTCInformation.reportNumberOfDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)
	
	def get_dtc_severity(self, dtc):
		return self.read_dtc_information(services.ReadDTCInformation.reportSeverityInformationOfDTC, dtc=dtc)

	def get_supported_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportSupportedDTCs)

	def get_first_test_failed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportFirstTestFailedDTC)

	def get_first_confirmed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportFirstConfirmedDTC)

	def get_most_recent_test_failed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportMostRecentTestFailedDTC)

	def get_most_recent_confirmed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportMostRecentConfirmedDTC)

	def get_dtc_with_permanent_status(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCWithPermanentStatus)

	def get_dtc_fault_counter(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCFaultDetectionCounter)

	def get_dtc_snapshot_identification(self):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCSnapshotIdentification)

	def get_dtc_snapshot_by_dtc_number(self, dtc, record_number=0xFF):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCSnapshotRecordByDTCNumber, dtc=dtc, snapshot_record_number=record_number)

	def get_dtc_snapshot_by_record_number(self, record_number):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCSnapshotRecordByRecordNumber, snapshot_record_number=record_number)

	def get_dtc_extended_data_by_dtc_number(self, dtc, record_number=0xFF, data_size = None):
		return self.read_dtc_information(services.ReadDTCInformation.reportDTCExtendedDataRecordByDTCNumber, dtc=dtc, extended_data_record_number=record_number,data_size=data_size)

	def get_mirrormemory_dtc_extended_data_by_dtc_number(self, dtc, record_number=0xFF, data_size = None):
		return self.read_dtc_information(services.ReadDTCInformation.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber, dtc=dtc, extended_data_record_number=record_number, data_size=data_size)

	# Performs a ReadDiagnsticInformation service request.
	# Many request are encoded the same way and many response are encoded the same way. Request grouping and response grouping are independent.

	def read_dtc_information(self, subfunction, status_mask=None, severity_mask=None,  dtc=None, snapshot_record_number=None, extended_data_record_number=None, data_size=None):
		# Process params		
		if status_mask is not None and isinstance(status_mask, Dtc.Status):
			status_mask = status_mask.get_byte_as_int()

		if severity_mask is not None and isinstance(severity_mask, Dtc.Severity):
			severity_mask = severity_mask.get_byte_as_int()

		if dtc is not None and isinstance(dtc, Dtc):
			dtc = dtc.id

		# Request grouping for subfunction that have the same request format
		request_subfn_no_param = [
			services.ReadDTCInformation.reportSupportedDTCs,
			services.ReadDTCInformation.reportFirstTestFailedDTC,
			services.ReadDTCInformation.reportFirstConfirmedDTC,
			services.ReadDTCInformation.reportMostRecentTestFailedDTC,
			services.ReadDTCInformation.reportMostRecentConfirmedDTC,
			services.ReadDTCInformation.reportDTCFaultDetectionCounter,
			services.ReadDTCInformation.reportDTCWithPermanentStatus,

			# Documentation is confusing about reportDTCSnapshotIdentification subfunction.
			# It is presented with reportDTCSnapshotRecordByDTCNumber (2 params) but a footnote says that these 2 parameters
			# are not to be provided for reportDTCSnapshotIdentification. Therefore, it is the same as other no-params subfn
			services.ReadDTCInformation.reportDTCSnapshotIdentification	

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

		# Response grouping for responses that are encoded the same way
		response_subfn_dtc_availability_mask_plus_dtc_record = [
			services.ReadDTCInformation.reportDTCByStatusMask,
			services.ReadDTCInformation.reportSupportedDTCs,
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
		
		response_subfn_dtc_plus_fault_counter = [
			services.ReadDTCInformation.reportDTCFaultDetectionCounter
		]

		response_subfn_dtc_plus_sapshot_record = [
			services.ReadDTCInformation.reportDTCSnapshotIdentification
		]

		response_sbfn_dtc_status_snapshots_records = [
			services.ReadDTCInformation.reportDTCSnapshotRecordByDTCNumber
		]

		response_sbfn_dtc_status_snapshots_records_record_first = [
			services.ReadDTCInformation.reportDTCSnapshotRecordByRecordNumber
		]

		response_subfn_mask_record_plus_extdata = [
			services.ReadDTCInformation.reportDTCExtendedDataRecordByDTCNumber,
			services.ReadDTCInformation.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber
		]

		# Craft Request and validate input params according the request group.

		service = services.ReadDTCInformation(subfunction)
		req = Request(service)

		if service.subfunction in request_subfn_no_param:		# Service ID + Subfunction
			pass

		elif service.subfunction in request_subfn_status_mask:
			if status_mask is None:
				raise ValueError('status_mask must be provided for subfunction 0x%02x' % service.subfunction)
				
			if not isinstance(status_mask, int) or status_mask < 0 or status_mask > 0xFF:
				raise ValueError('status_mask must be a Dtc.Status instance or an integer between 0 and 0xFF')

			req.data = struct.pack('B', (status_mask & 0xFF))

		elif service.subfunction in request_subfn_mask_record_plus_snapshot_record_number:
			if dtc is None:
				raise ValueError('A dtc value must be provided for subfunction 0x%02x' % service.subfunction)

			if not isinstance(dtc, int) or (isinstance(dtc, int) and (dtc < 0 or dtc > 0xFFFFFF)):
				raise ValueError('dtc parameter must be an instance of Dtcor an integer between 0 and 0xFFFFFF')

			if snapshot_record_number is None:
				raise ValueError('snapshot_record_number must be provided for subfunction 0x%02x' % service.subfunction)

			if not isinstance(snapshot_record_number, int) or (isinstance(snapshot_record_number, int) and (snapshot_record_number < 0 or snapshot_record_number > 0xFF)):
				raise ValueError('snapshot_record_number must be an integer between 0 and 0xFF')

			req.data = b''
			req.data += struct.pack('B', (dtc >> 16) & 0xFF)
			req.data += struct.pack('B', (dtc >> 8) & 0xFF)
			req.data += struct.pack('B', (dtc >> 0) & 0xFF)
			req.data += struct.pack('B', snapshot_record_number)

		elif service.subfunction in request_subfn_snapshot_record_number:
			if snapshot_record_number is None:
				raise ValueError('snapshot_record_number must be provided for subfunction 0x%02x' % service.subfunction)

			if not isinstance(snapshot_record_number, int) or (isinstance(snapshot_record_number, int) and (snapshot_record_number < 0 or snapshot_record_number > 0xFF)):
				raise ValueError('snapshot_record_number must be an integer between 0 and 0xFF')

			req.data = struct.pack('B', snapshot_record_number)

		elif service.subfunction in request_subfn_mask_record_plus_extdata_record_number:
			if dtc is None:
				raise ValueError('A dtc value must be provided for subfunction 0x%02x' % service.subfunction)

			if not isinstance(dtc, int) or dtc < 0 or dtc > 0xFFFFFF:
				raise ValueError('dtc parameter must be an instance of Dtcor an integer between 0 and 0xFFFFFF')

			if extended_data_record_number is None:
				raise ValueError('extended_data_record_number must be provided for subfunction 0x%02x' % service.subfunction)

			if not isinstance(extended_data_record_number, int) or (isinstance(extended_data_record_number, int) and (extended_data_record_number < 0 or extended_data_record_number > 0xFF)):
				raise ValueError('extended_data_record_number must be an integer between 0 and 0xFF')
			if data_size is None and 'extended_data_size' in self.config and dtc in self.config['extended_data_size']:
				data_size = self.config['extended_data_size'][dtc]
			
			if data_size is None:
				raise ValueError('data_size must be provided or config[extended_data_size][dtc] must be set as length of data is not given by the server.')

			if not isinstance(data_size, int) or (isinstance(data_size, int) and data_size <= 0):
				raise ValueError('data_size or config[extended_data_size][dtc] must be a non-zero positive integer')

			req.data = b''
			req.data += struct.pack('B', (dtc >> 16) & 0xFF)
			req.data += struct.pack('B', (dtc >> 8) & 0xFF)
			req.data += struct.pack('B', (dtc >> 0) & 0xFF)
			req.data += struct.pack('B', extended_data_record_number)

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

		# Request is crafted. Send it to server and get response.

		response = self.send_request(req)
		user_response = DTCServerRepsonseContainer()	# what will be returned 
		
		if len(response.data) < 1:
			raise InvalidResponseException(response, 'Response must be at least 1 byte long (echo of subfunction)')

		# Parse and validate response
		response_subfn = int(response.data[0])	# First byte is subfunction

		if response_subfn != service.subfunction:
			raise UnexpectedResponseException(response, 'Echo of ReadDTCInformation subfunction gotten from server(0x%02x) does not match the value in the request subfunction (0x%02x)' % (response_subfn, service.subfunction))	

		# Now for each response group, we have a different decoding algorithm
		if service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record + response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:

			if service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record:
				dtc_size = 4	# DTC ID (3) + Status (1)
			elif service.subfunction in response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:
				dtc_size = 6	# DTC ID (3) + Status (1) + Severity (1) + FunctionalUnit (1)

			if len(response.data) < 2:
				raise InvalidResponseException(response, 'Response must be at least 2 byte long (echo of subfunction and DTCStatusAvailabilityMask)')

			user_response.status_availability = response.data[1]

			actual_byte = 2	# Increasing index

			while True:	# Loop until we have read all dtc
				if len(response.data) <= actual_byte:
					break	# done

				elif len(response.data) < actual_byte+dtc_size:
					partial_dtc_length = len(response.data)-actual_byte
					if self.config['tolerate_zero_padding'] and response.data[actual_byte:] == b'\x00'*partial_dtc_length:
						break
					else:
						# We purposely ignore extra byte for subfunction reportSeverityInformationOfDTC as it is supposed to returns 0 or 1 DTC.
						if service.subfunction != services.ReadDTCInformation.reportSeverityInformationOfDTC or actual_byte == 2: 
							raise InvalidResponseException(response, 'Incomplete DTC record. Missing %d bytes to response to complete the record' % (dtc_size-partial_dtc_length))

				else:
					dtc_bytes = response.data[actual_byte:actual_byte+dtc_size]
					if dtc_bytes == b'\x00'*dtc_size and self.config['ignore_all_zero_dtc']:
						pass # ignore
					else:
						# DTC decoding				
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

		# The 2 following subfunctions response have different purpose but their construction is very similar.
		elif service.subfunction in response_subfn_dtc_plus_fault_counter + response_subfn_dtc_plus_sapshot_record:
			dtc_size = 4
			if len(response.data) < 1:
				raise InvalidResponseException(response, 'Response must be at least 1 byte long (echo of subfunction)')

			actual_byte = 1 	# Increasing index
			dtc_map = dict()	# This map is used to append snapshot to existing DTC.

			while True: 	# Loop until we have read all dtc
				if len(response.data) <= actual_byte:
					break 	# done

				elif len(response.data) < actual_byte+dtc_size:
					partial_dtc_length = len(response.data)-actual_byte
					if self.config['tolerate_zero_padding'] and response.data[actual_byte:] == b'\x00'*partial_dtc_length:
						break
					else:
						raise InvalidResponseException(response, 'Incomplete DTC record. Missing %d bytes to response to complete the record' % (dtc_size-partial_dtc_length))
				else:
					dtc_bytes = response.data[actual_byte:actual_byte+dtc_size]
					if dtc_bytes == b'\x00'*dtc_size and self.config['ignore_all_zero_dtc']:
						pass # ignore
					else:		
						# DTC decoding

						dtcid = 0
						dtcid |= int(dtc_bytes[0]) << 16
						dtcid |= int(dtc_bytes[1]) << 8
						dtcid |= int(dtc_bytes[2]) << 0

						# We create the DTC or get its reference if already created.
						dtc_created = False	
						if dtcid in dtc_map and service.subfunction in response_subfn_dtc_plus_sapshot_record:
							dtc = dtc_map[dtcid]
						else:
							dtc = Dtc(dtcid)
							dtc_map[dtcid] = dtc
							dtc_created = True

						# We either read the DTC fault counter or Snapshot record number. 
						if service.subfunction in response_subfn_dtc_plus_fault_counter:
							dtc.fault_counter = dtc_bytes[3]

							if dtc.fault_counter >= 0x7F or dtc.fault_counter < 0x01:
								self.logger.warning('Server returned a fault counter value of 0x%02x for DTC id 0x%06x while value should be between 0x01 and 0x7E.' % (dtc.fault_counter, dtc.id))

						elif service.subfunction in response_subfn_dtc_plus_sapshot_record:
							record_number = dtc_bytes[3]

							if dtc.snapshots is None:
								dtc.snapshots = []

							dtc.snapshots.append(record_number)
						
						# Adds the DTC to the list.
						if dtc_created:
							user_response.dtcs.append(dtc)
							
				actual_byte += dtc_size

			user_response.dtc_count = len(user_response.dtcs)

		# This group of response returns a number of DTC available
		elif service.subfunction in response_subfn_number_of_dtc:
			if len(response.data) < 5:
				raise InvalidResponseException(response, 'Response must be exactly 5 bytes long ')

			user_response.status_availability = response.data[1]
			user_response.dtc_format = response.data[2]

			if Dtc.Format.get_name(user_response.dtc_format) is None:
				self.logger.warning('Unknown DTC Format Identifier 0x%02x. Value should be between 0 and 3' % user_response.dtc_format)

			user_response.dtc_count = struct.unpack('>H', response.data[3:5])[0]
		
		# This group of response returns DTC snapshots
		# Response include a DTC, many snapshots records. For each records, we find many Data Identifier.
		# We create one Dtc.Snapshot for each DID. That'll be easier to work with.
		# <DTC,RecordNumber1,NumberOfDid_X,DID1,DID2,...DIDX, RecordNumber2,NumberOfDid_Y,DID1,DID2,...DIDY, etc>
		elif service.subfunction in response_sbfn_dtc_status_snapshots_records :
			if len(response.data) < 5:
				raise InvalidResponseException(response, 'Response must be at least 5 bytes long ')

			# DTC decoding
			dtcid = 0
			dtcid |= int(response.data[1]) << 16
			dtcid |= int(response.data[2]) << 8
			dtcid |= int(response.data[3]) << 0

			# This response is triggered by a request that included a DTC number
			if dtc != dtcid:
				error_msg = 'Server returned snapshot with DTC ID 0x%06x while client requested for 0x%06x' % (dtcid, dtc)
				raise UnexpectedResponseException(response, error_msg)

			dtc = Dtc(dtcid)
			dtc.status.set_byte(response.data[4])

			actual_byte = 5		# Increasing index

			# This configuration exists to overcome a lack of explanation in the documentation.
			if self.config['dtc_snapshot_did_size'] > 8 or self.config['dtc_snapshot_did_size'] < 1:
				raise RuntimeError('Configuration "dtc_snapshot_did_size" must be an integer between 1 and 8')

			while True:		# Loop until we have read all dtc
				if len(response.data) <= actual_byte:
					break	# done

				remaining_data = response.data[actual_byte:]
				if self.config['tolerate_zero_padding'] and remaining_data == b'\x00' * len(remaining_data):
					break
					
				if len(remaining_data) < 2:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing "number of identifier" and following data')

				record_number = remaining_data[0]	
				number_of_did = remaining_data[1]
				# Validate record number and number of DID before continuing
				if number_of_did == 0:
					error_msg = 'Server returned snapshot record #%d with no data identifier included' % (record_number)
					self.logger.warning(error_msg)
					raise InvalidResponseException(response, error_msg) 

				if (snapshot_record_number != 0xFF and record_number != snapshot_record_number):
					error_msg = 'Server returned snapshot with record number 0x%02x while client requested for 0x%02x' % (record_number, snapshot_record_number)
					self.logger.warning(error_msg)
					raise UnexpectedResponseException(response, error_msg) 

				if len(remaining_data) < 2 + self.config['dtc_snapshot_did_size']:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing DID number and associated data.')

				actual_byte += 2
				for i in range(number_of_did):
					remaining_data = response.data[actual_byte:]
					snapshot = Dtc.Snapshot()	# One snapshot per DID for convenience.
					snapshot.record_number = record_number

					# As standard does not specify the length of the DID, we craft it based on a config 
					did = 0
					for j in range(self.config['dtc_snapshot_did_size']):
						offset = self.config['dtc_snapshot_did_size']-1-j
						did |= (remaining_data[offset] << (8*j))
					
					# Decode the data based on DID number.
					snapshot.did = did
					didconfig = self.check_did_config(did)
					codec = DidCodec.from_config(didconfig[did])
					
					data_offset =  self.config['dtc_snapshot_did_size'];
					if len(remaining_data[data_offset:]) < len(codec):
						raise InvalidResponseException(response, 'Incomplete response. Data for DID 0x%04x is only %d bytes while %d bytes is expected' % (did, len(remaining_data[data_offset:]), len(codec)))

					snapshot.raw_data = remaining_data[data_offset:data_offset + len(codec)]
					snapshot.data = codec.decode(snapshot.raw_data)

					dtc.snapshots.append(snapshot)

					actual_byte += self.config['dtc_snapshot_did_size'] + len(codec)


			user_response.dtcs.append(dtc)
			user_response.dtc_count = 1
		
		# This group of response returns DTC snapshots
		# Response include a DTC, many snapshots records. For each records, we find many Data Identifier.
		# We create one Dtc.Snapshot for each DID. That'll be easier to work with.
		# Similar to previous subfunction group, but order of information is changed.

		# <RecordNumber1, DTC1,NumberOfDid_X,DID1,DID2,...DIDX, RecordNumber2,DTC2, NumberOfDid_Y,DID1,DID2,...DIDY, etc>
		elif service.subfunction in response_sbfn_dtc_status_snapshots_records_record_first :
			if len(response.data) < 2:
				raise InvalidResponseException(response, 'Response must be at least 2 bytes long. Subfunction echo + RecordNumber ')

			actual_byte = 1	 # Increasing index
			while True:	# Loop through response data
				if len(response.data) <= actual_byte:
					break	# done

				remaining_data = response.data[actual_byte:]
				record_number = remaining_data[0]

				# If empty response but filled with 0, it is considered ok
				if remaining_data == b'\x00' * len(remaining_data) and self.config['tolerate_zero_padding']:
					break

				# If record number does not match our request.
				if (snapshot_record_number != 0xFF and record_number != snapshot_record_number):
					error_msg = 'Server returned snapshot with record number 0x%02x while client requested for 0x%02x' % (record_number, snapshot_record_number)
					self.logger.warning(error_msg)
					raise UnexpectedResponseException(response, error_msg)

				# If record number received but no DTC provided (allowed according to standard), we exit.
				if len(remaining_data) == 1 or self.config['tolerate_zero_padding'] and remaining_data[1:] == b'\x00' * len(remaining_data[1:]):
					break

				if len(remaining_data) < 5: 	# Partial DTC (No DTC at all is checked above)
					raise InvalidResponseException(response, 'Incomplete response from server. Missing "DTCAndStatusRecord" and following data')

				if len(remaining_data) < 6:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing number of data identifier')

				# DTC decoding
				dtcid = 0
				dtcid |= int(remaining_data[1]) << 16
				dtcid |= int(remaining_data[2]) << 8
				dtcid |= int(remaining_data[3]) << 0

				dtc = Dtc(dtcid)
				dtc.status.set_byte(remaining_data[4])

				number_of_did = remaining_data[5]

				actual_byte += 6
				remaining_data = response.data[actual_byte:]

				# Validate number of DID and DID size
				if self.config['dtc_snapshot_did_size'] > 8 or self.config['dtc_snapshot_did_size'] < 1:
					raise RuntimeError('Configuration "dtc_snapshot_did_size" must be an integer between 1 and 8')

				if number_of_did == 0:
					error_msg = 'Server returned snapshot record #%d with no data identifier included' % (record_number)
					self.logger.warning(error_msg)
					raise InvalidResponseException(response, error_msg) 

				if len(remaining_data) < self.config['dtc_snapshot_did_size']:
					error_msg = 'Incomplete response from server. Missing DID and associated data'
					raise InvalidResponseException(response, error_msg)

				# We have a DTC and 0 DID, next loop
				if self.config['tolerate_zero_padding'] and remaining_data == b'\x00' * len(remaining_data):
					break

				# For each DID
				for i in range(number_of_did):
					remaining_data = response.data[actual_byte:]
					snapshot = Dtc.Snapshot()	# One snapshot epr DID for convenience
					snapshot.record_number = record_number

					# As standard does not specify the length of the DID, we craft it based on a config 
					did = 0
					for j in range(self.config['dtc_snapshot_did_size']):
						offset = self.config['dtc_snapshot_did_size']-1-j
						did |= (remaining_data[offset] << (8*j))
					
					# Decode the data based on DID number.
					snapshot.did = did
					didconfig = self.check_did_config(did)
					codec = DidCodec.from_config(didconfig[did])
					
					data_offset =  self.config['dtc_snapshot_did_size'];
					if len(remaining_data[data_offset:]) < len(codec):
						raise InvalidResponseException(response, 'Incomplete response. Data for DID 0x%04x is only %d bytes while %d bytes is expected' % (did, len(remaining_data[data_offset:]), len(codec)))

					snapshot.raw_data = remaining_data[data_offset:data_offset + len(codec)]
					snapshot.data = codec.decode(snapshot.raw_data)

					dtc.snapshots.append(snapshot)

					actual_byte += self.config['dtc_snapshot_did_size'] + len(codec)


				user_response.dtcs.append(dtc)
			user_response.dtc_count = len(user_response.dtcs)

		# These subfunction include DTC ExtraData. We give it raw to user.
		elif service.subfunction in response_subfn_mask_record_plus_extdata:

			if len(response.data) < 5: 
				raise InvalidResponseException(response, 'Incomplete response from server. Missing DTCAndStatusRecord')
			# DTC decoding
			dtcid = 0
			dtcid |= int(response.data[1]) << 16
			dtcid |= int(response.data[2]) << 8
			dtcid |= int(response.data[3]) << 0

			dtc = Dtc(dtcid)
			dtc.status.set_byte(response.data[4])

			actual_byte = 5	# Increasing index
			while actual_byte < len(response.data):	# Loop through data
				remaining_data = response.data[actual_byte:]
				record_number = remaining_data[0]

				if record_number == 0:
					if remaining_data == b'\x00' * len(remaining_data) and self.config['tolerate_zero_padding']:
						break
					else:
						raise InvalidResponseException(response, 'Extended data record number given by the server is 0 but this value is a reserved value.')

				if record_number != extended_data_record_number and  extended_data_record_number < 0xF0:	# Standard specifies that values between 0xF0 and 0xFF are for reporting groups (more than one record)
					raise UnexpectedResponseException(response, 'Extended data record number given by the server (0x%02x) does not match the record number requested by the client (0x%02x)' % (record_number, extended_data_record_number))

				actual_byte +=1
				remaining_data = response.data[actual_byte:]
				if len(remaining_data) < data_size:
					raise InvalidResponseException(response, 'Incomplete response from server. Length of extended data for DTC 0x%06x with record number 0x%02x is %d bytes but smaller than given data_size of %d bytes' % (dtcid, record_number, len(remaining_data), data_size))

				exdata = Dtc.ExtendedData()
				exdata.record_number = record_number
				exdata.raw_data = remaining_data[0:data_size]

				dtc.extended_data.append(exdata)

				actual_byte+= data_size

			user_response.dtcs.append(dtc)
			user_response.dtc_count = len(user_response.dtcs)

		return user_response

	# Basic transmission of request. This will need to be improved
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
			self.last_response = response
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