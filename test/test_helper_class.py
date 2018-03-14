from udsoncan import DataFormatIdentifier, AddressAndLengthIdentifier,MemoryLocation, CommunicationType, Baudrate, IOMasks, IOValues, Dtc
from test.UdsTest import UdsTest
import struct

class TestAddressAndLengthIdentifier(UdsTest):
	def test_ali_1(self):
		ali = AddressAndLengthIdentifier(memorysize_format=8, address_format=8)
		self.assertEqual(ali.get_byte(),b'\x11')

	def test_ali_2(self):
		ali = AddressAndLengthIdentifier(memorysize_format=16, address_format=8)
		self.assertEqual(ali.get_byte(),b'\x21')

	def test_ali_oob_values(self):	# Out Of Bounds Value
		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format=1, address_format=1)
		
		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format=0, address_format=8)

		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format=8, address_format=0)

		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format=40, address_format=0)

		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format=8, address_format=48)

		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format='8', address_format=8)

		with self.assertRaises(ValueError):
			AddressAndLengthIdentifier(memorysize_format=8, address_format='8')

class TestDataFormatIdentifier(UdsTest):
	def test_dfi(self):
		ali = DataFormatIdentifier(compression=1, encryption=2)
		self.assertEqual(ali.get_byte(),b'\x12')

	def test_dfi2(self):
		ali = DataFormatIdentifier(compression=15, encryption=15)
		self.assertEqual(ali.get_byte(),b'\xFF')

	def test_ali_oob_values(self):
		with self.assertRaises(ValueError):
			DataFormatIdentifier(compression=-1, encryption=1)
		
		with self.assertRaises(ValueError):
			DataFormatIdentifier(compression=1, encryption=-1)

		with self.assertRaises(ValueError):
			DataFormatIdentifier(compression=16, encryption=1)

		with self.assertRaises(ValueError):
			DataFormatIdentifier(compression=1, encryption=16)

class TestMemoryLocation(UdsTest):
	def test_memloc1(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0x78, address_format=16, memorysize_format=8)
		self.assertEqual(memloc.get_address_bytes(), b'\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78')

	def test_memloc_autosize1(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0x78)
		self.assertEqual(memloc.get_address_bytes(), b'\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78')

	def test_memloc_autosize2(self):
		memloc = MemoryLocation(address=0x1234567, memorysize=0x789abb)
		self.assertEqual(memloc.get_address_bytes(), b'\x01\x23\x45\x67')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78\x9a\xbb')

	def test_memloc_override(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0x78)
		self.assertEqual(memloc.get_address_bytes(), b'\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78')
		memloc.set_format_if_none(address_format=32)
		self.assertEqual(memloc.get_address_bytes(), b'\x00\x00\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78')
		memloc.set_format_if_none(memorysize_format=24)
		self.assertEqual(memloc.get_address_bytes(), b'\x00\x00\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x00\x00\x78')

class TestCommunicationType(UdsTest):
	def test_make(self):
		comtype = CommunicationType(subnet=CommunicationType.Subnet.node, normal_msg=True, network_management_msg=False)
		self.assertEqual(comtype.get_byte(), b'\x01')

		comtype = CommunicationType(subnet=CommunicationType.Subnet.network, normal_msg=True, network_management_msg=False)
		self.assertEqual(comtype.get_byte(), b'\xF1')

		comtype = CommunicationType(subnet=3, normal_msg=True, network_management_msg=True)
		self.assertEqual(comtype.get_byte(), b'\x33')

	def test_from_byte(self):
		comtype = CommunicationType.from_byte(b'\x01')
		self.assertEqual(comtype.get_byte(), b'\x01')

		comtype = CommunicationType.from_byte(b'\xF1')
		self.assertEqual(comtype.get_byte(), b'\xF1')

		comtype = CommunicationType.from_byte(b'\x33')
		self.assertEqual(comtype.get_byte(), b'\x33')

	def test_oob_values(self):
		with self.assertRaises(ValueError):
			CommunicationType(subnet=0, normal_msg=False, network_management_msg=False)

		with self.assertRaises(ValueError):
			CommunicationType(subnet='x', normal_msg=True, network_management_msg=False)

		with self.assertRaises(ValueError):
			CommunicationType(subnet=0, normal_msg=1, network_management_msg=True)

		with self.assertRaises(ValueError):
			CommunicationType(subnet=0, normal_msg=True, network_management_msg=1)

