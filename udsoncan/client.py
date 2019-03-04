from udsoncan import Response, Request, services, DidCodec, Routine, IOMasks, Dtc, DataIdentifier, MemoryLocation
from udsoncan.exceptions import *
from udsoncan.configs import default_client_config
import struct
import logging
import math
import binascii
import traceback
import functools
import time

class Client:
	"""
	__init__(self, conn, config=default_client_config, request_timeout = None)

	Object that interacts with a UDS server. 
	It builds a service request, sends it to the server, receives and parses its response, detects communication anomalies and logs what it is doing for further debugging.

	:param conn: The underlying protocol interface.
	:type conn: :ref:`Connection<Connection>`

	:param config: The :ref:`client configuration<client_config>`
	:type config: dict

	:param request_timeout: Maximum amount of time to wait for a response. This parameter exists for backward compatibility only. For detailed timeout handling, see :ref:`Client configuration<config_timeouts>`
	:type request_timeout: int
	"""

	class SuppressPositiveResponse:
		def __init__(self):
			self.enabled = False
		
		def __enter__(self):
			self.enabled = True
			return self

		def __exit__(self, type, value, traceback):
			self.enabled = False

	def __init__(self, conn, config=default_client_config, request_timeout=None):
		self.conn = conn
		self.config = dict(config) # Makes a copy of given configuration
		
		#For backward compatibility
		if request_timeout is not None:
			self.config['request_timeout'] = request_timeout
		self.suppress_positive_response = Client.SuppressPositiveResponse()
		self.last_response = None

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

	def set_configs(self, dic):
		self.config.update(dic)
		self.refresh_config()

	def refresh_config(self):
		self.configure_logger()
		for k in default_client_config:
			if k not in self.config:
				self.config[k] = default_client_config[k]


	
	# Decorator to apply on functions that the user will call.
	# Each function raises exceptions. This decorator handles these exceptions, logs them, 
	# then suppresses them or not depending on the client configuration.
	# if func1 and func2 are decorated and func2 calls func1, it should be done this way : self.func1._func_no_error_management(self, ...)
	
	def standard_error_management(func):
		@functools.wraps(func)
		def decorated(self, *args, **kwargs):
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

		decorated._func_no_error_management = func
		return decorated

	def service_log_prefix(self, service):
		return "%s<0x%02x>" % (service.get_name(), service.request_id())

	@standard_error_management
	def change_session(self, newsession):
		""" 
		Requests the server to change the diagnostic session with a :ref:`DiagnosticSessionControl<DiagnosticSessionControl>` service request

		:dependent configuration: ``exception_on_<type>_response``

		:param newsession: The session to try to switch. Values from :class:`DiagnosticSessionControl.Session <udsoncan.services.DiagnosticSessionControl.Session>` can be used.
		:type newsession: int 

		:return: The server response parsed by :meth:`DiagnosticSessionControl.interpret_response<udsoncan.services.DiagnosticSessionControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		req = services.DiagnosticSessionControl.make_request(newsession)

		named_newsession = '%s (0x%02x)' % (services.DiagnosticSessionControl.Session.get_name(newsession), newsession)
		self.logger.info('%s - Switching session to %s' % (self.service_log_prefix(services.DiagnosticSessionControl), named_newsession))
		
		response = self.send_request(req)
		if response is None:
			return 

		services.DiagnosticSessionControl.interpret_response(response)

		if newsession != response.service_data.session_echo:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (response.service_data.session_echo, newsession))

		return response

	@standard_error_management
	def request_seed(self, level):
		""" 
		Requests a seed to unlock a security level with the :ref:`SecurityAccess<SecurityAccess>` service 

		:dependent configuration: ``exception_on_<type>_response``

		:param level: The security level to unlock. If value is even, it will be converted to the corresponding odd value
		:type level: int 

		:return: The server response parsed by :meth:`SecurityAccess.interpret_response<udsoncan.services.SecurityAccess.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""		
		req = services.SecurityAccess.make_request(level, mode=services.SecurityAccess.Mode.RequestSeed)

		self.logger.info('%s - Requesting seed to unlock security access level 0x%02x' % (self.service_log_prefix(services.SecurityAccess), req.subfunction))	# level may be corrected by service.
		
		response = self.send_request(req)
		if response is None:
			return

		services.SecurityAccess.interpret_response(response, mode=services.SecurityAccess.Mode.RequestSeed)

		expected_level = services.SecurityAccess.normalize_level(mode=services.SecurityAccess.Mode.RequestSeed, level=level)
		received_level = response.service_data.security_level_echo
		if expected_level != received_level:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received_level, expected_level))

		self.logger.debug('Received seed [%s]' % (binascii.hexlify(response.service_data.seed)))
		return response

	# Performs a SecurityAccess service request. Send key
	@standard_error_management
	def send_key(self, level, key):
		""" 
		Sends a key to unlock a security level with the :ref:`SecurityAccess<SecurityAccess>` service 

		:dependent configuration: ``exception_on_<type>_response``

		:param level: The security level to unlock. If value is odd, it will be converted to the corresponding even value
		:type level: int 

		:param key: The key to send to the server
		:type key: bytes 

		:return: The server response parsed by :meth:`SecurityAccess.interpret_response<udsoncan.services.SecurityAccess.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""			
		req = services.SecurityAccess.make_request(level, mode=services.SecurityAccess.Mode.SendKey, key=key)
		self.logger.info('%s - Sending key to unlock security access level 0x%02x' % (self.service_log_prefix(services.SecurityAccess), req.subfunction))
		self.logger.debug('\tKey to send [%s]' % (binascii.hexlify(key)))

		response = self.send_request(req)
		if response is None:
			return

		services.SecurityAccess.interpret_response(response, mode=services.SecurityAccess.Mode.SendKey)

		expected_level = services.SecurityAccess.normalize_level(mode=services.SecurityAccess.Mode.SendKey, level=level)
		received_level = response.service_data.security_level_echo
		if expected_level != received_level:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (received_level, expected_level))

		return response
	
	@standard_error_management
	def unlock_security_access(self, level):
		"""
		Successively calls request_seed and send_key to unlock a security level with the :ref:`SecurityAccess<SecurityAccess>` service.
		The key computation is done by calling config['security_algo']

		:dependent configuration: ``exception_on_<type>_response`` ``security_algo`` ``security_algo_params``

		:param level: The level to unlock. Can be the odd or even variant of it.
		:type level: int

		:return: The server response parsed by :meth:`SecurityAccess.interpret_response<udsoncan.services.SecurityAccess.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""

		if 'security_algo' not in self.config or not callable(self.config['security_algo']):
			raise NotImplementedError("Client configuration does not provide a security algorithm")
		
		seed = self.request_seed._func_no_error_management(self, level).service_data.seed
		params = self.config['security_algo_params'] if 'security_algo_params' in self.config else None
		key = self.config['security_algo'].__call__(seed, params)
		return self.send_key._func_no_error_management(self, level, key)

	
	@standard_error_management
	def tester_present(self):
		"""
		Sends a TesterPresent request to keep the session active.

		:dependent configuration: ``exception_on_<type>_response``

		:return: The server response parsed by :meth:`TesterPresent.interpret_response<udsoncan.services.TesterPresent.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		req = services.TesterPresent.make_request()

		self.logger.info('%s - Sending TesterPresent request' % (self.service_log_prefix(services.TesterPresent)))
		response = self.send_request(req)
		if response is None:
			return

		services.TesterPresent.interpret_response(response)

		if req.subfunction != response.service_data.subfunction_echo:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (response.service_data.subfunction_echo, req.subfunction))

		return response

	@standard_error_management
	def read_data_by_identifier_first(self, didlist):
		"""
		Shortcut to extract a single DID. 
		Calls read_data_by_identifier then returns the first DID asked for. 

		:dependent configuration: ``exception_on_<type>_response`` ``data_identifiers`` ``tolerate_zero_padding``

		:param didlist: The list of DID to be read
		:type didlist: list[int]

		:return: The server response parsed by :meth:`ReadDataByIdentifier.interpret_response<udsoncan.services.ReadDataByIdentifier.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		didlist = services.ReadDataByIdentifier.validate_didlist_input(didlist)
		response = self.read_data_by_identifier(didlist)
		values = response.service_data.values
		if len(values) > 0 and len(didlist) > 0:
			return values[didlist[0]]

	@standard_error_management
	def read_data_by_identifier(self, didlist):
		"""
		Requests a value associated with a data identifier (DID) through the :ref:`ReadDataByIdentifier<ReadDataByIdentifier>` service.
		
		:dependent configuration: ``exception_on_<type>_response`` ``data_identifiers`` ``tolerate_zero_padding``

		See :ref:`an example<reading_a_did>` about how to read a DID

		:param didlist: The list of DID to be read
		:type didlist: list[int]

		:return: The server response parsed by :meth:`ReadDataByIdentifier.interpret_response<udsoncan.services.ReadDataByIdentifier.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		didlist = services.ReadDataByIdentifier.validate_didlist_input(didlist)
		req = services.ReadDataByIdentifier.make_request(didlist=didlist, didconfig=self.config['data_identifiers'])

		if len(didlist) == 1:
			self.logger.info("%s - Reading data identifier : 0x%04x (%s)" % (self.service_log_prefix(services.ReadDataByIdentifier), didlist[0], DataIdentifier.name_from_id(didlist[0])))
		else:
			self.logger.info("%s - Reading %d data identifier : %s" % (self.service_log_prefix(services.ReadDataByIdentifier), len(didlist), didlist))
		
		if 'data_identifiers' not in self.config or  not isinstance(self.config['data_identifiers'], dict):
			raise AttributeError('Configuration does not contains a valid data identifier description.')

		response = self.send_request(req)
		if response is None:
			return
		
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
		"""
		Requests to write a value associated with a data identifier (DID) through the :ref:`WriteDataByIdentifier<WriteDataByIdentifier>` service.
		
		:dependent configuration:  ``exception_on_<type>_response`` ``data_identifiers``

		:param didlist: The DID to write its value
		:type didlist: int
		
		:param value: Value given to the :ref:`DidCodec <DidCodec>`.encode method. The payload returned by the codec will be sent to the server.
		:type value: int

		:return: The server response parsed by :meth:`WriteDataByIdentifier.interpret_response<udsoncan.services.WriteDataByIdentifier.interpret_response>`
		:rtype: :ref:`Response<Response>`

		"""
		req = services.WriteDataByIdentifier.make_request(did, value, didconfig=self.config['data_identifiers'])
		self.logger.info("%s - Writing data identifier 0x%04x (%s)" % (self.service_log_prefix(services.WriteDataByIdentifier), did, DataIdentifier.name_from_id(did)))
		
		response = self.send_request(req)
		if response is None:
			return
		services.WriteDataByIdentifier.interpret_response(response)

		if response.service_data.did_echo != did:
			raise UnexpectedResponseException(response, "Server returned a response for data identifier 0x%04x while client requested for did 0x%04x" % (response.service_data.did_echo, did))
		
		return response

	@standard_error_management
	def ecu_reset(self, reset_type):
		"""
		Requests the server to execute a reset sequence through the :ref:`ECUReset<ECUReset>` service.

		:dependent configuration: ``exception_on_<type>_response``

		:param reset_type: The type of reset to perform.  :class:`ECUReset.ResetType<udsoncan.services.ECUReset.ResetType>`
		:type reset_type: int

		:return: The server response parsed by :meth:`ECUReset.interpret_response<udsoncan.services.ECUReset.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		req = services.ECUReset.make_request(reset_type)
		self.logger.info("%s - Requesting reset of type 0x%02x (%s)" % (self.service_log_prefix(services.ECUReset), reset_type, services.ECUReset.ResetType.get_name(reset_type)))
	
		response = self.send_request(req)
		if response is None:
			return
		services.ECUReset.interpret_response(response)
		
		if response.service_data.reset_type_echo != reset_type:
			raise UnexpectedResponseException(response, "Response subfunction received from server (0x%02x) does not match the requested subfunction (0x%02x)" % (response.service_data.reset_type_echo, reset_type))

		if response.service_data.reset_type_echo == services.ECUReset.ResetType.enableRapidPowerShutDown and response.service_data.powerdown_time != 0xFF:
			self.logger.info('Server will shutdown in %d seconds.' % (response.service_data.powerdown_time))

		return response

	@standard_error_management 
	def clear_dtc(self, group=0xFFFFFF):
		"""
		Requests the server to clear its active Diagnostic Trouble Codes with the :ref:`ClearDiagnosticInformation<ClearDiagnosticInformation>` service.

		:dependent configuration: ``exception_on_<type>_response``

		:param group: The group of DTCs to clear. It may refer to Powertrain DTCs, Chassis DTCs, etc. Values are defined by the ECU manufacturer except for two specific values

			- ``0x000000`` : Emissions-related systems
			- ``0xFFFFFF`` : All DTCs
		:type group: int

		:return: The server response parsed by :meth:`ClearDiagnosticInformation.interpret_response<udsoncan.services.ClearDiagnosticInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""

		request = services.ClearDiagnosticInformation.make_request(group)
		if group == 0xFFFFFF:
			self.logger.info('%s - Clearing all DTCs (group mask : 0xFFFFFF)' % (self.service_log_prefix(services.ClearDiagnosticInformation)))
		else:
			self.logger.info('%s - Clearing DTCs matching group mask : 0x%06x' % (self.service_log_prefix(services.ClearDiagnosticInformation), group))

		response = self.send_request(request)
		if response is None:
			return
		services.ClearDiagnosticInformation.interpret_response(response)

		return response

	# Performs a RoutineControl Service request
	def start_routine(self, routine_id, data=None):
		"""
		Requests the server to start a routine through the :ref:`RoutineControl<RoutineControl>` service (subfunction = 0x01).

		:dependent configuration: ``exception_on_<type>_response``

		:param routine_id: The 16-bit numerical ID of the routine to start
		:type group: int

		:param data: Optional additional data to give to the server
		:type data: bytes

		:return: The server response parsed by :meth:`RoutineControl.interpret_response<udsoncan.services.RoutineControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		return self.routine_control(routine_id, services.RoutineControl.ControlType.startRoutine, data)

	# Performs a RoutineControl Service request
	def stop_routine(self, routine_id, data=None):
		"""
		Requests the server to stop a routine through the :ref:`RoutineControl<RoutineControl>` service (subfunction = 0x02).

		:dependent configuration: ``exception_on_<type>_response``

		:param routine_id: The 16-bit numerical ID of the routine to stop
		:type group: int

		:param data: Optional additional data to give to the server
		:type data: bytes

		:return: The server response parsed by :meth:`RoutineControl.interpret_response<udsoncan.services.RoutineControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		return self.routine_control(routine_id, services.RoutineControl.ControlType.stopRoutine, data)

	# Performs a RoutineControl Service request
	def get_routine_result(self, routine_id, data=None):
		"""
		Requests the server to send back the execution result of the specified routine through the :ref:`RoutineControl<RoutineControl>` service (subfunction = 0x03).

		:dependent configuration: ``exception_on_<type>_response``

		:param routine_id: The 16-bit numerical ID of the routine
		:type group: int

		:param data: Optional additional data to give to the server
		:type data: bytes

		:return: The server response parsed by :meth:`RoutineControl.interpret_response<udsoncan.services.RoutineControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.routine_control(routine_id, services.RoutineControl.ControlType.requestRoutineResults, data)

	# Performs a RoutineControl Service request
	@standard_error_management
	def routine_control(self, routine_id, control_type, data=None):
		"""
		Sends a generic request for the :ref:`RoutineControl<RoutineControl>` service with custom subfunction (control_type).

		:dependent configuration: ``exception_on_<type>_response``

		:param control_type: The service subfunction. See :class:`RoutineControl.ControlType<udsoncan.services.RoutineControl.ControlType>`
		:type group: int

		:param routine_id: The 16-bit numerical ID of the routine
		:type group: int

		:param data: Optional additional data to give to the server
		:type data: bytes

		:return: The server response parsed by :meth:`RoutineControl.interpret_response<udsoncan.services.RoutineControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		request = services.RoutineControl.make_request(routine_id, control_type, data=data)
		payload_length = 0 if data is None else len(data)
		action = "ISOSAEReserved action for routine ID"
		if control_type == services.RoutineControl.ControlType.startRoutine:
			action = "Starting routine ID"
		elif control_type == services.RoutineControl.ControlType.stopRoutine:
			action = "Starting routine ID"
		elif control_type == services.RoutineControl.ControlType.requestRoutineResults:
			action = "Requesting result for routine ID"

		self.logger.info("%s - ControlType=0x%02x - %s 0x%04x (%s) with a payload of %d bytes" % (self.service_log_prefix(services.RoutineControl), control_type, action,  routine_id, Routine.name_from_id(routine_id), payload_length ))
		if data is not None:
			self.logger.debug("\tPayload data : %s" % binascii.hexlify(data))

		response = self.send_request(request)
		if response is None:
			return
		services.RoutineControl.interpret_response(response)

		if control_type != response.service_data.control_type_echo:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.control_type_echo, control_type))

		if routine_id != response.service_data.routine_id_echo:
			raise UnexpectedResponseException(response, "Response received from server (ID = 0x%04x) does not match the requested routine ID (0x%04x)" % (response.service_data.routine_id_echo, routine_id))

		return response

	def read_extended_timing_parameters(self):
		"""
		Reads the timing parameters from the server with :ref:`AccessTimingParameter<AccessTimingParameter>` service with subfunction ``readExtendedTimingParameterSet`` (0x01).

		:dependent configuration: ``exception_on_<type>_response``
		
		:return: The server response parsed by :meth:`AccessTimingParameter.interpret_response<udsoncan.services.AccessTimingParameter.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.readExtendedTimingParameterSet)

	def reset_default_timing_parameters(self):
		"""
		Resets the server timing parameters to their default value with :ref:`AccessTimingParameter<AccessTimingParameter>` service with subfunction ``setTimingParametersToDefaultValues`` (0x02).

		:dependent configuration: ``exception_on_<type>_response``
		
		:return: The server response parsed by :meth:`AccessTimingParameter.interpret_response<udsoncan.services.AccessTimingParameter.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.setTimingParametersToDefaultValues)

	def read_active_timing_parameters(self):
		"""
		Reads the currently active timing parameters from the server with :ref:`AccessTimingParameter<AccessTimingParameter>` service with subfunction ``readCurrentlyActiveTimingParameters`` (0x03).

		:dependent configuration: ``exception_on_<type>_response``
		
		:return: The server response parsed by :meth:`AccessTimingParameter.interpret_response<udsoncan.services.AccessTimingParameter.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.readCurrentlyActiveTimingParameters)
	
	def set_timing_parameters(self, params):
		"""
		Sets the timing parameters into the server with :ref:`AccessTimingParameter<AccessTimingParameter>` service with subfunction ``setTimingParametersToGivenValues`` (0x04).

		:dependent configuration: ``exception_on_<type>_response``
		
		:param params: The parameters data. Specific to each ECU.
		:type params: bytes

		:return: The server response parsed by :meth:`AccessTimingParameter.interpret_response<udsoncan.services.AccessTimingParameter.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""
		return self.access_timing_parameter(access_type=services.AccessTimingParameter.AccessType.setTimingParametersToGivenValues, request_record=params)

	
	@standard_error_management
	def access_timing_parameter(self, access_type, timing_param_record=None):
		"""
		Sends a generic request for :ref:`AccessTimingParameter<AccessTimingParameter>` service with configurable subfunction (access_type).

		:dependent configuration: ``exception_on_<type>_response``

		:param access_type: The service subfunction. See :class:`AccessTimingParameter.AccessType<udsoncan.services.AccessTimingParameter.AccessType>`
		:type access_type: bytes

		:param params: The parameters data. Specific to each ECU.
		:type params: bytes

		:return: The server response parsed by :meth:`AccessTimingParameter.interpret_response<udsoncan.services.AccessTimingParameter.interpret_response>`
		:rtype: :ref:`Response<Response>`
	
		"""

		request = services.AccessTimingParameter.make_request(access_type, timing_param_record)
		payload_length = 0 if timing_param_record is None else len(timing_param_record)

		self.logger.info('%s - AccessType=0x%02x (%s) - Sending request with record payload of %d bytes' % (self.service_log_prefix(services.AccessTimingParameter), access_type, services.AccessTimingParameter.AccessType.get_name(access_type), payload_length))
		if timing_param_record is not None:
			self.logger.debug("Payload data : %s" % binascii.hexlify(data))

		response = self.send_request(request)
		if response is None:
			return

		services.AccessTimingParameter.interpret_response(response)

		if access_type != response.service_data.access_type_echo:
			raise UnexpectedResponseException(response, "Access type of response (0x%02x) does not match request access type (0x%02x)" % (response.service_data.access_type_echo, access_type))

		allowed_response_record_access_type = [
			services.AccessTimingParameter.AccessType.readExtendedTimingParameterSet, 
			services.AccessTimingParameter.AccessType.readCurrentlyActiveTimingParameters
		]

		if len(response.service_data.timing_param_record) > 0 and access_type not in allowed_response_record_access_type:
			self.logger.warning("Server returned data in the AccessTimingParameter response although none was asked")

		return response

	@standard_error_management
	def communication_control(self, control_type, communication_type):
		"""
		Switches the transmission or reception of certain messages on/off with :ref:`CommunicationControl<CommunicationControl>` service.

		:dependent configuration: ``exception_on_<type>_response``
		
		:param control_type: The action to request such as enabling or disabling some messages. See :class:`CommunicationControl.ControlType<udsoncan.services.CommunicationControl.ControlType>`. This value can also be ECU manufacturer-specific
		:type control_type: int

		:param communication_type: Indicates what section of the network and the type of message that should be affected by the command. Refer to :ref:`CommunicationType<CommunicationType>` for more details. If an `integer` or a `bytes` is given, the value will be decoded to create the required :ref:`CommunicationType<CommunicationType>` object
		:type communication_type: :ref:`CommunicationType<CommunicationType>`, bytes, int

		:return: The server response parsed by :meth:`CommunicationControl.interpret_response<udsoncan.services.CommunicationControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""

		communication_type = services.CommunicationControl.normalize_communication_type(communication_type)

		request = services.CommunicationControl.make_request(control_type, communication_type)
		self.logger.info('%s - ControlType=0x%02x (%s) - Sending request with a CommunicationType byte of 0x%02x (%s)' % (self.service_log_prefix(services.CommunicationControl), control_type, services.CommunicationControl.ControlType.get_name(control_type), communication_type.get_byte_as_int(), str(communication_type)))

		response = self.send_request(request)
		if response is None:
			return

		services.CommunicationControl.interpret_response(response)

		if control_type != response.service_data.control_type_echo:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.control_type_echo, control_type))

		return response

	def request_download(self, memory_location, dfi=None):
		"""
		Informs the server that the client wants to initiate a download from the client to the server by sending a :ref:`RequestDownload<RequestDownload>` service request.

		:dependent configuration: ``exception_on_<type>_response`` ``server_address_format`` ``server_memorysize_format``

		:param memory_location: The address and size of the memory block to be written.
		:type memory_location: :ref:`MemoryLocation <MemoryLocation>`

		:param dfi: Optional :ref:`DataFormatIdentifier <DataFormatIdentifier>` defining the compression and encryption scheme of the data. 
			If not specified, the default value of 00 will be used, specifying no encryption and no compression
		:type dfi: :ref:`DataFormatIdentifier <DataFormatIdentifier>`

		:return: The server response parsed by :meth:`RequestDownload.interpret_response<udsoncan.services.RequestDownload.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.request_upload_download(services.RequestDownload, memory_location, dfi)

	def request_upload(self, memory_location, dfi=None):
		"""
		Informs the server that the client wants to initiate an upload from the server to the client by sending a :ref:`RequestUpload<RequestUpload>` service request.

		:dependent configuration: ``exception_on_<type>_response`` ``server_address_format`` ``server_memorysize_format``
		
		:param memory_location: The address and size of the memory block to be written.
		:type memory_location: :ref:`MemoryLocation <MemoryLocation>`

		:param dfi: Optional :ref:`DataFormatIdentifier <DataFormatIdentifier>` defining the compression and encryption scheme of the data. 
			If not specified, the default value of 00 will be used, specifying no encryption and no compression
		:type dfi: :ref:`DataFormatIdentifier <DataFormatIdentifier>`

		:return: The server response parsed by :meth:`RequestUpload.interpret_response<udsoncan.services.RequestUpload.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.request_upload_download(services.RequestUpload, memory_location, dfi)

	# Common code for both RequestDownload and RequestUpload services
	@standard_error_management
	def request_upload_download(self, service_cls, memory_location, dfi=None):
		dfi = service_cls.normalize_data_format_identifier(dfi)

		if service_cls not in [services.RequestDownload, services.RequestUpload]:
			raise ValueError('Service must either be RequestDownload or RequestUpload')

		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		# If user does not specify a byte format, we apply the one in client configuration.
		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		request = service_cls.make_request(memory_location=memory_location, dfi=dfi)

		action = ""
		if service_cls == services.RequestDownload:
			action = "Requesting a download (client to server)"
		elif service_cls == services.RequestUpload:
			action = "Requesting an upload (server to client)"

		self.logger.info('%s - %s for memory location [%s] and DataFormatIdentifier 0x%02x (%s)' % (self.service_log_prefix(service_cls), action, str(memory_location), dfi.get_byte_as_int(), str(dfi)))

		response = self.send_request(request)
		if response is None:
			return
		service_cls.interpret_response(response)
		
		return response

	@standard_error_management
	def transfer_data(self, sequence_number, data=None):
		"""
		Transfer a block of data to/from the client to/from the server by sending a :ref:`TransferData<TransferData>` service request and returning the server response.

		:dependent configuration: ``exception_on_<type>_response``
		
		:param sequence_number: Corresponds to an 8bit counter that should increment for each new block transferred.
			Allowed values are from 0 to 0xFF
		:type sequence_number: int

		:param data: Optional additional data to send to the server
		:type data: bytes

		:return: The server response parsed by :meth:`TransferData.interpret_response<udsoncan.services.TransferData.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		request = services.TransferData.make_request(sequence_number, data)
		
		data_len = 0 if data is None else len(data)
		self.logger.info('%s - Sending a block of data with SequenceNumber=%d that is %d bytes long .' % (self.service_log_prefix(services.TransferData), sequence_number, data_len))
		if data is not None:
			self.logger.debug('Data to transfer : %s' % binascii.hexlify(data))
		
		response = self.send_request(request)
		if response is None:
			return
		services.TransferData.interpret_response(response)

		if sequence_number != response.service_data.sequence_number_echo:
			raise UnexpectedResponseException(response, "Block sequence number of response (0x%02x) does not match request block sequence number (0x%02x)" % (response.service_data.sequence_number_echo, sequence_number))

		return response

	@standard_error_management
	def request_transfer_exit(self, data=None):
		"""
		Informs the server that the client wants to stop the data transfer by sending a :ref:`RequestTransferExit<RequestTransferExit>` service request.

		:dependent configuration: ``exception_on_<type>_response``

		:param data: Optional additional data to send to the server
		:type data: bytes

		:return: The server response parsed by :meth:`RequestTransferExit.interpret_response<udsoncan.services.RequestTransferExit.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		request = services.RequestTransferExit.make_request(data)
		self.logger.info('%s - Sending exit request' % (self.service_log_prefix(services.RequestTransferExit)))

		response = self.send_request(request)
		if response is None:
			return
		services.RequestTransferExit.interpret_response(response)

		return response

	@standard_error_management
	def link_control(self, control_type, baudrate=None):
		"""
		Controls the communication baudrate by sending a :ref:`LinkControl<LinkControl>` service request.

		:dependent configuration: ``exception_on_<type>_response``

		:param control_type: Allowed values are from 0 to 0xFF. See :class:`LinkControl.ControlType<udsoncan.services.LinkControl.ControlType>`
		:type control_type: int

		:param baudrate: Required baudrate value when ``control_type`` is either ``verifyBaudrateTransitionWithFixedBaudrate`` (1) or ``verifyBaudrateTransitionWithSpecificBaudrate`` (2)
		:type baudrate: :ref:`Baudrate <Baudrate>`

		:return: The server response parsed by :meth:`LinkControl.interpret_response<udsoncan.services.LinkControl.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		request = services.LinkControl.make_request(control_type, baudrate)
		baudrate_str = 'No baudrate specified' if baudrate is None else 'Baudrate : ' + str(baudrate)

		action = "Performing LinkControl request"
		if control_type in [services.LinkControl.ControlType.verifyBaudrateTransitionWithFixedBaudrate, services.LinkControl.ControlType.verifyBaudrateTransitionWithSpecificBaudrate]:
			action = "Verifiying support"
		elif   control_type == services.LinkControl.ControlType.transitionBaudrate:
			action = "Switching"

		self.logger.info('%s - ControlType=0x%02x (%s) - %s for baudrate %s ' % (self.service_log_prefix(services.LinkControl), control_type, services.LinkControl.ControlType.get_name(control_type), action, baudrate_str))
		
		response = self.send_request(request)
		if response is None:
			return
		services.LinkControl.interpret_response(response)
		
		if control_type != response.service_data.control_type_echo:
			raise UnexpectedResponseException(response, "Control type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.control_type_echo, control_type))

		return response

	@standard_error_management
	def io_control(self, did, control_param=None, values=None, masks=None):
		"""
		Substitutes the value of an input signal or overrides the state of an output by sending a :ref:`InputOutputControlByIdentifier<InputOutputControlByIdentifier>` service request.

		:dependent configuration: ``exception_on_<type>_response`` ``input_output`` ``tolerate_zero_padding``

		:param did: Data identifier to represent the IO
		:type did: int

		:param control_param: Optional parameter that can be a value from :class:`InputOutputControlByIdentifier.ControlParam<udsoncan.services.InputOutputControlByIdentifier.ControlParam>`
		:type control_param: int

		:param values: Optional values to send to the server. This parameter will be given to :ref:`DidCodec<DidCodec>`.encode() method. 
			It can be:
			
				- A list for positional arguments
				- A dict for named arguments
				- An instance of :ref:`IOValues<IOValues>` for mixed arguments

		:type values: list, dict, :ref:`IOValues<IOValues>`

		:param masks: Optional mask record for composite values. The mask definition must be included in ``config['input_output']``
			It can be:

				- A list naming the bit mask to set
				- A dict with the mask name as a key and a boolean setting or clearing the mask as the value
				- An instance of :ref:`IOMask<IOMask>`
				- A boolean value to set all masks to the same value.
		:type masks: list, dict, :ref:`IOMask<IOMask>`, bool

		:return: The server response parsed by :meth:`InputOutputControlByIdentifier.interpret_response<udsoncan.services.InputOutputControlByIdentifier.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		if 'input_output' not in self.config:
			raise ConfigError('input_output', msg='input_output must be defined in client configuration in order to use InputOutputControlByIdentifier service')

		request = services.InputOutputControlByIdentifier.make_request( did, control_param=control_param, values=values, masks=masks, ioconfig=self.config['input_output'])
		
		control_param_str = 'no control parameter' if control_param is None else 'control parameter 0x%02x (%s)' % (control_param, services.InputOutputControlByIdentifier.ControlParam.get_name(control_param))		
		self.logger.info('%s - Sending request for DID=0x%04x, %s.' % (self.service_log_prefix(services.InputOutputControlByIdentifier), did, control_param_str))

		response = self.send_request(request)
		if response is None:
			return
		services.InputOutputControlByIdentifier.interpret_response(response, control_param=control_param, tolerate_zero_padding=self.config['tolerate_zero_padding'], ioconfig=self.config['input_output'])

		if response.service_data.did_echo != did:
			raise UnexpectedResponseException(response, "Echo of the DID number (0x%04x) does not match the value in the request (0x%04x)" % (response.service_data.did_echo, did))

		if control_param != response.service_data.control_param_echo:
			raise UnexpectedResponseException(response, 'Echo of the InputOutputControlParameter (0x%02x) does not match the value in the request (0x%02x)' % (response.service_data.control_param_echo, control_param))	

		return response

	@standard_error_management
	def control_dtc_setting(self, setting_type, data=None):
		"""
		Controls some settings related to the Diagnostic Trouble Codes by sending a :ref:`ControlDTCSetting<ControlDTCSetting>` service request. 
		It can enable/disable some DTCs or perform some ECU specific configuration.

		:dependent configuration: ``exception_on_<type>_response``

		:param setting_type: Allowed values are from 0 to 0x7F. See :class:`ControlDTCSetting.SettingType<udsoncan.services.ControlDTCSetting.SettingType>`
		:type setting_type: int

		:param data: Optional additional data sent with the request called `DTCSettingControlOptionRecord`
		:type data: bytes

		:return: The server response parsed by :meth:`ControlDTCSetting.interpret_response<udsoncan.services.ControlDTCSetting.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		request = services.ControlDTCSetting.make_request(setting_type, data)
		data_len = 0 if data is None else len(data)
		action = "Performing ControlDTCSetting request"
		if setting_type == services.ControlDTCSetting.SettingType.on:
			action = "Turning DTC On"
		elif setting_type == services.ControlDTCSetting.SettingType.off:
			action =  "Turning DTC Off"

		self.logger.info('%s - SettingType=0x%02x (%s) - %s with a paylod of %d bytes' % (self.service_log_prefix(services.ControlDTCSetting), setting_type, services.ControlDTCSetting.SettingType.get_name(setting_type), action, data_len))
		if data is not None:
			self.logger.debug("Payload of data : %s" % binascii.hexlify(data))

		response = self.send_request(request)
		if response is None:
			return

		services.ControlDTCSetting.interpret_response(response)

		if response.service_data.setting_type_echo != setting_type:
			raise UnexpectedResponseException(response, "Setting type of response (0x%02x) does not match request control type (0x%02x)" % (response.service_data.setting_type_echo, setting_type))

		return response

	@standard_error_management
	def read_memory_by_address(self, memory_location):
		"""
		Reads a block of memory from the server by sending a :ref:`ReadMemoryByAddress<ReadMemoryByAddress>` service request. 

		:dependent configuration: ``exception_on_<type>_response`` ``server_address_format`` ``server_memorysize_format``

		:param memory_location: The address and the size of the memory block to read.
		:type memory_location: :ref:`MemoryLocation <MemoryLocation>`

		:return: The server response parsed by :meth:`ReadMemoryByAddress.interpret_response<udsoncan.services.ReadMemoryByAddress.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		request = services.ReadMemoryByAddress.make_request(memory_location)
		self.logger.info('%s - Reading memory address at %s' % (self.service_log_prefix(services.ReadMemoryByAddress), str(memory_location)))
		
		response = self.send_request(request)
		if response is None:
			return
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
		"""
		Writes a block of memory in the server by sending a :ref:`WriteMemoryByAddress<WriteMemoryByAddress>` service request. 

		:dependent configuration: ``exception_on_<type>_response`` ``server_address_format`` ``server_memorysize_format``

		:param memory_location: The address and the size of the memory block to read. 
		:type memory_location: :ref:`MemoryLocation <MemoryLocation>`

		:param data: The data to write into memory.
		:type data: bytes

		:return: The server response parsed by :meth:`WriteMemoryByAddress.interpret_response<udsoncan.services.WriteMemoryByAddress.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""

		if not isinstance(memory_location, MemoryLocation):
			raise ValueError('memory_location must be an instance of MemoryLocation')

		if 'server_address_format' in self.config:
			memory_location.set_format_if_none(address_format=self.config['server_address_format'])

		if 'server_memorysize_format' in self.config:
			memory_location.set_format_if_none(memorysize_format=self.config['server_memorysize_format'])

		request = services.WriteMemoryByAddress.make_request(memory_location, data)
		self.logger.info('%s - Writing %d bytes to memory address at %s' % (self.service_log_prefix(services.WriteMemoryByAddress), len(data), str(memory_location)))

		if len(data) != memory_location.memorysize:
			self.logger.warning('%s: Given data block length (%d bytes) does not match MemoryLocation size (%d bytes)' % (self.service_log_prefix(services.WriteMemoryByAddress), len(data), memory_location.memorysize))

		response = self.send_request(request)
		if response is None:
			return
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
		"""
		Reads all the Diagnostic Trouble Codes that have a status matching the given mask. 
		The server will check all of its DTCs and if (Dtc.status & status_mask) != 0, then the DTCs match the filter and are sent back to the client.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCByStatusMask, status_mask=status_mask)

	def get_emission_dtc_by_status_mask(self, status_mask):
		"""
		Reads the emission-related Diagnostic Trouble Codes that have a status matching the given mask.
		The server will check its emission-related DTCs and if (Dtc.status & status_mask) != 0, then the DTCs match the filter and are sent back to the client.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportEmissionsRelatedOBDDTCByStatusMask, status_mask=status_mask)

	def get_mirrormemory_dtc_by_status_mask(self, status_mask):
		"""
		Reads all the Diagnostic Trouble Codes stored in mirror memory that have a status matching the given mask. 
		The server will check all of its DTCs and if (Dtc.status & status_mask) != 0, then the DTCs match the filter and are sent back to the client.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMirrorMemoryDTCByStatusMask, status_mask=status_mask)

	def get_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		"""
		Reads all the Diagnostic Trouble Codes that have a status and a severity matching the given masks. 
		The server will check all of its DTCs and if ( (Dtc.status & status_mask) != 0 && (Dtc.severity & severity) !=0), then the DTCs match the filter and are sent back to the client.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`
		
		:param severity_mask: The severity mask against which the DTCs are tested. 
		:type severity_mask: int or :ref:`Dtc.Severity<DTC_Severity>`
		
		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)

	def get_number_of_dtc_by_status_mask(self, status_mask):
		"""
		Gets the number of DTCs that match the specified status mask.

		:dependent configuration: ``exception_on_<type>_response``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfDTCByStatusMask, status_mask=status_mask)
	
	def get_mirrormemory_number_of_dtc_by_status_mask(self, status_mask):
		"""
		Gets the number of DTCs that match the specified status mask in mirror memory.

		:dependent configuration: ``exception_on_<type>_response``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfMirrorMemoryDTCByStatusMask, status_mask=status_mask)
	
	def get_number_of_emission_dtc_by_status_mask(self, status_mask):
		"""
		Gets the number of emission-related DTCs that match the specified status mask.

		:dependent configuration: ``exception_on_<type>_response``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfEmissionsRelatedOBDDTCByStatusMask, status_mask=status_mask)

	def get_number_of_dtc_by_status_severity_mask(self, status_mask, severity_mask):
		"""
		Gets the number of DTCs that match the specified status mask and severity mask.

		:dependent configuration: ``exception_on_<type>_response``

		:param status_mask: The status mask against which the DTCs are tested. 
		:type status_mask: int or :ref:`Dtc.Status<DTC_Status>`

		:param severity_mask: The severity mask against which the DTCs are tested. 
		:type severity_mask: int or :ref:`Dtc.Severity<DTC_Severity>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportNumberOfDTCBySeverityMaskRecord, status_mask=status_mask, severity_mask=severity_mask)
	
	def get_dtc_severity(self, dtc):
		"""
		Requests the server for a specific DTC severity level.

		:dependent configuration: ``exception_on_<type>_response``

		:param dtc: The DTC ID for which we request the severity. It can be a 3-byte integer or a DTC instance with an ID set.
		:type dtc: int or :ref:`Dtc<DTC>`

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportSeverityInformationOfDTC, dtc=dtc)

	def get_supported_dtc(self):
		"""
		Requests the list of supported DTCs by the server.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportSupportedDTCs)

	def get_first_test_failed_dtc(self):
		"""
		Reads a single DTC. Requests the server for the first DTC that set its ``Dtc.Status.test_failed`` bit.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportFirstTestFailedDTC)

	def get_first_confirmed_dtc(self):
		"""
		Reads a single DTC. Requests the server for the first DTC that set its ``Dtc.Status.confirmed`` bit.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportFirstConfirmedDTC)

	def get_most_recent_test_failed_dtc(self):
		"""
		Reads a single DTC. Requests the server for the last DTC that set its ``Dtc.Status.test_failed`` bit.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMostRecentTestFailedDTC)

	def get_most_recent_confirmed_dtc(self):
		"""
		Reads a single DTC. Requests the server for the last DTC that set its ``Dtc.Status.confirmed`` bit.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMostRecentConfirmedDTC)

	def get_dtc_with_permanent_status(self):
		"""
		Returns all DTCs that the server marked as `permanent`. 

		A permanent DTC is a DTC stored in Non-Volatile memory and that cannot be erased by test equipment or by power-cycling the ECU.
		
		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCWithPermanentStatus)

	def get_dtc_fault_counter(self):
		"""
		Requests the server for all DTCs that are `prefailed` along with their fault detection counter. 

		A prefailed DTC is a DTC for which the detection condition is met, but has not been identified as `pending` or `confirmed` yet. 

		If the ECU follows the UDS guidelines, it will wait to detect a fault many times before setting a status bit for this fault DTC. Each time the fault is detected, a fault counter is incremented, when it is not detected, the counter is decremented.
		Once the fault counter reaches a threshold, a status bit is set and the DTC is not `prefailed` anymore. A `prefailed` DTC is any DTC that has fault detection counter greater than 0, but less than the detection threshold.
		
		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCFaultDetectionCounter)

	def get_dtc_snapshot_identification(self):
		"""
		Requests the server to return an index of all the DTC snapshots available. The server will respond with a list of DTCs and a list of snapshot record numbers for each DTC.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc``

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCSnapshotIdentification)

	def get_dtc_snapshot_by_dtc_number(self, dtc, record_number=0xFF):
		"""
		Requests the server for one or many specific DTC snapshots associated with a single DTC.
		Each snapshot has a data identifier associated with it. The data will be decoded using the associated :ref:`DidCodec<DidCodec>` defined in ``config['data_identifiers']``.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``ignore_all_zero_dtc`` ``dtc_snapshot_did_size``

		:param dtc: The DTC ID for which we request the snapshot data. It can be a 3-byte integer or a DTC instance with an ID set.
		:type dtc: int or :ref:`Dtc<DTC>`

		:param record_number: The record number of the snapshot data to read. If 0xFF is given, then all snapshots will be read, otherwise, a single snapshot will be read.
		:type record_number: int

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByDTCNumber, dtc=dtc, snapshot_record_number=record_number)

	def get_dtc_snapshot_by_record_number(self, record_number=0xFF):
		"""
		Requests the server for one or many DTC snapshots by specifying a record number. This functionality can exist only if the server assigns globally unique record_numbers to DTC snapshots, regardless of the DTC ID.

		Each snapshot has a data identifier associated with it. The data will be decoded using the associated :ref:`DidCodec<DidCodec>` defined in ``config['data_identifiers']``.

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding``  ``dtc_snapshot_did_size``

		:param record_number: The record number of the snapshot data to read. If 0xFF is given, then all snapshots will be read, otherwise, a single snapshot will be read.
		:type record_number: int

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByRecordNumber, snapshot_record_number=record_number)

	def get_dtc_extended_data_by_dtc_number(self, dtc, record_number=0xFF, data_size = None):
		"""
		Requests the server for one or many DTC **extended data** by specifying a record number.

		The DTC extended data is an ECU specific set of data that is not associated with a data identifier. Given as ``bytes``

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``extended_data_size``

		:param dtc: The DTC ID for which we request the extended data. It can be a 3-byte integer or a DTC instance with an ID set.
		:type dtc: int or :ref:`Dtc<DTC>`

		:param record_number: The record number of the extended data to read. If 0xFF is given, then all extended data entries will be read, otherwise, a single entry will be read.
		:type record_number: int

		:param data_size: The number of bytes of an extended data record. If not specified ``config['extended_data_size'][dtc]`` will be used.
		:type data_size: int or None

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportDTCExtendedDataRecordByDTCNumber, dtc=dtc, extended_data_record_number=record_number,extended_data_size=data_size)

	def get_mirrormemory_dtc_extended_data_by_dtc_number(self, dtc, record_number=0xFF, data_size = None):
		"""
		Requests the server for one or many DTC **extended data** stored in mirror memory by specifying a record number.

		The DTC extended data is an ECU specific set of data that is not associated with a data identifier. Given as ``bytes``

		:dependent configuration: ``exception_on_<type>_response`` ``tolerate_zero_padding`` ``extended_data_size``

		:param dtc: The DTC ID for which we request the extended data. It can be a 3-byte integer or a DTC instance with an ID set.
		:type dtc: int or :ref:`Dtc<DTC>`

		:param record_number: The record number of the extended data to read. If 0xFF is given, then all extended data entries will be read, otherwise, a single entry will be read.
		:type record_number: int

		:param data_size: The number of bytes of an extended data record. If not specified ``config['extended_data_size'][dtc]`` wil be used.
		:type data_size: int or None

		:return: The server response parsed by :meth:`ReadDTCInformation.interpret_response<udsoncan.services.ReadDTCInformation.interpret_response>`
		:rtype: :ref:`Response<Response>`
		"""
		return self.read_dtc_information(services.ReadDTCInformation.Subfunction.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber, dtc=dtc, extended_data_record_number=record_number, extended_data_size=data_size)

	# Performs a ReadDiagnsticInformation service request.
	# Many requests are encoded the same way and many responses are encoded the same way. Request grouping and response grouping are independent.
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

		self.logger.info('%s - Sending request with subfunction "%s" (0x%02X).' % (self.service_log_prefix(services.ReadDTCInformation), services.ReadDTCInformation.Subfunction.get_name(subfunction), subfunction))
		self.logger.debug('\tParams are : %s' % str(request_params))
		response = self.send_request(request)
		if response is None:
			return

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

	# Basic transmission of requests. This will need to be improved
	def send_request(self, request, timeout=-1):
		if timeout < 0:
			# Timeout not provided by user: defaults to Client request_timeout value
			overall_timeout = self.config['request_timeout']
			single_request_timeout = min(overall_timeout, self.config['p2_timeout'])
		else:
			overall_timeout = timeout
			single_request_timeout = timeout
		overall_timeout_time = time.time() + overall_timeout
		using_p2_star = False	# Will switch to true when Nrc 0x78 will be received the first time.
		
		self.conn.empty_rxqueue()
		self.logger.debug("Sending request to server")
		override_suppress_positive_response = False
		if self.suppress_positive_response.enabled == True and request.service.use_subfunction():
			payload = request.get_payload(suppress_positive_response=True)
			override_suppress_positive_response = True
		else:
			payload = request.get_payload()

		if self.suppress_positive_response.enabled and not request.service.use_subfunction():
			self.logger.warning('SuppressPositiveResponse cannot be used for service %s. Ignoring' % (request.service.get_name()))

		self.conn.send(payload)

		if request.suppress_positive_response  or override_suppress_positive_response:
			return
		
		done_receiving = False

		while not done_receiving:
			done_receiving = True
			self.logger.debug("Waiting for server response")

			try:
				if time.time() + single_request_timeout < overall_timeout_time:	
					timeout_type_used 	= 'single_request'
					timeout_value 		= single_request_timeout
				else:	
					timeout_type_used 	= 'overall'
					timeout_value 		= max(overall_timeout_time - time.time(), 0)

				payload = self.conn.wait_frame(timeout=timeout_value, exception=True)	
			except TimeoutException:
				if timeout_type_used == 'single_request':
					timeout_name_to_report = 'P2* timeout' if using_p2_star else 'P2 timeout'
				elif timeout_type_used == 'overall':
					timeout_name_to_report = 'Global request timeout'
				else:	# Shouldn't go here.
					timeout_name_to_report = 'Timeout'
				raise TimeoutException('Did not receive response in time. %s time has expired (timeout=%.3f sec)' % (timeout_name_to_report, timeout_value))
			except Exception as e:
				raise e

			response = Response.from_payload(payload)
			self.last_response = response
			self.logger.debug("Received response from server")

			if not response.valid:
				raise InvalidResponseException(response)

			if response.service.response_id() != request.service.response_id():
				msg = "Response gotten from server has a service ID different than the request service ID. Received=0x%02x, Expected=0x%02x" % (response.service.response_id() , request.service.response_id() )
				raise UnexpectedResponseException(response, msg)

			if not response.positive:
				if not request.service.is_supported_negative_response(response.code):
					self.logger.warning('Given response code "%s" (0x%02x) is not a supported negative response code according to UDS standard.' % (response.code_name, response.code))

				if response.code == Response.Code.RequestCorrectlyReceived_ResponsePending:
						done_receiving = False
						if not using_p2_star:
							# Received a 0x78 NRC: timeout is now set to P2*
							single_request_timeout = self.config['p2_star_timeout']
							using_p2_star = True
							self.logger.debug("Server requested to wait with response code %s (0x%02x), single request timeout is now set to P2* (%.3f seconds)" % (response.code_name, response.code, single_request_timeout))
				else:
					raise NegativeResponseException(response)

		self.logger.info('Received positive response for service %s (0x%02x) from server.' % (response.service.get_name(), response.service.request_id()))
		return response
