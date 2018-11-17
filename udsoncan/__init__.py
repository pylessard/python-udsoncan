#!/usr/bin/env python
# -*- coding: utf-8 -*-

import inspect
import struct
import math

from udsoncan.exceptions import *
from udsoncan.Request import Request
from udsoncan.Response import Response

import logging, logging.config
from os import path
__default_log_config_file = path.join(path.dirname(path.abspath(__file__)), 'logging.conf')

def setup_logging(config_file = __default_log_config_file):
	"""
	This function setup the logger accordingly to the module provided cfg file
	"""
	try:
		logging.config.fileConfig(config_file)
	except Exception as e:
		logging.warning('Cannot load logging configuration from %s. %s:%s' % (config_file, e.__class__.__name__, str(e)))

#Define how to encode/decode a Data Identifier value to/from a binary payload
class DidCodec:
	"""
	This class defines how to encode/decode a Data Identifier value to/from a binary payload.

	One should extend this class and override the ``encode``, ``decode``, ``__len__`` methods as they will be used
	to generate or parse binary payloads.

		- ``encode`` Must receive any Python object and must return a bytes payload
		- ``decode`` Must receive a bytes payload and may return any Python object
		- ``__len__`` Must return the length of the bytes payload

	If a data can be processed by a pack string, then this class may be used as is, without being extended.

	:param packstr: A pack string used with struct.pack / struct.unpack. 
	:type packstr: string
	"""

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

	#Must tell the size of the payload encoded or expected for decoding
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
			if len(didconfig) == 0:
				raise ValueError("pack/unpack string given for Codec config should not be empty.")
			return cls(packstr = didconfig)

class AsciiCodec(DidCodec):
	def __init__(self, string_len=None):
		if string_len is None:
			raise ValueError("You must provide a string length to the AsciiCodec")
		self.string_len = string_len

	def encode(self, string_ascii):
		if len(string_ascii) != self.string_len:
			raise ValueError('String must be %d long' % self.string_len)
		return string_ascii.encode('ascii')

	def decode(self, string_bin):
		string_ascii = string_bin.decode('ascii')
		if len(string_ascii) != self.string_len:
			raise ValueError('Trying to decode a string of %d bytes but codec expects %d bytes' % (len(string_ascii), self.string_len))
		return string_ascii

	def __len__(self):
		return self.string_len