class TestBaudrate(UdsTest):
	def test_create_fixed(self):
		br = Baudrate(115200, baudtype=Baudrate.Type.Fixed)
		self.assertEqual(br.get_bytes(), b'\x05')

		with self.assertRaises(ValueError):
			br = Baudrate(123456, baudtype=Baudrate.Type.Fixed)

	def test_create_specific(self):
		br = Baudrate(115200, baudtype=Baudrate.Type.Specific)
		self.assertEqual(br.get_bytes(), b'\x01\xC2\x00')

		with self.assertRaises(ValueError):
			br = Baudrate(0x1000000, baudtype=Baudrate.Type.Specific)

	def test_create_id(self):
		for i in range (0xFF):
			br = Baudrate(i, baudtype=Baudrate.Type.Identifier)
			self.assertEqual(br.get_bytes(), struct.pack('B', i))

		with self.assertRaises(ValueError):
			br = Baudrate(0x100, baudtype=Baudrate.Type.Identifier)

	def test_effective_baudrate(self):
		br = Baudrate(0x12, Baudrate.Type.Identifier) # 500kbits
		self.assertEqual(br.effective_baudrate(), 500000)

	def test_change_type(self):
		br = Baudrate(115200, baudtype=Baudrate.Type.Fixed)
		br2 = br.make_new_type(Baudrate.Type.Specific)
		self.assertEqual(br2.get_bytes(), b'\x01\xC2\x00')

		br = Baudrate(115200, baudtype=Baudrate.Type.Specific)
		br2 = br.make_new_type(Baudrate.Type.Fixed)
		self.assertEqual(br2.get_bytes(), b'\x05')

	def test_create_auto(self):
		# Direct ID
		br = Baudrate(1)
		self.assertEqual(br.get_bytes(), b'\x01')
		
		br = Baudrate(0xFF)
		self.assertEqual(br.get_bytes(), b'\xFF')

		# Fixed baudrate
		br = Baudrate(115200)
		self.assertEqual(br.get_bytes(), b'\x05')

		br = Baudrate(500000)
		self.assertEqual(br.get_bytes(), b'\x12')
		
		#Specific Baudrate:
		br = Baudrate(0x123456)
		self.assertEqual(br.get_bytes(), b'\x12\x34\x56')

	def test_oob_values(self):
		with self.assertRaises(ValueError):
			br = Baudrate(-1)

		with self.assertRaises(ValueError):
			br = Baudrate(1, baudtype=-1)

		with self.assertRaises(ValueError):
			br = Baudrate(1, baudtype=0xFF)

class TestIOMasks(UdsTest):
	def test_oob_values(self):
		with self.assertRaises(ValueError):
			IOMasks(aaa='asd')

		with self.assertRaises(ValueError):
			IOMasks(1,2,3)

	def test_make_dict(self):
		m = IOMasks('aaa', 'bbb') # Correct syntax
		self.assertEqual(m.get_dict(), {'aaa' : True, 'bbb' : True})

		m = IOMasks('aaa', 'bbb', ccc=True, ddd=False) # Correct syntax
		self.assertEqual(m.get_dict(), {'aaa' : True, 'bbb' : True, 'ccc':True, 'ddd':False})

