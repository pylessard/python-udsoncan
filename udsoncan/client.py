from udsoncan import Response, Request, services, DidCodec, Routine, IOMasks, Dtc, DataIdentifier, MemoryLocation
from udsoncan.exceptions import *
from udsoncan.configs import default_client_config
import struct
import logging
import math
import binascii
import traceback

class Client:

	def __init__(self, conn, config=default_client_config, request_timeout = 1):
		self.conn = conn
		self.request_timeout = request_timeout
		self.config = dict(config) # Makes a copy of given configuration

		self.refresh_config()

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

	def configure_logger(self):
		logger_name = 'UdsClient'
		if 'logger_name' in self.config:
			logger_name = "UdsClient[%s]" % self.config['logger_name']

		self.logger = logging.getLogger(logger_name)

	def set_config(self, key, value):
		self.config[key] = value
		self.refresh_config()

	def refresh_config(self):
		self.configure_logger()
	
	# Decorator to apply on functions that the user will call.
	# Each functions raises exceptions. This decorator handle these exception, log them, 
	# then suppress them or not depending on the client configuration.
	# There is a security mechanism to avoid nesting try_catch by calling a decorated function from another decorated function.
	# if func1 and func2 are decorated and func2 calls func1, it should be done this way : self.func1._func_no_error_management(self, ...)
	def standard_error_management(func):
		def norecurse(f):	
			def func(*args, **kwargs):
				if len([l[2] for l in traceback.extract_stack() if l[2] == f.__name__]) > 0:
					raise RuntimeError('Recursion within the error management system.')
				return f(*args, **kwargs)
			return func

		@norecurse
		# Long name to minimize chances of name collision
		def client_standard_error_management_decorated_fn(self, *args, **kwargs):
			try:
				return func(self, *args, **kwargs)
			
			except NegativeResponseException as e:
				e.positive = False
				if self.config['exception_on_negative_response']:
					logline = '[%s] : %s' % (e.__class__.__name__, str(e))
					self.logger.warning(logline)
					raise
				else:
					self.logger.warning(str(e))
					return e.response
			
			except InvalidResponseException as e:
				e.response.valid = False
				if self.config['exception_on_invalid_response']:
					self.logger.error('[%s] : %s' % (e.__class__.__name__, str(e)))
					raise
				else:
					self.logger.error(str(e))
					return e.response
			
			except UnexpectedResponseException as e:
				e.response.unexpected = True
				if self.config['exception_on_unexpected_response']:
					self.logger.error('[%s] : %s' % (e.__class__.__name__, str(e)))
					raise
				else:
					self.logger.error(str(e))
					return e.response
			
			except Exception as e:
				self.logger.error('[%s] : %s' % (e.__class__.__name__, str(e)))
				raise

		client_standard_error_management_decorated_fn._func_no_error_management = func
		return client_standard_error_management_decorated_fn

	# Performs a DiagnosticSessionControl service request
	@standard_error_management
	def change_session(self, newsession):
		req = services.DiagnosticSessionControl.make_request(newsession)

		named_newsession = '%s (0x%02x)' % (services.DiagnosticSessionControl.Session.get_name(newsession), newsession)
		self.logger.info('Switching session to : %s' % (named_newsession))
		
		response = self.send_request(req)
		services.DiagnosticSessionControl.interpret_response(response)

		if newsession != response.service_data.session_echo:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (response.service_data.session_echo, newsession))

		return response

	# Performs a SecurityAccess service request. Request Seed
	@standard_error_management
	def request_seed(self, level):
		req = services.SecurityAccess.make_request(level, mode=services.SecurityAccess.Mode.RequestSeed)

		self.logger.info('Requesting seed to unlock security access level 0x%02x' % (req.subfunction))	# level may be corrected by service.
		
		response = self.send_request(req)
		services.SecurityAccess.interpret_response(response, mode=services.SecurityAccess.Mode.RequestSeed)

		expected_level = services.SecurityAccess.normalize_level(mode=services.SecurityAccess.Mode.RequestSeed, level=level)
		received_level = response.service_data.security_level_echo
		if expected_level != received_level:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received_level, expected_level))

		self.logger.debug('Received seed : [%s]' % (binascii.hexlify(response.service_data.seed)))
		return response

	# Performs a SecurityAccess service request. Send key
	@standard_error_management
	def send_key(self, level, key):
		req = services.SecurityAccess.make_request(level, mode=services.SecurityAccess.Mode.SendKey, key=key)
		self.logger.info('Sending key to unlock security access level 0x%02x' % (req.subfunction))
		self.logger.debug('Key to send : [%s]' % (binascii.hexlify(key)))

		response = self.send_request(req)
		services.SecurityAccess.interpret_response(response, mode=services.SecurityAccess.Mode.SendKey)

		expected_level = services.SecurityAccess.normalize_level(mode=services.SecurityAccess.Mode.SendKey, level=level)
		received_level = response.service_data.security_level_echo
		if expected_level != received_level:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received_level, expected_level))

		return response
	
	# # Performs 2 SecurityAccess service request. successively request a seed, compute the key and sends it.	
	@standard_error_management
	def unlock_security_access(self, level):
		if 'security_algo' not in self.config or not callable(self.config['security_algo']):
			raise NotImplementedError("Client configuration does not provide a security algorithm")
		
		seed = self.request_seed._func_no_error_management(self, level).service_data.seed
		params = self.config['security_algo_params'] if 'security_algo_params' in self.config else None
		key = self.config['security_algo'].__call__(seed, params)
		return self.send_key._func_no_error_management(self, level, key)

	# Sends a TesterPresent request to keep the session active.
	@standard_error_management
	def tester_present(self):
		req = services.TesterPresent.make_request()

		self.logger.info('Sending TesterPresent request')
		response = self.send_request(req)
		services.TesterPresent.interpret_response(response)

		if req.subfunction != response.service_data.subfunction_echo:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (response.service_data.subfunction_echo, req.subfunction))

		return response

	# Returns the first DID read if more than one is given.
	@standard_error_management
	def read_data_by_identifier_first(self, didlist):
		values = self.read_data_by_identifier(didlist)
		if len(values) > 0 and len(didlist) > 0:
			return values[didlist[0]]

	# Perform a ReadDataByIdentifier request.
	@standard_error_management
	def read_data_by_identifier(self, dids):
		didlist = services.ReadDataByIdentifier.validate_didlist_input(dids)
		req = services.ReadDataByIdentifier.make_request(didlist=didlist, didconfig=self.config['data_identifiers'])

		if len(didlist) == 1:
			self.logger.info("Reading data identifier : %s (%s)" % (didlist[0], DataIdentifier.name_from_id(didlist[0])))
		else:
			self.logger.info("Reading %d data identifier : %s" % (len(didlist), didlist))
		
		if 'data_identifiers' not in self.config or  not isinstance(self.config['data_identifiers'], dict):
			raise AttributeError('Configuration does not contains a valid data identifier description.')

		response = self.send_request(req)
		
		params = {
			'didlist' : didlist, 
			'didconfig' : self.config['data_identifiers'],
			'tolerate_zero_padding' : self.config['tolerate_zero_padding']
			}
		
		try:
			services.ReadDataByIdentifier.interpret_response(response, **params)
		except ConfigError as e:
			if e.key in didlist:
				raise
			else:
				raise UnexpectedResponseException(response, "Server returned values for data identifier 0x%04x that was not requested and no Codec was defined for it. Parsing must be stopped." % (e.key))
		
		set_request_didlist = set(didlist)
		set_response_didlist = set(response.service_data.values.keys())
		extra_did  = set_response_didlist - set_request_didlist
		missing_did  = set_request_didlist - set_response_didlist

		if len(extra_did) > 0:
			raise UnexpectedResponseException(response, "Server returned values for %d data identifier that were not requested. Dids are : %s" % (len(extra_did), extra_did))

		if len(missing_did) > 0:
			raise UnexpectedResponseException(response, "%d data identifier values are missing from server response. Dids are : %s" % (len(missing_did), missing_did))

		return response
		

	# Performs a WriteDataByIdentifier request.
	@standard_error_management
	def write_data_by_identifier(self, did, value):
		req = services.WriteDataByIdentifier.make_request(did, value, didconfig=self.config['data_identifiers'])
		self.logger.info("Writing data identifier %s (%s)", did, DataIdentifier.name_from_id(did))
		
		response = self.send_request(req)
		services.WriteDataByIdentifier.interpret_response(response)

		if response.service_data.did_echo != did:
			raise UnexpectedResponseException(response, "Server returned a response for data identifier 0x%02x while client requested for did 0x%02x" % (response.service_data.did_echo, did))
		
		return response

	# Performs a ECUReset service request
	@standard_error_management
	def ecu_reset(self, reset_type):
		req = services.ECUReset.make_request(reset_type)
		self.logger.info("Requesting ECU reset of type 0x%02x (%s)" % (reset_type, services.ECUReset.ResetType.get_name(reset_type)))
	
		response = self.send_request(req)
		services.ECUReset.interpret_response(response)
		
		if response.service_data.reset_type_echo != reset_type:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (response.service_data.reset_type_echo, reset_type))

		if response.service_data.reset_type_echo == services.ECUReset.ResetType.enableRapidPowerShutDown and response.service_data.powerdown_time != 0xFF:
			self.logger.info('Server will shutdown in %d seconds.' % (response.service_data.powerdown_time))

		return response

	# Performs a ClearDTC service request.
	@standard_error_management 
	def clear_dtc(self, group=0xFFFFFF):
		request = services.ClearDiagnosticInformation.make_request(group)
		if group == 0xFFFFFF:
			self.logger.info('Clearing all DTCs (group mask : 0xFFFFFF)')
		else:
			self.logger.info('Clearing DTCs matching group mask : 0x%06x' % group)

		response = self.send_request(request)
		services.ClearDiagnosticInformation.interpret_response(response)

		return response

	# Performs a RoutineControl Service request
	def start_routine(self, routine_id, data=None):
		return self.routine_control(routine_id, services.RoutineControl.ControlType.startRoutine, data)

	# Performs a RoutineControl Service request
	def stop_routine(self, routine_id, data=None):
		return self.routine_control(routine_id, services.RoutineControl.ControlType.stopRoutine, data)

	# Performs a RoutineControl Service request
	def get_routine_result(self, routine_id, data=None):
		return self.routine_control(routine_id, services.RoutineControl.ControlType.requestRoutineResults, data)

	# Performs a RoutineControl Service request
	@standard_error_management
	def routine_control(self, routine_id, control_type, data=None):
		request = services.RoutineControl.make_request(routine_id, control_type, data=data)
		payload_length = 0 if data is None else len(data)

		self.logger.info("Sending RoutineControl request with control type %s (0x%02x) for Routine ID : 0x%04x (%s) with a payload of %d bytes" % ( services.RoutineControl.ControlType.get_name(control_type), control_type, routine_id, Routine.name_from_id(routine_id), payload_length))

		response = self.send_request(request)
		services.RoutineControl.interpret_response(response)

		if control_type != response.service_data.control_type_echo:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.control_type_echo, control_type))

		if routine_id != response.service_data.routine_id_echo:
			raise UnexpectedResponseException(response, "Response received from server (ID = 0x%02x) is not for the requested routine ID (0x%02x)" % (response.service_data.routine_id_echo, routine_id))

		return response

	# Performs an AccessTimingParameter service request
	def read_extended_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.readExtendedTimingParameterSet)

	# Performs an AccessTimingParameter service request
	def read_active_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.readCurrentlyActiveTimingParameters)

	# Performs an AccessTimingParameter service request
	def set_timing_parameters(self, params):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.setTimingParametersToGivenValues, request_record=params)
	
	# Performs an AccessTimingParameter service request
	def reset_default_timing_parameters(self):
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.setTimingParametersToDefaultValues)
	
	# Performs an AccessTimingParameter service request
	@standard_error_management
	def access_timing_parameter(self, access_type, timing_param_record=None):
		request = services.AccessTimingParameter.make_request(access_type, timing_param_record)
		payload_length = 0 if timing_param_record is None else len(timing_param_record)

		self.logger.info('Sending AccessTimingParameter service request with access type 0x%02x (%s) and a request record payload of %d bytes' % (access_type, services.AccessTimingParameter.AccessType.get_name(access_type), payload_length))

		response = self.send_request(request)
		services.AccessTimingParameter.interpret_response(response)

		if access_type != response.service_data.access_type_echo:
			raise UnexpectedResponseException(response, "Access type of response (0x%02x) does not match request access type (0x%02x)" % (response.service_data.access_type_echo, access_type))

		allowed_response_record_access_type = [
			services.AccessTimingParameter.AccessType.readExtendedTimingParameterSet, 
			services.AccessTimingParameter.AccessType.readCurrentlyActiveTimingParameters
		]

		if len(response.service_data.timing_param_record) > 0 and access_type not in allowed_response_record_access_type:
			self.logger.warning("Server returned data for AccessTimingParameter altough none were asked")

		return response

	# Performs a CommunicationControl service request
	@standard_error_management
	def communication_control(self, control_type, communication_type):
		communication_type = services.CommunicationControl.normalize_communication_type(communication_type)

		request = services.CommunicationControl.make_request(control_type, communication_type)
		self.logger.info('Sending CommunicationControl service request with control type 0x%02x (%s) and a communication type byte of 0x%02x (%s)' % (control_type, services.CommunicationControl.ControlType.get_name(control_type), communication_type.get_byte_as_int(), str(communication_type)))

		response = self.send_request(request)
		services.CommunicationControl.interpret_response(response)

		if control_type != response.service_data.control_type_echo:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.control_type_echo, control_type))

		return response

	#Performs a RequestDownload service request
	def request_download(self, memory_location, dfi=None):
		return self.request_upload_download(services.RequestDownload, memory_location, dfi)

	#Performs a RequestUpload service request
	def request_upload(self, memory_location, dfi=None):
		return self.request_upload_download(services.RequestUpload, memory_location, dfi)

	# Common code for both RequestDownload and RequestUpload services
	@standard_error_management
	def request_upload_download(self, service_cls, memory_location, dfi=None):
		dfi = service_cls.normalize_data_format_identifier(dfi)

		if service_cls not in [services.RequestDownload, services.RequestUpload]:
			raise ValueError('services must either be RequestDownload or RequestUpload')

		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		# If user does not specify a byte format, we apply the one in client configuration.
		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		request = service_cls.make_request(memory_location=memory_location, dfi=dfi)
		self.logger.info('Sending %s service request for memory location [%s] and DataFormatIdentifier 0x%02x (%s)' % (service_cls.__name__, str(memory_location), dfi.get_byte_as_int(), str(dfi)))

		response = self.send_request(request)
		service_cls.interpret_response(response)
		
		return response

	@standard_error_management
	def transfer_data(self, sequence_number, data=None):
		request = services.TransferData.make_request(sequence_number, data)
		
		data_len = 0 if data is None else len(data)
		self.logger.info('Sending TransferData service request with SequenceNumber=%d and %d bytes of data.' % (sequence_number, data_len))
		if data_len > 0:
			self.logger.debug('Data to transfer : %s' % binascii.hexlify(data))
		
		response = self.send_request(request)
		services.TransferData.interpret_response(response)

		if sequence_number != response.service_data.sequence_number_echo:
			raise UnexpectedResponseException(response, "Block sequence number of response (0x%02x) does not match request block sequence number (0x%02x)" % (response.service_data.sequence_number_echo, sequence_number))

		return response

	@standard_error_management
	def request_transfer_exit(self, data=None):
		request = services.RequestTransferExit.make_request(data)
		self.logger.info('Sending RequestTransferExit service request')

		response = self.send_request(request)
		services.RequestTransferExit.interpret_response(response)

		return response

	@standard_error_management
	def link_control(self, control_type, baudrate=None):
		request = services.LinkControl.make_request(control_type, baudrate)
		baudrate_str = 'No baudrate specified' if baudrate is None else 'Baudrate : ' + str(baudrate)
		self.logger.info('Sending LinkControl service request with control type of 0x%02x (%s). %s' % (control_type, services.LinkControl.ControlType.get_name(control_type), baudrate_str))
		
		response = self.send_request(request)
		services.LinkControl.interpret_response(response)
		
		if control_type != response.service_data.control_type_echo:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.control_type_echo, control_type))

		return response

	#Perform InputOutputControlByIdentifier service request
	@standard_error_management
	def io_control(self,  did, control_param=None, values=None, masks=None):
		if 'input_output' not in self.config:
			raise ConfigError('input_output', msg='input_output must be defined in client configuration in order to use InputOutputControlByIdentifier service')

		request = services.InputOutputControlByIdentifier.make_request( did, control_param=control_param, values=values, masks=masks, ioconfig=self.config['input_output'])
		
		control_param_str = 'no control parameter' if control_param is None else 'control parameter 0x%02x (%s)' % (control_param, services.InputOutputControlByIdentifier.ControlParam.get_name(control_param))		
		self.logger.info('Sending InputOutputControlByIdentifier service request for DID=0x%04x, %s.' % (did, control_param_str))

		response = self.send_request(request)
		services.InputOutputControlByIdentifier.interpret_response(response, control_param=control_param, tolerate_zero_padding=self.config['tolerate_zero_padding'], ioconfig=self.config['input_output'])

		if response.service_data.did_echo != did:
			raise UnexpectedResponseException(response, "Echo of the DID number (0x%02x) does not match the value in the request (0x%02x)" % (response.service_data.did_echo, did))

		if control_param != response.service_data.control_param_echo:
			raise UnexpectedResponseException(response, 'Echo of the InputOutputControlParameter (0x%02x) does not match the value in the request (0x%02x)' % (response.service_data.control_param_echo, control_param))	

		return response

	@standard_error_management
	def control_dtc_setting(self, setting_type, data=None):
		request = services.ControlDTCSetting.make_request(setting_type, data)
		data_len = 0 if data is None else len(data)
		self.logger.info('Sending ControlDTCSetting service request with setting type 0x%02x (%s) and %d bytes of data' % (setting_type, services.ControlDTCSetting.SettingType.get_name(setting_type), data_len))

		response = self.send_request(request)
		services.ControlDTCSetting.interpret_response(response)

		if response.service_data.setting_type_echo != setting_type:
			raise UnexpectedResponseException(response, "Setting type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.setting_type_echo, setting_type))

		return response

	@standard_error_management
	def read_memory_by_address(self, memory_location):
		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		request = services.ReadMemoryByAddress.make_request(memory_location)
		self.logger.info('Reading memory address (ReadMemoryByAddress) - %s' % str(memory_location))
		
		response = self.send_request(request)
		services.ReadMemoryByAddress.interpret_response(response)
		memdata = response.service_data.memory_block
		
		if len(memdata) < memory_location.memorysize:
			raise UnexpectedResponseException(response, 'Data block given by the server is too short. Client requested for %d bytes but only received %d bytes' % (memory_location.memorysize, len(response.data)))

		if len(memdata) > memory_location.memorysize:
			extra_bytes = len(memdata) - memory_location.memorysize
			if memdata[memory_location.memorysize:] == b'\x00' * extra_bytes and self.config['tolerate_zero_padding']:
				response.service_data.memory_block = memdata[0:memory_location.memorysize]	# trim exceeding zeros
			else:
				raise UnexpectedResponseException(response, 'Data block given by the server is too long. Client requested for %d bytes but received %d bytes' % (memory_location.memorysize, len(response.data)))

		return response

	@standard_error_management
	def write_memory_by_address(self, memory_location, data):
		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		request = services.WriteMemoryByAddress.make_request(memory_location, data)
		self.logger.info('Writing %d bytes to memory address (WriteMemoryByAddress) - %s' % (len(data), str(memory_location)))

		if len(data) != memory_location.memorysize:
			self.logger.warning('WriteMemoryByAddress: data block length (%d bytes) does not match MemoryLocation size (%d bytes)' % (len(data, memory_location.memorysize)))

		response = self.send_request(request)
		services.WriteMemoryByAddress.interpret_response(response, memory_location)

		alfid_byte 			= memory_location.alfid.get_byte_as_int()   # AddressAndLengthFormatIdentifier
		address_bytes 		= memory_location.get_address_bytes()
		memorysize_bytes 	= memory_location.get_memorysize_bytes()
		
		# We make sure that the echo from the server matches the request we sent.
		if response.service_data.alfid_echo != alfid_byte:
			raise UnexpectedResponseException(response, 'AddressAndLengthFormatIdentifier echoed back by the server (0x%02X) does not match the one requested by the client (0x%02X)' % (response.service_data.alfid_echo, int(alfid_byte)) )
		
		if response.service_data.memory_location_echo.address != memory_location.address:
			raise UnexpectedResponseException(response, 'Address echoed back by the server (0x%X) does not match the one requested by the client (0x%X)' % (response.service_data.memory_location_echo.address, memory_location.address) )

		if response.service_data.memory_location_echo.memorysize != memory_location.memorysize:
			raise UnexpectedResponseException(response, 'Memory size echoed back by the server (0x%X) does not match the one requested by the client (0x%X)' % (response.service_data.memory_location_echo.memorysize, memory_location.memorysize) )

		return response

# ====  ReadDTCInformation
	def get_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCByStatusMask, status_mask=status_mask)

	def get_emission_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportEmissionsRelatedOBDDTCByStatusMask, status_mask=status_mask)

	def get_mirrormemory_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMirrorMemoryDTCByStatusMask, status_mask=status_mask)

	def get_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)

	def get_number_of_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfDTCByStatusMask, status_mask=status_mask)
	
	def get_mirrormemory_number_of_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfMirrorMemoryDTCByStatusMask, status_mask=status_mask)
	
	def get_number_of_emission_dtc_by_status_mask(self, status_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfEmissionsRelatedOBDDTCByStatusMask, status_mask=status_mask)

	def get_number_of_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)
	
	def get_dtc_severity(self, dtc):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportSeverityInformationOfDTC, dtc=dtc)

	def get_supported_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportSupportedDTCs)

	def get_first_test_failed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportFirstTestFailedDTC)

	def get_first_confirmed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportFirstConfirmedDTC)

	def get_most_recent_test_failed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMostRecentTestFailedDTC)

	def get_most_recent_confirmed_dtc(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMostRecentConfirmedDTC)

	def get_dtc_with_permanent_status(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCWithPermanentStatus)

	def get_dtc_fault_counter(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCFaultDetectionCounter)

	def get_dtc_snapshot_identification(self):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCSnapshotIdentification)

	def get_dtc_snapshot_by_dtc_number(self, dtc, record_number=0xFF):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByDTCNumber, dtc=dtc, snapshot_record_number=record_number)

	def get_dtc_snapshot_by_record_number(self, record_number):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByRecordNumber, snapshot_record_number=record_number)

	def get_dtc_extended_data_by_dtc_number(self, dtc, record_number=0xFF, data_size = None):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCExtendedDataRecordByDTCNumber, dtc=dtc, extended_data_record_number=record_number,extended_data_size=data_size)

	def get_mirrormemory_dtc_extended_data_by_dtc_number(self, dtc, record_number=0xFF, data_size = None):
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber, dtc=dtc, extended_data_record_number=record_number, extended_data_size=data_size)

	# Performs a ReadDiagnsticInformation service request.
	# Many request are encoded the same way and many response are encoded the same way. Request grouping and response grouping are independent.
	@standard_error_management
	def read_dtc_information(self, subfunction, status_mask=None, severity_mask=None,  dtc=None, snapshot_record_number=None, extended_data_record_number=None, extended_data_size=None):
		if dtc is not None and isinstance(dtc, Dtc):
			dtc = dtc.id

		request_params = {
			'subfunction' : subfunction,
			'status_mask' : status_mask,
			'severity_mask' : severity_mask,
			'dtc' : dtc,
			'snapshot_record_number' : snapshot_record_number,
			'extended_data_record_number' : extended_data_record_number
		}

		request = services.ReadDTCInformation.make_request(**request_params)

		self.logger.info('Sending a ReadDtcInformation service request with subfunction "%s" (0x%02X).' % (services.ReadDTCInformation.Subfunction.get_name(subfunction), subfunction))
		self.logger.debug('Params are : %s' % str(request_params))
		response = self.send_request(request)

		response_params = {
			'subfunction' : subfunction,
			'tolerate_zero_padding' : self.config['tolerate_zero_padding'],
			'ignore_all_zero_dtc' : self.config['ignore_all_zero_dtc'],
			'dtc_snapshot_did_size' : self.config['dtc_snapshot_did_size'],
			'didconfig' : self.config['data_identifiers'] if 'data_identifiers' in self.config else None,
			'extended_data_size' : extended_data_size
		}

		if extended_data_size is None:
			if 'extended_data_size' in self.config:
				if dtc is not None and dtc in self.config['extended_data_size']:
					response_params['extended_data_size'] = self.config['extended_data_size'][dtc]

		services.ReadDTCInformation.interpret_response(response, **response_params)
		
		if response.service_data.subfunction_echo != subfunction:
			raise UnexpectedResponseException(response, 'Echo of ReadDTCInformation subfunction gotten from server(0x%02x) does not match the value in the request subfunction (0x%02x)' % (response.service_data.subfunction_echo, subfunction))	

		if subfunction == services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByDTCNumber:
			if len(response.service_data.dtcs) == 1:
				if dtc != response.service_data.dtcs[0].id:
					raise UnexpectedResponseException(response, 'Server returned snapshot with DTC ID 0x%06x while client requested for 0x%06x' % (response.service_data.dtcs[0].id, dtc))

		if subfunction in [services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByRecordNumber, services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByDTCNumber]:
			if len(response.service_data.dtcs) == 1 and snapshot_record_number != 0xFF:
				for snapshot in response.service_data.dtcs[0].snapshots:
					if snapshot.record_number != snapshot_record_number:
						raise UnexpectedResponseException(response, 'Server returned snapshot with record number 0x%02x while client requested for 0x%02x' % (snapshot.record_number, snapshot_record_number)) 

		if subfunction in [services.ReadDTCInformation.Subfunction.reportDTCExtendedDataRecordByDTCNumber, services.ReadDTCInformation.Subfunction.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber]:
			if len(response.service_data.dtcs) == 1 and extended_data_record_number < 0xF0: # Standard specifies that values between 0xF0 and 0xFF are for reporting groups (more than one record)
				for extended_data in response.service_data.dtcs[0].extended_data:
					if extended_data.record_number != extended_data_record_number :	
						raise UnexpectedResponseException(response, 'Extended data record number given by the server (0x%02x) does not match the record number requested by the client (0x%02x)' % (extended_data.record_number, extended_data_record_number))

		for dtc in response.service_data.dtcs:
			if dtc.fault_counter is not None and (dtc.fault_counter >= 0x7F or dtc.fault_counter < 0x01):
				self.logger.warning('Server returned a fault counter value of 0x%02x for DTC id 0x%06x while value should be between 0x01 and 0x7E.' % (dtc.fault_counter, dtc.id))

		if Dtc.Format.get_name(response.service_data.dtc_format) is None:
			self.logger.warning('Unknown DTC Format Identifier 0x%02x. Value should be between 0 and 3' % response.service_data.dtc_format)

		return response

	# Basic transmission of request. This will need to be improved
	def send_request(self, request, timeout=-1):
		if timeout is not None and timeout < 0:
			timeout = self.request_timeout
		self.conn.empty_rxqueue()
		self.logger.debug("Sending request to server")
		self.conn.send(request)

		if not request.suppress_positive_response:
			self.logger.debug("Waiting for server response")
			try:
				payload = self.conn.wait_frame(timeout=timeout, exception=True)
			except Exception as e:
				raise e

			response = Response.from_payload(payload)
			self.last_response = response
			self.logger.debug("Received response from server")

			if not response.valid:
				raise InvalidResponseException(response, 'Received response is invalid.')
					
			if response.service.response_id() != request.service.response_id():
				msg = "Response gotten from server has a service ID different than the one of the request. Received=0x%02x, Expected=0x%02x" % (response.service.response_id() , request.service.response_id() )
				raise UnexpectedResponseException(response, msg)
			
			if not response.positive:
				if not request.service.is_supported_negative_response(response.code):
					self.logger.warning("Given response (%s) is not a supported negative response code according to UDS standard." % response.code_name)	
				raise NegativeResponseException(response)

			self.logger.info('Received positive response from server.')
			return response