# Some standards, such as J1939, break down the 3-byte ID into 2-byte ID and 1-byte subtypes. 
class Dtc:
	"""
	Defines a Diagnostic Trouble Code which consist of a 3-byte ID, a status, a severity and some diagnostic data.

	:param dtcid: The 3-byte ID of the DTC
	:type dtcid: int
	
	"""
	class Format:
		"""
		Provide a list of DTC formats and their indices. These values are used by the :ref:`The ReadDTCInformation<ReadDtcInformation>` when requesting a number of DTCs.		
		"""
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

	# DTC Status byte
	# This byte is an 8-bit flag indicating how much we are sure that a DTC is active.
	class Status:
		"""
		Represents a DTC status which consists of 8 boolean flags (a byte). All flags can be set after instantiation without problems. 

		:param test_failed: DTC is no longer failed at the time of the request
		:type test_failed: bool

		:param test_failed_this_operation_cycle: DTC never failed on the current operation cycle.
		:type test_failed_this_operation_cycle: bool

		:param pending: DTC failed on the current or previous operation cycle.
		:type pending: bool

		:param confirmed: DTC is not confirmed at the time of the request.
		:type confirmed: bool

		:param test_not_completed_since_last_clear: DTC test has been completed since the last codeclear.
		:type test_not_completed_since_last_clear: bool

		:param test_failed_since_last_clear: DTC test failed at least once since last code clear.
		:type test_failed_since_last_clear: bool

		:param test_not_completed_this_operation_cycle: DTC test completed this operation cycle.
		:type test_not_completed_this_operation_cycle: bool

		:param warning_indicator_requested: Server is not requesting warningIndicator to be active.
		:type warning_indicator_requested: bool
		"""

		def __init__(self, test_failed=False, test_failed_this_operation_cycle=False, pending=False, confirmed=False, test_not_completed_since_last_clear=False, test_failed_since_last_clear=False, test_not_completed_this_operation_cycle=False, warning_indicator_requested=False):
			self.test_failed 								= test_failed
			self.test_failed_this_operation_cycle 			= test_failed_this_operation_cycle
			self.pending 									= pending
			self.confirmed 									= confirmed
			self.test_not_completed_since_last_clear 		= test_not_completed_since_last_clear
			self.test_failed_since_last_clear 				= test_failed_since_last_clear
			self.test_not_completed_this_operation_cycle 	= test_not_completed_this_operation_cycle
			self.warning_indicator_requested 				= warning_indicator_requested

		def get_byte_as_int(self):	# Returns the status byte as an integer 
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

		def get_byte(self):	# Returns the status byte in "bytes" format for payload creation
			return struct.pack('B', self.get_byte_as_int())

		def set_byte(self, byte):	# Set all the status flags from the status byte
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

		@classmethod
		def from_byte(cls, byte):
			status = cls()
			status.set_byte(byte)
			return status

	# DTC Severity byte, it's a 3-bit indicator telling how serious a trouble code is.
	class Severity:
		"""
		Represents a DTC severity which consists of 3 boolean flags. All flags can be set after instantiation without problems. 

		:param maintenance_only: This value indicates that the failure requests maintenance only
		:type maintenance_only: bool

		:param check_at_next_exit: This value indicates that the failure requires a check of the vehicle at the next halt.
		:type check_at_next_exit: bool

		:param check_immediately: This value indicates that the failure requires an immediate check of the vehicle.
		:type check_immediately: bool
		"""
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
		self.snapshots = []  		# . DID codec must be configured
		self.extended_data = [] 	
		self.severity = Dtc.Severity()
		self.functional_unit = None 	# Implementation specific (ISO 14229 D.4)
		self.fault_counter = None 		# Common practice is to detect a specific failure many times before setting the DTC active. This counter should tell the actual count.

	
	def __repr__(self):
		return '<DTC ID=0x%06x, Status=0x%02x, Severity=0x%02x at 0x%08x>' % (self.id, self.status.get_byte_as_int(), self.severity.get_byte_as_int(), id(self))

	# A snapshot data. Not defined by ISO14229 and implementation specific. 
	# To read this data, the client must have a DID codec set in its config.
	class Snapshot:
		record_number = None
		did = None
		data = None
		raw_data = b''

	# Extended data. Not defined by ISO14229 and implementation specific
	# Only raw data can be given to user.
	class ExtendedData:
		record_number = None
		raw_data = b''
		

class AddressAndLengthFormatIdentifier:
	"""
	This class defines how many bytes of a memorylocation, composed of an address and a memorysize, should be encoded when sent over the underlying protocol.
	Mainly used by :ref:`ReadMemoryByAddress<ReadMemoryByAddress>`, :ref:`WriteMemoryByAddress<WriteMemoryByAddress>`, :ref:`RequestDownload<RequestDownload>` and :ref:`RequestUpload<RequestUpload>` services
	
	Defined by ISO-14229:2006, Annex G

	:param address_format: The number of bits on which an address should be encoded. Possible values are 8, 16, 24, 32, 40
	:type address_format: int

	:param memorysize_format: The number of bits on which a memory size should be encoded. Possible values are 8, 16, 24, 32
	:type memorysize_format: int

	"""
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

	def __init__(self, address_format, memorysize_format):
		if address_format not in self.address_map:
			raise ValueError('address_format must ba an integer selected from : %s ' % (self.address_map.keys()))

		if not isinstance(memorysize_format, int) or not isinstance(address_format, int):
			raise ValueError('memorysize_format and address_format must be integers')

		if memorysize_format not in self.memsize_map:
			raise ValueError('memorysize_format must be an integer selected from : %s' % (self.memsize_map.keys()))
		

		self.memorysize_format = memorysize_format
		self.address_format = address_format

	def get_byte_as_int(self):
		return  ((self.memsize_map[self.memorysize_format] << 4) | (self.address_map[self.address_format])) & 0xFF

	# Byte given alongside a memory address and a length so that they are decoded properly.
	def get_byte(self):
		return  struct.pack('B', self.get_byte_as_int())

