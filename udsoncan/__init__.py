import inspect
import struct
import math

from udsoncan.exceptions import *
from udsoncan.Request import Request
from udsoncan.Response import Response

#Define how to encode/decode a Data Identifier value to/from abinary payload
class DidCodec:

	def __init__(self, packstr=None):
		self.packstr = packstr

	def encode(self, *did_value):
		if self.packstr is None:
			raise NotImplementedError('Cannot encode DID to binary payload. Codec has no "encode" implementation')

		return struct.pack(self.packstr, *did_value)

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
		if isinstance(didconfig, cls):	#the given object already is a DidCodec instance
			return didconfig

		# The definition of the codec is a class. Returns an instance of this codec.
		if inspect.isclass(didconfig) and issubclass(didconfig, cls):	
			return didconfig()

		# It could be that the codec is in a dict. (for io_control)
		if isinstance(didconfig, dict) and 'codec' in didconfig:
			return cls.from_config(didconfig['codec'])

		# The codec can be defined by a struct pack/unpack string
		if isinstance(didconfig, str):
			return cls(packstr = didconfig)


class SecurityLevel(object):
	def __init__(self, levelid):
		self.levelid = levelid & 0xFE

class Dtc:
	class Format:
		ISO15031_6 = 0
		ISO14229_1 = 1
		SAE_J1939_73 = 2
		ISO11992_4 = 3

		@classmethod
		def get_name(cls, given_id):
			if given_id is None:
				return ""

			for member in inspect.getmembers(cls):
				if isinstance(member[1], int):
					if member[1] == given_id:
						return member[0]
						
			return None

	class Status:
		def __init__(self, test_failed=False, test_failed_this_operation_cycle=False, pending=False, confirmed=False, test_not_completed_since_last_clear=False, test_failed_since_last_clear=False, test_not_completed_this_operation_cycle=False, warning_indicator_requested=False):
			self.test_failed 								= test_failed
			self.test_failed_this_operation_cycle 			= test_failed_this_operation_cycle
			self.pending 									= pending
			self.confirmed 									= confirmed
			self.test_not_completed_since_last_clear 		= test_not_completed_since_last_clear
			self.test_failed_since_last_clear 				= test_failed_since_last_clear
			self.test_not_completed_this_operation_cycle 	= test_not_completed_this_operation_cycle
			self.warning_indicator_requested 				= warning_indicator_requested

		def get_byte_as_int(self):
			byte = 0
			byte |= 0x1 	if self.test_failed else 0
			byte |= 0x2 	if self.test_failed_this_operation_cycle else 0
			byte |= 0x4 	if self.pending else 0
			byte |= 0x8 	if self.confirmed else 0
			byte |= 0x10 	if self.test_not_completed_since_last_clear else 0
			byte |= 0x20 	if self.test_failed_since_last_clear else 0
			byte |= 0x40 	if self.test_not_completed_this_operation_cycle else 0
			byte |= 0x80 	if self.warning_indicator_requested else 0

			return byte

		def get_byte(self):
			return struct.pack('B', self.get_byte_as_int())

		def set_byte(self, byte):
			if not isinstance(byte, int) and not isinstance(byte, bytes):
				raise ValueError('Given byte must be an integer or bytes object.')

			if isinstance(byte, bytes):
				byte = struct.unpack('B', byte[0])

			self.test_failed 								= True if byte & 0x01 > 0 else False
			self.test_failed_this_operation_cycle 			= True if byte & 0x02 > 0 else False
			self.pending 									= True if byte & 0x04 > 0 else False
			self.confirmed 									= True if byte & 0x08 > 0 else False
			self.test_not_completed_since_last_clear 		= True if byte & 0x10 > 0 else False
			self.test_failed_since_last_clear 				= True if byte & 0x20 > 0 else False
			self.test_not_completed_this_operation_cycle	= True if byte & 0x40 > 0 else False
			self.warning_indicator_requested 				= True if byte & 0x80 > 0 else False

	class Severity:
		def __init__(self, maintenance_only=False, check_at_next_exit=False, check_immediately=False):
			self.maintenance_only 		= maintenance_only
			self.check_at_next_exit 	= check_at_next_exit
			self.check_immediately 		= check_immediately

		def get_byte_as_int(self):
			byte = 0
			byte |= 0x20 	if self.maintenance_only else 0
			byte |= 0x40 	if self.check_at_next_exit else 0
			byte |= 0x80 	if self.check_immediately else 0

			return byte

		def get_byte(self):
			return struct.pack('B', self.get_byte_as_int())

		def set_byte(self, byte):
			if not isinstance(byte, int) and not isinstance(byte, bytes):
				raise ValueError('Given byte must be an integer or bytes object.')

			if isinstance(byte, bytes):
				byte = struct.unpack('B', byte[0])

			self.maintenance_only 			= True if byte & 0x20 > 0 else False
			self.check_at_next_exit 		= True if byte & 0x40 > 0 else False
			self.check_immediately 			= True if byte & 0x80 > 0 else False

		@property
		def available(self):
			return True if self.get_byte_as_int() > 0 else False
			
	def __init__(self, dtcid):
		self.id = dtcid
		self.status = Dtc.Status()
		self.snapshots = []  		# Not defined by ISO14229. Must be defined in config
		self.extended_data = [] 	# Not defined by ISO14229. Must be defined in config
		self.severity = Dtc.Severity()
		self.functional_unit = None 	# Implementation specific (ISO 14229 D.4)
		self.fault_counter = None

	
	def __repr__(self):
		return '<DTC ID=0x%06x, Status=0x%02x, Severity=0x%02x at 0x%08x>' % (self.id, self.status.get_byte_as_int(), self.severity.get_byte_as_int(), id(self))

	class Snapshot:
		record_number = None
		did = None
		data = None
		raw_data = b''

		def decode(self):
			return self.codec.decode(self.data)

	class ExtendedData:
		record_number = None
		raw_data = b''
		

