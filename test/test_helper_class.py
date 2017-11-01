from udsoncan import DataFormatIdentifier, AddressAndLengthIdentifier,MemoryLocation
from test.UdsTest import UdsTest

class TestAddressAndLengthIdentifier(UdsTest):
	def test_ali_1(self):
		ali = AddressAndLengthIdentifier(memorysize_format=8, address_format=8)
		self.assertEqual(ali.get_byte(),b'\x11')

	def test_ali_2(self):
		ali = AddressAndLengthIdentifier(memorysize_format=16, address_format=8)
		self.assertEqual(ali.get_byte(),b'\x21')

	def test_ali_oob_values(self):
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

	def test_memloc_ovverride(self):
		memloc = MemoryLocation(address=0x1234, memorysize=0x78)
		self.assertEqual(memloc.get_address_bytes(), b'\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78')
		memloc.set_format_if_none(address_format=32)
		self.assertEqual(memloc.get_address_bytes(), b'\x00\x00\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x78')
		memloc.set_format_if_none(memorysize_format=24)
		self.assertEqual(memloc.get_address_bytes(), b'\x00\x00\x12\x34')
		self.assertEqual(memloc.get_memorysize_bytes(), b'\x00\x00\x78')