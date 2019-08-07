from test.UdsTest import UdsTest
from udsoncan.connections import *
from test.stub import StubbedIsoTPSocket
import socket
import threading
import time
import unittest

try:
    _STACK_UNVAILABLE_REASON = ''
    _interface_name = 'vcan0'
    import isotp
    import can
    s = isotp.socket()
    s.bind(_interface_name,rxid=1,txid=2)
    s.close()
    _STACK_POSSIBLE = True
except Exception as e:
    _STACK_UNVAILABLE_REASON = str(e)
    _STACK_POSSIBLE = False

class TestIsoTPSocketConnection(UdsTest):

    def setUp(self):
        self.tpsock1 = StubbedIsoTPSocket(timeout=0.1)
        self.tpsock2 = StubbedIsoTPSocket(timeout=0.1)

    def test_open(self):
        conn = IsoTPSocketConnection(interface='vcan0', rxid=0x001, txid=0x002, tpsock=self.tpsock1, name='unittest')
        self.assertFalse(conn.is_open())
        conn.open()
        self.assertTrue(conn.is_open())
        conn.close()
        self.assertFalse(conn.is_open())

    def test_transmit(self):
        conn1 = IsoTPSocketConnection(interface='vcan0', rxid=0x100, txid=0x101, tpsock=self.tpsock1, name='unittest')
        conn2 = IsoTPSocketConnection(interface='vcan0', rxid=0x101, txid=0x100, tpsock=self.tpsock2, name='unittest')

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
            self.conn.wait_frame(timeout=0.05, exception=True)

        self.assertTrue(self.conn.touserqueue.empty())

@unittest.skipIf(_STACK_POSSIBLE == False, 'Cannot test TestPythonIsoTpConnection. %s' % _STACK_UNVAILABLE_REASON)
class TestPythonIsoTpConnection(UdsTest):
    def __init__(self, *args, **kwargs):
        UdsTest.__init__(self, *args, **kwargs)
        if not hasattr(self.__class__, '_next_id'):
            self.__class__._next_id=1

        self.stack_txid = self.__class__._next_id
        self.stack_rxid = self.__class__._next_id +1
        self.__class__._next_id += 2

    def make_bus(self):
        return can.interface.Bus(bustype='socketcan', channel='vcan0', bitrate=500000, receive_own_messages=True)

    def setUp(self):
        self.vcan0_bus = self.make_bus()
        addr = isotp.Address(isotp.AddressingMode.Normal_11bits, rxid=self.stack_rxid, txid=self.stack_txid)
        self.conn = PythonIsoTpConnection(isotp.CanStack(bus=self.vcan0_bus, address=addr), name='unittest')
        self.conn.open()

    def test_open(self):
        self.assertTrue(self.conn.is_open())

    def test_receive(self):
        self.vcan0_bus.send(can.Message(arbitration_id = self.stack_rxid, data =  b"\x03\x01\x02\x03", extended_id = False))
        frame = self.conn.wait_frame(timeout=1)
        self.assertEqual(frame, b"\x01\x02\x03")

    def test_send(self):
        self.conn.send(b"\xAA\xBB\xCC\xDD\xEE\xFF")
        t1 = time.time()
        msg = self.vcan0_bus.recv(1)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.data, b'\x06\xAA\xBB\xCC\xDD\xEE\xFF')

    def test_reopen(self):
        self.conn.send(b"\x0A\x0B\x0C\x0D")
        self.vcan0_bus.send(can.Message(arbitration_id = self.stack_rxid, data =  b"\x03\x01\x02\x03", extended_id = False))
        self.conn.close()
        self.vcan0_bus.shutdown()
        self.vcan0_bus = self.make_bus()
        self.conn.open(bus=self.vcan0_bus)

        with self.assertRaises(TimeoutException):
            self.conn.wait_frame(timeout=0.05, exception=True)

        self.assertIsNone(self.vcan0_bus.recv(0))

    def tearDown(self):
        self.conn.close()
        self.vcan0_bus.shutdown()