class AddressAndLengthIdentifier:
	#As defined by ISO-14229:2006, Annex G
	address_map = {
		8 	: 1,
		16 	: 2,
		24	: 3,
		32 	: 4,
		40	: 5
	}

	memsize_map = {
		8 : 1,
		16 : 2,
		24 : 3,
		32 : 4
	}

	def __init__(self, memorysize_format, address_format):
		if not isinstance(memorysize_format, int) or not isinstance(address_format, int):
			raise ValueError('memorysize_format and address_format must be integers')

		if memorysize_format not in self.memsize_map:
			raise ValueError('memorysize_format must be an integer selected from : %s' % (self.memsize_map.keys()))
		
		if address_format not in self.address_map:
			raise ValueError('address_format must ba an integer selected from : %s ' % (self.address_map.keys()))

		self.memorysize_format = memorysize_format
		self.address_format = address_format

	def get_byte(self):
		return  struct.pack('B', ((self.memsize_map[self.memorysize_format] << 4) | (self.address_map[self.address_format])) & 0xFF)

class MemoryLocation:
	def __init__(self, address, memorysize, address_format=None, memorysize_format=None):
		self.address = address
		self.memorysize = memorysize
		self.address_format = address_format
		self.memorysize_format = memorysize_format

		if address_format is None:
			address_format = self.autosize_address(address)
				
		if memorysize_format is None:
			memorysize_format = self.autosize_memorysize(memorysize)

		self.ali = AddressAndLengthIdentifier(memorysize_format=memorysize_format, address_format=address_format)
		
	def set_format_if_none(self, address_format=None, memorysize_format=None):
		previous_address_format = self.address_format
		previous_memorysize_format = self.memorysize_format
		try:
			if address_format is not None:
				if self.address_format is None:
					self.address_format = address_format

			if memorysize_format is not None:
				if address_format is None:
					self.memorysize_format=memorysize_format

			address_format = self.address_format if self.address_format is not None else self.autosize_address(self.address) 
			memorysize_format = self.memorysize_format if self.memorysize_format is not None else self.autosize_memorysize(self.memorysize) 

			self.ali = AddressAndLengthIdentifier(memorysize_format=memorysize_format, address_format=address_format)
		except:
			self.address_format = previous_address_format
			self.memorysize_format = previous_memorysize_format
			raise

	def autosize_address(self, val):
		fmt = math.ceil(val.bit_length()/8)*8
		if fmt > 40:
			raise ValueError("address size must be smaller or equal than 40 bits")
		return fmt

	def autosize_memorysize(self, val):
		fmt = math.ceil(val.bit_length()/8)*8
		if fmt > 32:
			raise ValueError("memory size must be smaller or equal than 32 bits")
		return fmt

	def get_address_bytes(self):
		n = AddressAndLengthIdentifier.address_map[self.ali.address_format]

		data = struct.pack('>q', self.address)
		return data[-n:]

	def get_memorysize_bytes(self):
		n = AddressAndLengthIdentifier.memsize_map[self.ali.memorysize_format]

		data = struct.pack('>q', self.memorysize)
		return data[-n:]