class TestDtc(UdsTest):
	def test_init(self):
		dtc = Dtc(0x1234)
		self.assertEqual(dtc.id, 0x1234 )
		self.assertEqual(dtc.status.get_byte(), b'\x00')
		self.assertEqual(dtc.status.get_byte_as_int(), 0x00)

		self.assertEqual(dtc.status.test_failed, False)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, False)
		self.assertEqual(dtc.status.pending, False)
		self.assertEqual(dtc.status.confirmed, False)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, False)
		self.assertEqual(dtc.status.test_failed_since_last_clear, False)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		with self.assertRaises(TypeError):
			Dtc()

	def test_set_status_with_byte_no_error(self):
		dtc=Dtc(1)
		for i in range(255):
			dtc.status.set_byte(i)

	def test_status_behaviour(self):
		dtc=Dtc(1)

		self.assertEqual(dtc.status.get_byte(), b'\x00')
		dtc.status.test_failed=True
		self.assertEqual(dtc.status.get_byte(), b'\x01')
		dtc.status.test_failed_this_operation_cycle = True
		self.assertEqual(dtc.status.get_byte(), b'\x03')
		dtc.status.pending = True
		self.assertEqual(dtc.status.get_byte(), b'\x07')
		dtc.status.confirmed = True
		self.assertEqual(dtc.status.get_byte(), b'\x0F')
		dtc.status.test_not_completed_since_last_clear = True
		self.assertEqual(dtc.status.get_byte(), b'\x1F')
		dtc.status.test_failed_since_last_clear = True
		self.assertEqual(dtc.status.get_byte(), b'\x3F')
		dtc.status.test_not_completed_this_operation_cycle = True
		self.assertEqual(dtc.status.get_byte(), b'\x7F')
		dtc.status.warning_indicator_requested = True
		self.assertEqual(dtc.status.get_byte(), b'\xFF')
		
		dtc.status.set_byte(0x01)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, False)
		self.assertEqual(dtc.status.pending, False)
		self.assertEqual(dtc.status.confirmed, False)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, False)
		self.assertEqual(dtc.status.test_failed_since_last_clear, False)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0x03)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, False)
		self.assertEqual(dtc.status.confirmed, False)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, False)
		self.assertEqual(dtc.status.test_failed_since_last_clear, False)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0x07)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, True)
		self.assertEqual(dtc.status.confirmed, False)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, False)
		self.assertEqual(dtc.status.test_failed_since_last_clear, False)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0x0F)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, True)
		self.assertEqual(dtc.status.confirmed, True)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, False)
		self.assertEqual(dtc.status.test_failed_since_last_clear, False)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0x1F)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, True)
		self.assertEqual(dtc.status.confirmed, True)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, True)
		self.assertEqual(dtc.status.test_failed_since_last_clear, False)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0x3F)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, True)
		self.assertEqual(dtc.status.confirmed, True)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, True)
		self.assertEqual(dtc.status.test_failed_since_last_clear, True)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, False)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0x7F)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, True)
		self.assertEqual(dtc.status.confirmed, True)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, True)
		self.assertEqual(dtc.status.test_failed_since_last_clear, True)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, True)
		self.assertEqual(dtc.status.warning_indicator_requested, False)

		dtc.status.set_byte(0xFF)
		self.assertEqual(dtc.status.test_failed, True)
		self.assertEqual(dtc.status.test_failed_this_operation_cycle, True)
		self.assertEqual(dtc.status.pending, True)
		self.assertEqual(dtc.status.confirmed, True)
		self.assertEqual(dtc.status.test_not_completed_since_last_clear, True)
		self.assertEqual(dtc.status.test_failed_since_last_clear, True)
		self.assertEqual(dtc.status.test_not_completed_this_operation_cycle, True)
		self.assertEqual(dtc.status.warning_indicator_requested, True)

	def test_severity(self):
		dtc = Dtc(1)

		dtc.severity = Dtc.Severity.NotAvailable
		dtc.severity = Dtc.Severity.MaintenanceOnly
		dtc.severity = Dtc.Severity.CheckAtNextHalt
		dtc.severity = Dtc.Severity.CheckImmediately

		with self.assertRaises(ValueError):
			dtc.severity = -1

		with self.assertRaises(ValueError):
			dtc.severity = 8










