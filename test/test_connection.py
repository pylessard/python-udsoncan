from test.UdsTest import UdsTest
from udsoncan.connections import *
from test.stub import StubbedIsoTPSocket
import socket
import threading
import time

class TestIsoTPConnection(UdsTest):

	def setUp(self):
		self.tpsock1 = StubbedIsoTPSocket(timeout=0.1)
		self.tpsock2 = StubbedIsoTPSocket(timeout=0.1)

	def test_open(self):
		conn = IsoTPConnection(interface='vcan0', rxid=0x001, txid=0x002, tpsock=self.tpsock1, name='unittest')
		self.assertFalse(conn.is_open())
		conn.open()
		self.assertTrue(conn.is_open())
		conn.close()
		self.assertFalse(conn.is_open())

	def test_transmit(self):
		conn1 = IsoTPConnection(interface='vcan0', rxid=0x100, txid=0x101, tpsock=self.tpsock1, name='unittest')
		conn2 = IsoTPConnection(interface='vcan0', rxid=0x101, txid=0x100, tpsock=self.tpsock2, name='unittest')
		
		with conn1.open():
			with conn2.open():
				payload1 = b"\x00\x01\x02\x03\x04"
				conn1.send(payload1)
				payload2 = conn2.wait_frame(timeout=0.3)
				self.assertEqual(payload1, payload2)

class TestSocketConnection(UdsTest):
	def server_sock_thread_task(self):
		self.thread_started=True
		self.sock1, addr = self.server_sock.accept()

	def setUp(self):
		self.thread_started = False
		self.server_sock_thread = threading.Thread(target=self.server_sock_thread_task)

		self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_sock.setblocking(False)
		self.sock1 = None
		self.sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

		self.server_sock.settimeout(0.5)

		self.server_sock.bind(('127.0.0.1', 0))
		self.server_sock.listen(1)
		self.server_sock_thread.start()

		t1 = time.time()
		while not self.thread_started:
			if (time.time() - t1) > 0.5:
				raise RuntimeError('Timeout while connecting sockets together.')
			time.sleep(0.01)
		time.sleep(0.01)

		self.sock2.connect(self.server_sock.getsockname())
		t1 = time.time()
		while self.sock1 is None:
			if (time.time() - t1) > 0.5:
				raise RuntimeError('Timeout while connecting sockets together.')

	def tearDown(self):
		if isinstance(self.sock1, socket.socket):
			self.sock1.close()
		
		if isinstance(self.sock2, socket.socket):
			self.sock2.close()

		if isinstance(self.server_sock, socket.socket):
			self.server_sock.close()
		
	def test_open(self):
		conn = SocketConnection(self.sock1, name='unittest')
		self.assertFalse(conn.is_open())
		conn.open()
		self.assertTrue(conn.is_open())
		conn.close()
		self.assertFalse(conn.is_open())

	def test_transmit(self):
		conn1 = SocketConnection(self.sock1, name='unittest')
		conn2 = SocketConnection(self.sock2, name='unittest')
		
		with conn1.open():
			with conn2.open():
				payload1 = b"\x00\x01\x02\x03\x04"
				conn1.send(payload1)
				payload2 = conn2.wait_frame(timeout=1, exception=True)
				self.assertEqual(payload1, payload2)


class TestQueueConnection(UdsTest):
	def setUp(self):
		self.conn = QueueConnection(name='unittest')
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