class DataFormatIdentifier:
	def __init__(self, compression=0, encryption=0):
		both = (compression, encryption)
		for param in both:
			if not isinstance(param, int):
				raise ValueError('compression and encryption method must be an integer value')

			if param < 0 or param > 0xF:
				raise ValueError('compression and encryption method must each be an integer between 0 and 0xF')

		self.compression = compression
		self.encryption=encryption

	def get_byte(self):
		return struct.pack('B', ((self.compression & 0xF) << 4) | (self.encryption & 0xF))

class Units:
	#As defined in ISO-14229:2006 Annex C
	class Prefixs:
		class Prefix:
			def __init__(self, id, name, symbol, description=None):
				self.name = name
				self.id = id
				self.symbol = symbol
				self.description = description

			def __str__(self):
				return self.name

			def __repr__(self):
				desc = "(%s) " % self.description if self.description is not None else ""
				return "<UDS Unit prefix : %s[%s] %swith ID=%d at %08x>" % (self.name, self.symbol, desc, self.id, id(self))
		exa		= Prefix(id=0x40, name= 'exa', 	symbol='E', description='10e18')
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


		def __str__(self):
			return self.name

		def __repr__(self):
			desc = "(unit of %s) " % self.description if self.description is not None else ""
			return "<UDS Unit : %s[%s] %swith ID=%d at %08x>" % (self.name, self.symbol, desc, self.id, id(self))
	
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
	psi					= Unit(id=0x27, name= 'pound force per square inch',symbol='psi', 		description='pressure')
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
	radians				= Unit(id=0x3D, name= 'radians square second', 		symbol='rad/s2', 	description='angular acceleration')
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

class CommunicationType:
# As defined by ISO-14229:2006 Annex B, table B.1
	class Subnet:
		node = 0
		network = 0xF

		def __init__(self, subnet):
			if not isinstance(subnet, int):
				raise ValueError('subnet must be an integer value')

			if subnet < 0 or subnet > 0xF:
				raise ValueError('subnet must be an integer between 0 and 0xF')

			self.subnet=subnet

		def value(self):
			return self.subnet

	def __init__(self, subnet, normal_msg=False, network_management_msg=False):

		if not isinstance(subnet, self.Subnet):
			subnet = self.Subnet(subnet)

		if not isinstance(normal_msg, bool) or not isinstance(network_management_msg, bool):
			raise ValueError('message type (normal_msg, network_management_msg) must be valid boolean values')

		if normal_msg == False and network_management_msg == False:
			raise ValueError('At least one message type must be controlled')

		self.subnet = subnet
		self.message_type = 0
		if normal_msg:
			self.message_type |= 1
		if network_management_msg:
			self.message_type |= 2

	def get_byte(self):
		byte = (self.message_type & 0x3) | ((self.subnet.value() & 0xF) << 4)
		return struct.pack('B', byte)

	@classmethod
	def from_byte(cls, byte):
		if isinstance(byte, bytes):
			val = struct.unpack('B', byte)[0]
		val = int(val)
		subnet = (val & 0xF0) >> 4
		normal_msg = True if val & 1 > 0 else False
		network_management_msg = True if val & 2 > 0 else False
		return cls(subnet,normal_msg,network_management_msg)

