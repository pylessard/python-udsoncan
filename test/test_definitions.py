from udsoncan import DataIdentifier, Routine, Units
from test.UdsTest import UdsTest

class TestDefinitions(UdsTest):
	def test_data_identifier_name_from_id(self):
		for i in range(0x10000):
			name = DataIdentifier.name_from_id(i)
			self.assertTrue(isinstance(name, str))
	
	def test_routine_name_from_id(self):
		for i in range(0x10000):
			name = Routine.name_from_id(i)
			self.assertTrue(isinstance(name, str))
		