class MemoryLocation:
	"""
	This class defines a memory block location including : address, size, AddressAndLengthFormatIdentifier (address format and memory size format)
	
	:param address: A memory address pointing to the beginning of the memory block
	:type address: int
	
	:param memorysize: The size of the memory block
	:type memorysize: int
	
	:param address_format: The number of bits on which an address should be encoded. Possible values are 8, 16, 24, 32, 40.
		If ``None`` is specified, the smallest size required to store the given address will be used
	:type address_format: int or None
	
	:param memorysize_format: The number of bits on which a memory size should be encoded. Possible values are 8, 16, 24, 32
		If ``None`` is specified, the smallest size required to store the given memorysize will be used
	:type memorysize_format: int or None	

	"""
	def __init__(self, address, memorysize, address_format=None, memorysize_format=None):
		self.address = address
		self.memorysize = memorysize
		self.address_format = address_format
		self.memorysize_format = memorysize_format

		if address_format is None:
			address_format = self.autosize_address(address)
				
		if memorysize_format is None:
			memorysize_format = self.autosize_memorysize(memorysize)

		self.alfid = AddressAndLengthFormatIdentifier(memorysize_format=memorysize_format, address_format=address_format)
		
	# This is used by the client/server to set a format from a config object while letting the user override it
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

			self.alfid = AddressAndLengthFormatIdentifier(memorysize_format=memorysize_format, address_format=address_format)
		except:
			self.address_format = previous_address_format
			self.memorysize_format = previous_memorysize_format
			raise

	# Finds the smallest size that fits the address
	def autosize_address(self, val):
		fmt = math.ceil(val.bit_length()/8)*8
		if fmt > 40:
			raise ValueError("address size must be smaller or equal than 40 bits")
		return fmt

	# Finds the smallest size that fits the memory size
	def autosize_memorysize(self, val):
		fmt = math.ceil(val.bit_length()/8)*8
		if fmt > 32:
			raise ValueError("memory size must be smaller or equal than 32 bits")
		return fmt

	# Gets the address byte in the requested format
	def get_address_bytes(self):
		n = AddressAndLengthFormatIdentifier.address_map[self.alfid.address_format]

		data = struct.pack('>q', self.address)
		return data[-n:]


	# Gets the memory size byte in the requested format
	def get_memorysize_bytes(self):
		n = AddressAndLengthFormatIdentifier.memsize_map[self.alfid.memorysize_format]

		data = struct.pack('>q', self.memorysize)
		return data[-n:]

	# Generates an instance from the byte stream
	@classmethod
	def from_bytes(cls, address_bytes, memorysize_bytes):
		if not isinstance(address_bytes, bytes):
			raise ValueError('address_bytes must be a valid bytes object')

		if not isinstance(memorysize_bytes, bytes):
			raise ValueError('memorysize_bytes must be a valid bytes object')

		if len(address_bytes) > 5:
			raise ValueError('Address must be at most 40 bits long')

		if len(memorysize_bytes) > 4:
			raise ValueError('Memory size must be at most 32 bits long')

		address_bytes_padded = b'\x00' * (8-len(address_bytes)) + address_bytes
		memorysize_bytes_padded = b'\x00' * (8-len(memorysize_bytes)) + memorysize_bytes

		address = struct.unpack('>q', address_bytes_padded)[0]
		memorysize = struct.unpack('>q', memorysize_bytes_padded)[0]
		address_format = len(address_bytes) * 8
		memorysize_format = len(memorysize_bytes) * 8

		return cls(address=address, memorysize=memorysize, address_format=address_format, memorysize_format=memorysize_format)

	def __str__(self):
		return 'Address=0x%x (%d bits), Size=0x%x (%d bits)' % (self.address, self.alfid.address_format, self.memorysize, self.alfid.memorysize_format)

	def __repr__(self):
		return '<%s: %s at 0x%08x>' % (self.__class__.__name__, str(self), id(self))

class DataFormatIdentifier:
	"""
	Defines the compression and encryption method of a specific chunk of data. 
	Mainly used by the :ref:`RequestUpload<RequestUpload>` and :ref:`RequestDownload<RequestDownload>` services

	:param compression: Value between 0 and 0xF specifying the compression method. Only the value 0 has a meaning defined by UDS standard and it is `No compression`. 
		All other values are ECU manufacturer specific.
	:type compression: int 
	
	:param encryption: Value between 0 and 0xF specifying the encryption method. Only the value 0 has a meaning defined by UDS standard and it is `No encryption`. 
		All other values are ECU manufacturer specific.
	:type encryption: int

	"""
	def __init__(self, compression=0, encryption=0):
		both = (compression, encryption)
		for param in both:
			if not isinstance(param, int):
				raise ValueError('compression and encryption method must be an integer value')

			if param < 0 or param > 0xF:
				raise ValueError('compression and encryption method must each be an integer between 0 and 0xF')

		self.compression = compression
		self.encryption=encryption

	def get_byte_as_int(self):
		return ((self.compression & 0xF) << 4) | (self.encryption & 0xF)

	def get_byte(self):
		return struct.pack('B', self.get_byte_as_int())

	def __str__(self):
		return 'Compression:0x%x, Encryption:0x%x' % (self.compression, self.encryption)

	def __repr__(self):
		return '<%s: %s at 0x%08x>' % (self.__class__.__name__, str(self), id(self))

# Units defined in standard. Nowhere does the ISO-14229 make use of them, but they are defined
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


# Routine class that containes few definitions for usage with nice syntax.
# myRoutine = Routine.EraseMemory    or    print(Routine.name_from_id(myRoutine))
class Routine:
	"""
	Defines a list of constants that are routine identifiers defined by the UDS standard.
	This class provides no functionality apart from defining these constants
	"""
	DeployLoopRoutineID	= 0xE200
	EraseMemory	= 0xFF00
	CheckProgrammingDependencies = 0xFF01
	EraseMirrorMemoryDTCs = 0xFF02


	@classmethod
	def name_from_id(cls, routine_id):
		# Helper to print the type of requests (logging purpose) as defined by ISO-14229:2006, Annex F
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
	"""
	Defines a list of constants that are data identifiers defined by the UDS standard.
	This class provides no functionality apart from defining these constants
	"""
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

# Communication type is a single byte value including message type and subnet.
# Used by CommunicationControl service and defined by ISO-14229:2006 Annex B, table B.1
class CommunicationType:
	"""
	This class represents a pair of subnet and message types. This value is mainly used by the :ref:`CommunicationControl<CommunicationControl>` service

	:param subnet: Represent the subnet number. Value ranges from 0 to 0xF 
	:type subnet: int

	:param normal_msg: Bit indicating that the `normal messages` are involved
	:type normal_msg: bool

	:param network_management_msg: Bit indicating that the `network management messages` are involved
	:type network_management_msg: bool

	"""
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
		self.normal_msg = normal_msg
		self.network_management_msg = network_management_msg

	def get_byte_as_int(self):
		message_type = 0
		if self.normal_msg:
			message_type |= 1
		if self.network_management_msg:
			message_type |= 2

		byte = (message_type & 0x3) | ((self.subnet.value() & 0xF) << 4)
		return byte

	def get_byte(self):
		return struct.pack('B', self.get_byte_as_int())

	@classmethod
	def from_byte(cls, val):
		if isinstance(val, bytes):
			val = struct.unpack('B', val)[0]
		val = int(val)
		subnet = (val & 0xF0) >> 4
		normal_msg = True if val & 1 > 0 else False
		network_management_msg = True if val & 2 > 0 else False
		return cls(subnet,normal_msg,network_management_msg)

	def __str__(self):
		flags = []
		if self.normal_msg:
			flags.append('NormalMsg')

		if self.network_management_msg:
			flags.append('NetworkManagementMsg')

		return 'subnet=0x%x. Flags : [%s]' % (self.subnet.value(), ','.join(flags))

	def __repr__(self):
		return '<%s: %s at 0x%08x>' % (self.__class__.__name__, str(self), id(self))

class Baudrate:
	"""
	Represents a link speed in bit per seconds (or symbol per seconds to be more accurate).
	This class is used by the :ref:`LinkControl<LinkControl>` service that controls the underlying protocol speeds.

	The class can encode the baudrate in 2 different fashions : **Fixed** or **Specific**.
	
	Some standard baudrate values are defined within ISO-14229:2006 Annex B.3
	
	:param baudrate: The baudrate to be used. 
	:type baudrate: int
	
	:param baudtype: Tells how the baudrate shall be encoded. 4 values are possible:

		- ``Baudrate.Type.Fixed`` (0) : Will encode the baudrate in a single byte Fixed fashion. `baudrate` should be a supported value such as 9600, 19200, 125000, 250000, etc.
		- ``Baudrate.Type.Specific`` (1) : Will encode the baudrate in a three-byte Specific fashion. `baudrate` can be any value ranging from 0 to 0xFFFFFF
		- ``Baudrate.Type.Identifier`` (2) : Will encode the baudrate in a single byte Fixed fashion. `baudrate` should be the byte value to encode if the user wants to use a custom type.
		- ``Baudrate.Type.Auto`` (3) : Let the class guess the type. 
			
			- If ``baudrate`` is a known standard value (19200, 38400, etc), then Fixed shall be used
			- If ``baudrate`` is an integer that fits in a single byte, then Identifier shall be used
			- If ``baudrate`` is none of the above, then Specific will be used.
	:type baudtype: int

	"""
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
		Fixed = 0		# When baudrate is a predefined value from standard
		Specific = 1	# When using custom baudrate
		Identifier = 2  # Baudrate implied by baudrate ID
		Auto = 3		# Let the class decide the type

	# User can specify the type of baudrate or let this class guess what he wants (this adds some simplicity for non-experts).
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

	# internal helper to change the type of this baudrate
	def make_new_type(self, baudtype):
		if baudtype not in [self.Type.Fixed, self.Type.Specific]:
			raise ValueError('Baudrate type can only be change to Fixed or Specific')

		return Baudrate(self.effective_baudrate(), baudtype=baudtype)

	# Returns the baudrate in Symbol Per Seconds if available, otherwise value given by the user.
	def effective_baudrate(self):
		if self.baudtype == self.Type.Identifier:
			for k in self.baudrate_map:
				if self.baudrate_map[k] == self.baudrate:
					return k

			raise RuntimeError('Unknown effective baudrate, this could indicate a bug')
		else:
			return self.baudrate

	# Encodes the baudrate value the way they are exchanged.
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

	def __str__(self):
		baudtype_str = ''
		if self.baudtype == self.Type.Fixed:
			baudtype_str = 'Fixed'
		elif self.baudtype == self.Type.Specific:
			baudtype_str = 'Specific'
		elif self.baudtype == self.Type.Identifier:
			baudtype_str = 'Defined by identifier'

		return '%sBauds, %s format.' % (str(self.effective_baudrate()), baudtype_str)

	def __repr__(self):
		return '<%s: %s at 0x%08x>' % (self.__class__.__name__, str(self), id(self))

#Used for IO Control service. Allows comprehensive one-liner.
class IOMasks:
	"""
	Allow to specify a list of masks for a :ref:`InputOutputControlByIdentifier<InputOutputControlByIdentifier>` composite codec.
	
	Example : IOMasks(mask1,mask2, mask3=True, mask4=False)

	:param args: Masks to set to True
	:param kwargs: Masks and their values
	"""
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

#Used for IO Control service. Allows comprehensive one-liner.
class IOValues:
	"""
	This class saves a function argument so they can be passed to a callback function.

	:param args: Arguments
	:param kwargs: Named arguments
	"""
	def __init__(self, *args, **kwargs):
		self.args = args
		self.kwargs = kwargs