class Baudrate:
	baudrate_map = {
	9600 : 0x01,
	19200 : 0x02,
	38400 : 0x03,
	57600 : 0x04,
	115200 : 0x05,
	125000 : 0x10,
	250000 : 0x11,
	500000 : 0x12,
	1000000 : 0x13,
	}

	class Type:
		Fixed = 0		# When baudrate is predefined value from standard
		Specific = 1	# When using custom baudrate
		Identifier = 2  # Baudrate implied by baudrate ID
		Auto = 3		# Let the class decide the type

	def __init__(self, baudrate, baudtype=Type.Auto):
		if not isinstance(baudrate, int):
			raise ValueError('baudrate must be an integer')

		if baudrate < 0:
			raise ValueError('baudrate must be an integer greater than 0')

		if baudtype == self.Type.Auto:
			if baudrate in self.baudrate_map:
				self.baudtype = self.Type.Fixed
			else:
				if baudrate <= 0xFF:
					self.baudtype = self.Type.Identifier
				else:
					self.baudtype = self.Type.Specific
		else:
			self.baudtype = baudtype

		if self.baudtype == self.Type.Specific:
			if baudrate > 0xFFFFFF:
				raise ValueError('Baudrate value cannot be bigger than a 24 bits value.')

		elif self.baudtype == self.Type.Identifier:
			if baudrate > 0xFF:
				raise ValueError('Baudrate ID must be an integer between 0 and 0xFF')
		elif self.baudtype == self.Type.Fixed:
			if baudrate not in self.baudrate_map:
				raise ValueError('baudrate must be part of the supported baudrate list defined by UDS standard')
		else:
			raise ValueError('Unknown baudtype : %s' % self.baudtype)

		self.baudrate = baudrate

	def make_new_type(self, baudtype):
		if baudtype not in [self.Type.Fixed, self.Type.Specific]:
			raise ValueError('Baudrate type can only be change to Fixed or Specific')

		return Baudrate(self.effective_baudrate(), baudtype=baudtype)


	def effective_baudrate(self):
		if self.baudtype == self.Type.Identifier:
			for k in self.baudrate_map:
				if self.baudrate_map[k] == self.baudrate:
					return k

			raise RuntimeError('Unknown effective baudrate, this could indicate a bug')
		else:
			return self.baudrate

	def get_bytes(self):
		if self.baudtype == self.Type.Fixed:
			return struct.pack('B', self.baudrate_map[self.baudrate])

		if self.baudtype == self.Type.Specific:
			b1 = (self.baudrate >> 16 ) & 0xFF
			b2 = (self.baudrate >> 8 ) & 0xFF
			b3 = (self.baudrate >> 0 ) & 0xFF
			return struct.pack('BBB', b1, b2, b3)

		if self.baudtype==self.Type.Identifier:
			return struct.pack('B', self.baudrate)

		raise RuntimeError('Unknown baudrate baudtype : %s' % self.baudtype)

#Used for IO Control service. Allow comprehensive one-liner.
class IOMasks:
	def __init__(self, *args, **kwargs):
		for k in kwargs:
			if not isinstance(kwargs[k], bool):
				raise ValueError('mask value must be a boolean value')

		for k in args:
			if not isinstance(k, str):
				raise ValueError('Mask name must be a valid string')

		self.maskdict = dict();
		for k in args:
			self.maskdict[k] = True

		for k in kwargs:
			if not isinstance(kwargs[k], bool):
				raise ValueError('Mask value must be True or False') 
			self.maskdict[k] = kwargs[k]

	def get_dict(self):
		return self.maskdict


class IOValues:
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs