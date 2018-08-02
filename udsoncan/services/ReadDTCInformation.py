from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class ReadDTCInformation(BaseService):
	_sid = 0x19

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestOutOfRange
							]

	class Subfunction(BaseSubfunction):
		__pretty_name__ = 'subfunction'

		reportNumberOfDTCByStatusMask = 1
		reportDTCByStatusMask = 2
		reportDTCSnapshotIdentification = 3
		reportDTCSnapshotRecordByDTCNumber = 4
		reportDTCSnapshotRecordByRecordNumber = 5
		reportDTCExtendedDataRecordByDTCNumber = 6
		reportNumberOfDTCBySeverityMaskRecord = 7
		reportDTCBySeverityMaskRecord = 8
		reportSeverityInformationOfDTC = 9
		reportSupportedDTCs = 0xA
		reportFirstTestFailedDTC = 0xB
		reportFirstConfirmedDTC = 0xC
		reportMostRecentTestFailedDTC = 0xD
		reportMostRecentConfirmedDTC = 0xE
		reportMirrorMemoryDTCByStatusMask = 0xF
		reportMirrorMemoryDTCExtendedDataRecordByDTCNumber = 0x10
		reportNumberOfMirrorMemoryDTCByStatusMask = 0x11
		reportNumberOfEmissionsRelatedOBDDTCByStatusMask = 0x12
		reportEmissionsRelatedOBDDTCByStatusMask = 0x13
		reportDTCFaultDetectionCounter = 0x14
		reportDTCWithPermanentStatus = 0x15

	@classmethod
	def assert_severity_mask(cls, severity_mask, subfunction):
		if severity_mask is None:
			raise ValueError('severity_mask must be provided for subfunction 0x%02x' % subfunction)
		ServiceHelper.validate_int(severity_mask, min=0, max=0xFF, name='Severity mask')

	@classmethod		
	def assert_status_mask(cls, status_mask, subfunction):
		if status_mask is None:
			raise ValueError('status_mask must be provided for subfunction 0x%02x' % subfunction)
		ServiceHelper.validate_int(status_mask, min=0, max=0xFF, name='Status mask')
	
	@classmethod	
	def assert_dtc(cls, dtc, subfunction):
		if dtc is None:
			raise ValueError('A dtc value must be provided for subfunction 0x%02x' % subfunction)
		ServiceHelper.validate_int(dtc, min=0, max=0xFFFFFF, name='DTC')
	
	@classmethod	
	def assert_snapshot_record_number(cls, snapshot_record_number, subfunction):
		if snapshot_record_number is None:
			raise ValueError('snapshot_record_number must be provided for subfunction 0x%02x' % subfunction)
		ServiceHelper.validate_int(snapshot_record_number, min=0, max=0xFF, name='Snapshot record number')
	
	@classmethod	
	def assert_extended_data_record_number(cls, extended_data_record_number, subfunction):
		if extended_data_record_number is None:
			raise ValueError('extended_data_record_number must be provided for subfunction 0x%02x' % subfunction)
		ServiceHelper.validate_int(extended_data_record_number, min=0, max=0xFF, name='Extended data record number')
	
	@classmethod	
	def assert_extended_data_size(cls, extended_data_size, subfunction):
		if extended_data_size is None:
			raise ValueError('extended_data_size must be provided as length of data is not given by the server.')
		ServiceHelper.validate_int(extended_data_size, min=0, max=0xFFF, name='Extended data size')
	
	@classmethod	
	def pack_dtc(cls, dtcid):
		return struct.pack('BBB', (dtcid >> 16) & 0xFF, (dtcid >> 8) & 0xFF,  (dtcid >> 0) & 0xFF)


	@classmethod
	def make_request(cls, subfunction, status_mask=None, severity_mask=None,  dtc=None, snapshot_record_number=None, extended_data_record_number=None):
		"""
		Generates a request for ReadDTCInformation. 
		Each subfunction uses a subset of parameters. 

		:param subfunction: The service subfunction. Values are defined in :class:`ReadDTCInformation.Subfunction<ReadDTCInformation.Subfunction>`
		:type subfunction: int

		:param status_mask: A DTC status mask used to filter DTC
		:type status_mask: int or :ref:`Dtc.Status <DTC_Status>`

		:param severity_mask: A severity mask used to filter DTC 
		:type severity_mask: int or :ref:`Dtc.Severity <DTC_Severity>`

		:param dtc: A DTC mask used to filter DTC
		:type dtc: int or :ref:`Dtc <DTC>`

		:param snapshot_record_number: Snapshot record number
		:type snapshot_record_number: int

		:param extended_data_record_number: Extended data record number
		:type extended_data_record_number: int

		:raises ValueError: If parameters are out of range, missing or wrong type
		"""	

		from udsoncan import Request, Dtc

		# Request grouping for subfunctions that have the same request format
		request_subfn_no_param = [
			ReadDTCInformation.Subfunction.reportSupportedDTCs,
			ReadDTCInformation.Subfunction.reportFirstTestFailedDTC,
			ReadDTCInformation.Subfunction.reportFirstConfirmedDTC,
			ReadDTCInformation.Subfunction.reportMostRecentTestFailedDTC,
			ReadDTCInformation.Subfunction.reportMostRecentConfirmedDTC,
			ReadDTCInformation.Subfunction.reportDTCFaultDetectionCounter,
			ReadDTCInformation.Subfunction.reportDTCWithPermanentStatus,

			# Documentation is confusing about reportDTCSnapshotIdentification subfunction.
			# It is presented with reportDTCSnapshotRecordByDTCNumber (2 params) but a footnote says that these 2 parameters
			# are not to be provided for reportDTCSnapshotIdentification. Therefore, it is the same as other no-params subfn
			ReadDTCInformation.Subfunction.reportDTCSnapshotIdentification	

			]

		request_subfn_status_mask = [
			ReadDTCInformation.Subfunction.reportNumberOfDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportMirrorMemoryDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportNumberOfMirrorMemoryDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportNumberOfEmissionsRelatedOBDDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportEmissionsRelatedOBDDTCByStatusMask
		]

		request_subfn_mask_record_plus_snapshot_record_number = [
			ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByDTCNumber
		]

		request_subfn_snapshot_record_number = [
			ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByRecordNumber
		]

		request_subfn_mask_record_plus_extdata_record_number = [
			ReadDTCInformation.Subfunction.reportDTCExtendedDataRecordByDTCNumber,
			ReadDTCInformation.Subfunction.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber
		]

		request_subfn_severity_plus_status_mask = [
			ReadDTCInformation.Subfunction.reportNumberOfDTCBySeverityMaskRecord,
			ReadDTCInformation.Subfunction.reportDTCBySeverityMaskRecord
		]

		request_subfn_mask_record = [
			ReadDTCInformation.Subfunction.reportSeverityInformationOfDTC		
			]


		ServiceHelper.validate_int(subfunction, min=1, max=0x15, name='Subfunction')
		
		if status_mask is not None and isinstance(status_mask, Dtc.Status):
			status_mask = status_mask.get_byte_as_int()

		if severity_mask is not None and isinstance(severity_mask, Dtc.Severity):
			severity_mask = severity_mask.get_byte_as_int()

		if dtc is not None and isinstance(dtc, Dtc):
			dtc = dtc.id

		req = Request(service=cls, subfunction=subfunction)

		if subfunction in request_subfn_no_param:		# Service ID + Subfunction
			pass

		elif subfunction in request_subfn_status_mask:
			cls.assert_status_mask(status_mask, subfunction)
			req.data = struct.pack('B', status_mask)

		elif subfunction in request_subfn_mask_record_plus_snapshot_record_number:
			cls.assert_dtc(dtc, subfunction)
			cls.assert_snapshot_record_number(snapshot_record_number, subfunction)
			req.data = cls.pack_dtc(dtc) + struct.pack('B', snapshot_record_number)

		elif subfunction in request_subfn_snapshot_record_number:
			cls.assert_snapshot_record_number(snapshot_record_number, subfunction)
			req.data = struct.pack('B', snapshot_record_number)

		elif subfunction in request_subfn_mask_record_plus_extdata_record_number:
			cls.assert_dtc(dtc, subfunction)
			cls.assert_extended_data_record_number(extended_data_record_number, subfunction)
			req.data = cls.pack_dtc(dtc) + struct.pack('B', extended_data_record_number)

		elif subfunction in request_subfn_severity_plus_status_mask:
			cls.assert_status_mask(status_mask, subfunction)
			cls.assert_severity_mask(severity_mask, subfunction)
			req.data = struct.pack('BB', severity_mask, status_mask)

		elif subfunction in request_subfn_mask_record:
			cls.assert_dtc(dtc, subfunction)
			req.data = cls.pack_dtc(dtc)

		return req

	@classmethod
	def interpret_response(cls, response, subfunction,  extended_data_size=None, tolerate_zero_padding=True, ignore_all_zero_dtc=True, dtc_snapshot_did_size=2, didconfig=None):
		"""
		Populates the response ``service_data`` property with an instance of :class:`ReadDTCInformation.ResponseData<udsoncan.services.ReadDTCInformation.ResponseData>`

		:param response: The received response to interpret
		:type response: :ref:`Response<Response>`

		:param subfunction: The service subfunction. Values are defined in :class:`ReadDTCInformation.Subfunction<udsoncan.services.ReadDTCInformation.Subfunction>`
		:type subfunction: int

		:param extended_data_size: Extended data size to expect. Extended data is implementation specific, therefore, size is not standardized
		:type extended_data_size: int

		:param tolerate_zero_padding: Ignore trailing zeros in the response data avoiding raising false :class:`InvalidResponseException<udsoncan.exceptions.InvalidResponseException>`.
		:type tolerate_zero_padding:  bool

		:param ignore_all_zero_dtc: Discard any DTC entries that have an ID of 0. Avoid reading extra DTCs when using a transport protocol using zero padding.
		:type ignore_all_zero_dtc: bool

		:param dtc_snapshot_did_size: Number of bytes to encode the data identifier number. Other services such as :ref:`ReadDataByIdentifier<ReadDataByIdentifier>` encode DID over 2 bytes.
			UDS standard does not define the size of the snapshot DID, therefore, it must be supplied.
		:type dtc_snapshot_did_size: int

		:param didconfig: Definition of DID codecs. Dictionary mapping a DID (int) to a valid :ref:`DidCodec<DidCodec>` class or pack/unpack string 
		:type didconfig: dict[int] = :ref:`DidCodec<DidCodec>`
		
		:raises InvalidResponseException: If response length is wrong or does not match DID configuration
		:raises ValueError: If parameters are out of range, missing or wrong types
		:raises ConfigError: If the server returns a snapshot DID not defined in ``didconfig``
		"""	

		from udsoncan import Dtc, DidCodec
		ServiceHelper.validate_int(subfunction, min=1, max=0x15, name='Subfunction')

		# Response grouping for responses that are encoded the same way
		response_subfn_dtc_availability_mask_plus_dtc_record = [
			ReadDTCInformation.Subfunction.reportDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportSupportedDTCs,
			ReadDTCInformation.Subfunction.reportFirstTestFailedDTC,
			ReadDTCInformation.Subfunction.reportFirstConfirmedDTC,
			ReadDTCInformation.Subfunction.reportMostRecentTestFailedDTC,
			ReadDTCInformation.Subfunction.reportMostRecentConfirmedDTC,
			ReadDTCInformation.Subfunction.reportMirrorMemoryDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportEmissionsRelatedOBDDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportDTCWithPermanentStatus
		]

		response_subfn_number_of_dtc = [
			ReadDTCInformation.Subfunction.reportNumberOfDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportNumberOfDTCBySeverityMaskRecord,
			ReadDTCInformation.Subfunction.reportNumberOfMirrorMemoryDTCByStatusMask,
			ReadDTCInformation.Subfunction.reportNumberOfEmissionsRelatedOBDDTCByStatusMask,
		]

		response_subfn_dtc_availability_mask_plus_dtc_record_with_severity = [
			ReadDTCInformation.Subfunction.reportDTCBySeverityMaskRecord,
			ReadDTCInformation.Subfunction.reportSeverityInformationOfDTC
		]
		
		response_subfn_dtc_plus_fault_counter = [
			ReadDTCInformation.Subfunction.reportDTCFaultDetectionCounter
		]

		response_subfn_dtc_plus_sapshot_record = [
			ReadDTCInformation.Subfunction.reportDTCSnapshotIdentification
		]

		response_sbfn_dtc_status_snapshots_records = [
			ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByDTCNumber
		]

		response_sbfn_dtc_status_snapshots_records_record_first = [
			ReadDTCInformation.Subfunction.reportDTCSnapshotRecordByRecordNumber
		]

		response_subfn_mask_record_plus_extdata = [
			ReadDTCInformation.Subfunction.reportDTCExtendedDataRecordByDTCNumber,
			ReadDTCInformation.Subfunction.reportMirrorMemoryDTCExtendedDataRecordByDTCNumber
		]

		
		response.service_data = cls.ResponseData()	# what will be returned 
		
		if len(response.data) < 1:
			raise InvalidResponseException(response, 'Response must be at least 1 byte long (echo of subfunction)')

		response.service_data.subfunction_echo = response.data[0]	# First byte is subfunction

		# Now for each response group, we have a different decoding algorithm
		if subfunction in response_subfn_dtc_availability_mask_plus_dtc_record + response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:

			if subfunction in response_subfn_dtc_availability_mask_plus_dtc_record:
				dtc_size = 4	# DTC ID (3) + Status (1)
			elif subfunction in response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:
				dtc_size = 6	# DTC ID (3) + Status (1) + Severity (1) + FunctionalUnit (1)

			if len(response.data) < 2:
				raise InvalidResponseException(response, 'Response must be at least 2 byte long (echo of subfunction and DTCStatusAvailabilityMask)')

			response.service_data.status_availability = Dtc.Status.from_byte(response.data[1])

			actual_byte = 2	# Increasing index
			while True:	# Loop until we have read all dtcs
				if len(response.data) <= actual_byte:
					break	# done

				elif len(response.data) < actual_byte+dtc_size:
					partial_dtc_length = len(response.data)-actual_byte
					if tolerate_zero_padding and response.data[actual_byte:] == b'\x00'*partial_dtc_length:
						break
					else:
						# We purposely ignore extra byte for subfunction reportSeverityInformationOfDTC as it is supposed to return 0 or 1 DTC.
						if subfunction != ReadDTCInformation.Subfunction.reportSeverityInformationOfDTC or actual_byte == 2: 
							raise InvalidResponseException(response, 'Incomplete DTC record. Missing %d bytes to response to complete the record' % (dtc_size-partial_dtc_length))

				else:
					dtc_bytes = response.data[actual_byte:actual_byte+dtc_size]
					if dtc_bytes == b'\x00'*dtc_size and ignore_all_zero_dtc:
						pass # ignore
					else:
						if subfunction in response_subfn_dtc_availability_mask_plus_dtc_record:
							dtc = Dtc(struct.unpack('>L', b'\x00' + dtc_bytes[0:3])[0])
							dtc.status.set_byte(dtc_bytes[3])
						elif subfunction in response_subfn_dtc_availability_mask_plus_dtc_record_with_severity:
							dtc = Dtc(struct.unpack('>L', b'\x00' + dtc_bytes[2:5])[0])
							dtc.severity.set_byte(dtc_bytes[0])
							dtc.functional_unit = dtc_bytes[1]
							dtc.status.set_byte(dtc_bytes[5])

						response.service_data.dtcs.append(dtc)
				actual_byte += dtc_size
			response.service_data.dtc_count = len(response.service_data.dtcs)

		# The 2 following subfunction responses have different purposes but their constructions are very similar.
		elif subfunction in response_subfn_dtc_plus_fault_counter + response_subfn_dtc_plus_sapshot_record:
			dtc_size = 4
			if len(response.data) < 1:
				raise InvalidResponseException(response, 'Response must be at least 1 byte long (echo of subfunction)')

			actual_byte = 1 	# Increasing index
			dtc_map = dict()	# This map is used to append snapshot to existing DTC.

			while True: 	# Loop until we have read all dtcs
				if len(response.data) <= actual_byte:
					break 	# done

				elif len(response.data) < actual_byte+dtc_size:
					partial_dtc_length = len(response.data)-actual_byte
					if tolerate_zero_padding and response.data[actual_byte:] == b'\x00'*partial_dtc_length:
						break
					else:
						raise InvalidResponseException(response, 'Incomplete DTC record. Missing %d bytes to response to complete the record' % (dtc_size-partial_dtc_length))
				else:
					dtc_bytes = response.data[actual_byte:actual_byte+dtc_size]
					if dtc_bytes == b'\x00'*dtc_size and ignore_all_zero_dtc:
						pass # ignore
					else:		
						dtcid = struct.unpack('>L', b'\x00' + dtc_bytes[0:3])[0]
						# We create the DTC or get its reference if already created.
						dtc_created = False	
						if dtcid in dtc_map and subfunction in response_subfn_dtc_plus_sapshot_record:
							dtc = dtc_map[dtcid]
						else:
							dtc = Dtc(dtcid)
							dtc_map[dtcid] = dtc
							dtc_created = True

						# We either read the DTC fault counter or Snapshot record number. 
						if subfunction in response_subfn_dtc_plus_fault_counter:
							dtc.fault_counter = dtc_bytes[3]

						elif subfunction in response_subfn_dtc_plus_sapshot_record:
							record_number = dtc_bytes[3]

							if dtc.snapshots is None:
								dtc.snapshots = []

							dtc.snapshots.append(record_number)
						
						# Adds the DTC to the list.
						if dtc_created:
							response.service_data.dtcs.append(dtc)
							
				actual_byte += dtc_size

			response.service_data.dtc_count = len(response.service_data.dtcs)

		# This group of responses returns a number of DTCs available
		elif subfunction in response_subfn_number_of_dtc:
			if len(response.data) < 5:
				raise InvalidResponseException(response, 'Response must be exactly 5 bytes long ')

			response.service_data.status_availability = Dtc.Status.from_byte(response.data[1])
			response.service_data.dtc_format = response.data[2]
			response.service_data.dtc_count = struct.unpack('>H', response.data[3:5])[0]
		
		# This group of responses returns DTC snapshots
		# Responses include a DTC, many snapshot records. For each record, we find many Data Identifiers.
		# We create one Dtc.Snapshot for each DID. That'll be easier to work with.
		# <DTC,RecordNumber1,NumberOfDid_X,DID1,DID2,...DIDX, RecordNumber2,NumberOfDid_Y,DID1,DID2,...DIDY, etc>
		elif subfunction in  response_sbfn_dtc_status_snapshots_records:
			if len(response.data) < 5:
				raise InvalidResponseException(response, 'Response must be at least 5 bytes long ')

			dtc = Dtc(struct.unpack('>L', b'\x00' + response.data[1:4])[0])
			dtc.status.set_byte(response.data[4])
			actual_byte = 5		# Increasing index

			ServiceHelper.validate_int(dtc_snapshot_did_size, min=1, max=8, name='dtc_snapshot_did_size')

			while True:		# Loop until we have read all dtcs
				if len(response.data) <= actual_byte:
					break	# done

				remaining_data = response.data[actual_byte:]
				if tolerate_zero_padding and remaining_data == b'\x00' * len(remaining_data):
					break
					
				if len(remaining_data) < 2:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing "number of identifier" and following data')

				record_number = remaining_data[0]	
				number_of_did = remaining_data[1]
				# Validate record number and number of DID before continuing
				if number_of_did == 0:
					raise InvalidResponseException(response, 'Server returned snapshot record #%d with no data identifier included' % (record_number)) 

				if len(remaining_data) < 2 + dtc_snapshot_did_size:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing DID number and associated data.')

				actual_byte += 2
				for i in range(number_of_did):
					remaining_data = response.data[actual_byte:]
					snapshot = Dtc.Snapshot()	# One snapshot per DID for convenience.
					snapshot.record_number = record_number

					# As standard does not specify the length of the DID, we craft it based on a config 
					did = 0
					for j in range(dtc_snapshot_did_size):
						offset = dtc_snapshot_did_size-1-j
						did |= (remaining_data[offset] << (8*j))
					
					# Decode the data based on DID number.
					snapshot.did = did
					didconfig = ServiceHelper.check_did_config(did, didconfig)
					codec = DidCodec.from_config(didconfig[did])
					
					data_offset =  dtc_snapshot_did_size;
					if len(remaining_data[data_offset:]) < len(codec):
						raise InvalidResponseException(response, 'Incomplete response. Data for DID 0x%04x is only %d bytes while %d bytes is expected' % (did, len(remaining_data[data_offset:]), len(codec)))

					snapshot.raw_data = remaining_data[data_offset:data_offset + len(codec)]
					snapshot.data = codec.decode(snapshot.raw_data)

					dtc.snapshots.append(snapshot)
					actual_byte += dtc_snapshot_did_size + len(codec)

			response.service_data.dtcs.append(dtc)
			response.service_data.dtc_count = 1
		
		# This group of responses returns DTC snapshots
		# Responses include a DTC, many snapshots records. For each record, we find many Data Identifiers.
		# We create one Dtc.Snapshot for each DID. That'll be easier to work with.
		# Similar to previous subfunction group, but order of information is changed.

		# <RecordNumber1, DTC1,NumberOfDid_X,DID1,DID2,...DIDX, RecordNumber2,DTC2, NumberOfDid_Y,DID1,DID2,...DIDY, etc>
		elif subfunction in response_sbfn_dtc_status_snapshots_records_record_first :
			ServiceHelper.validate_int(dtc_snapshot_did_size, min=1, max=8, name='dtc_snapshot_did_size')

			if len(response.data) < 2:
				raise InvalidResponseException(response, 'Response must be at least 2 bytes long. Subfunction echo + RecordNumber ')

			actual_byte = 1	 # Increasing index
			while True:	# Loop through response data
				if len(response.data) <= actual_byte:
					break	# done

				remaining_data = response.data[actual_byte:]
				record_number = remaining_data[0]

				# If empty response but filled with 0, it is considered ok
				if remaining_data == b'\x00' * len(remaining_data) and tolerate_zero_padding:
					break

				# If record number received but no DTC provided (allowed according to standard), we exit.
				if len(remaining_data) == 1 or tolerate_zero_padding and remaining_data[1:] == b'\x00' * len(remaining_data[1:]):
					break

				if len(remaining_data) < 5: 	# Partial DTC (No DTC at all is checked above)
					raise InvalidResponseException(response, 'Incomplete response from server. Missing "DTCAndStatusRecord" and following data')

				if len(remaining_data) < 6:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing number of data identifier')

				# DTC decoding
				dtc = Dtc(struct.unpack('>L', b'\x00' + remaining_data[1:4])[0])
				dtc.status.set_byte(remaining_data[4])
				number_of_did = remaining_data[5]

				actual_byte += 6
				remaining_data = response.data[actual_byte:]

				if number_of_did == 0:
					raise InvalidResponseException(response, 'Server returned snapshot record #%d with no data identifier included' % (record_number)) 

				if len(remaining_data) < dtc_snapshot_did_size:
					raise InvalidResponseException(response, 'Incomplete response from server. Missing DID and associated data')

				# We have a DTC and 0 DID, next loop
				if tolerate_zero_padding and remaining_data == b'\x00' * len(remaining_data):
					break

				# For each DID
				for i in range(number_of_did):
					remaining_data = response.data[actual_byte:]
					snapshot = Dtc.Snapshot()	# One snapshot epr DID for convenience
					snapshot.record_number = record_number

					# As standard does not specify the length of the DID, we craft it based on a config 
					did = 0
					for j in range(dtc_snapshot_did_size):
						offset = dtc_snapshot_did_size-1-j
						did |= (remaining_data[offset] << (8*j))
					
					# Decode the data based on DID number.
					snapshot.did = did
					didconfig = ServiceHelper.check_did_config(did, didconfig)
					codec = DidCodec.from_config(didconfig[did])
					
					data_offset =  dtc_snapshot_did_size;
					if len(remaining_data[data_offset:]) < len(codec):
						raise InvalidResponseException(response, 'Incomplete response. Data for DID 0x%04x is only %d bytes while %d bytes is expected' % (did, len(remaining_data[data_offset:]), len(codec)))

					snapshot.raw_data = remaining_data[data_offset:data_offset + len(codec)]
					snapshot.data = codec.decode(snapshot.raw_data)

					dtc.snapshots.append(snapshot)

					actual_byte += dtc_snapshot_did_size + len(codec)

				response.service_data.dtcs.append(dtc)
			response.service_data.dtc_count = len(response.service_data.dtcs)

		# These subfunctions include DTC ExtraData. We give it raw to user.
		elif subfunction in response_subfn_mask_record_plus_extdata:
			cls.assert_extended_data_size(extended_data_size, subfunction)

			if len(response.data) < 5: 
				raise InvalidResponseException(response, 'Incomplete response from server. Missing DTCAndStatusRecord')
			# DTC decoding
			dtc = Dtc(struct.unpack('>L', b'\x00' + response.data[1:4])[0])
			dtc.status.set_byte(response.data[4])

			actual_byte = 5	# Increasing index
			while actual_byte < len(response.data):	# Loop through data
				remaining_data = response.data[actual_byte:]
				record_number = remaining_data[0]

				if record_number == 0:
					if remaining_data == b'\x00' * len(remaining_data) and tolerate_zero_padding:
						break
					else:
						raise InvalidResponseException(response, 'Extended data record number given by the server is 0 but this value is a reserved value.')

				actual_byte +=1
				remaining_data = response.data[actual_byte:]
				
				if len(remaining_data) < extended_data_size:
					raise InvalidResponseException(response, 'Incomplete response from server. Length of extended data for DTC 0x%06x with record number 0x%02x is %d bytes but smaller than given data_size of %d bytes' % (dtc.id, record_number, len(remaining_data), extended_data_size))

				exdata = Dtc.ExtendedData()
				exdata.record_number = record_number
				exdata.raw_data = remaining_data[0:extended_data_size]

				dtc.extended_data.append(exdata)

				actual_byte+= extended_data_size

			response.service_data.dtcs.append(dtc)
			response.service_data.dtc_count = len(response.service_data.dtcs)

	class ResponseData(BaseResponseData):
		"""
		.. data:: subfunction_echo
			
			Subfunction echoed back by the server

		.. data:: dtcs
			
			:ref:`DTC<DTC>` instances and their status read from the server.

		.. data:: dtc_count
			
			Number of DTC read or available

		.. data:: dtc_format
			
			Integer indicating the format of the DTC. See :ref:`DTC.Format<DTC_Format>`

		.. data:: status_availability
			
			:ref:`Dtc.Status<DTC_Status>` indicating which status the server supports

		.. data:: extended_data
			
			List of bytes containing the DTC extended data

		"""			
		def __init__(self):
			super().__init__(ReadDTCInformation)
			self.subfunction_echo = None
			self.dtcs = []
			self.dtc_count = 0
			self.dtc_format = None
			self.status_availability = None
			self.extended_data = []	