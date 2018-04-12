from test.UdsTest import UdsTest
from test.stub import StubbedConnection
from udsoncan.exceptions import *

class TestStubbedConnection(UdsTest):

	def setUp(self):
		self.conn = StubbedConnection(name='unittest')
		self.conn.open()

	def tearDown(self):
		self.conn.close()

	def test_open(self):
		self.assertTrue(self.conn.is_open())

	def test_receive(self):
		payload = b"\x00\x01\x02\x03"
		self.conn.fromuserqueue.put(payload)
		frame = self.conn.wait_frame()
		self.assertEqual(frame, payload)

	def test_send(self):
		payload = b"\x00\x01\x02\x03"
		self.conn.send(payload)
		frame = self.conn.touserqueue.get()
		self.assertEqual(frame, payload)

	def test_truncate(self):
		payload = b"\x00\x01\x02\x03"*5000
		self.conn.send(payload)
		frame = self.conn.touserqueue.get()
		self.assertEqual(len(frame), 4095)
		self.assertEqual(frame, payload[0:4095])

		self.conn.fromuserqueue.put(payload)
		frame = self.conn.wait_frame()

		self.assertEqual(len(frame), 4095)
		self.assertEqual(frame, payload[0:4095])

	def test_reopen(self):
		payload = b"\x00\x01\x02\x03"
		self.conn.send(payload)
		self.conn.fromuserqueue.put(payload)

		self.conn.close()
		self.conn.open()
		
		with self.assertRaises(TimeoutException):
			frame = self.conn.wait_frame(timeout=0.05, exception=True)

		self.assertTrue(self.conn.touserqueue.empty())