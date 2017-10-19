import unittest
from stub import StubbedConnection
from udsoncan.client import Client
from udsoncan import services


class Testclient(unittest.TestCase):
	def setUp(self):
		conn = StubbedConnection()
		self.client = Client(conn)
		self.client.open()

	def test_ecu_reset(self):
		self.client.ecu_reset(1)
		frame = self.client.conn.touserqueue.get()
		

	def tearDown(self):
		self.client.close()