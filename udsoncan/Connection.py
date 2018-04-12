import socket
import queue
import threading
import logging
import binascii
from abc import ABC, abstractmethod

from udsoncan.Request import Request
from udsoncan.Response import Response
from udsoncan.exceptions import TimeoutException

class BaseConnection(ABC):

	def __init__(self, name=None):
		if name is None:
			name = 'Connection'
		else:
			name = 'Connection[%s]' % (name)

		self.logger = logging.getLogger(name)

	def send(self, obj):
		if isinstance(obj, Request) or isinstance(obj, Response):
			payload = obj.get_payload()  
		else :
			payload = obj

		if self.logger.getEffectiveLevel() >= logging.DEBUG:
			self.logger.debug('Sending %d bytes : [%s]' % (len(payload), binascii.hexlify(payload) ))
		else:
			self.logger.info('Sending %d bytes' % ( len(payload) ))

		self.specific_send(payload)

	def wait_frame(self, timeout=2, exception=False):
		frame = self.specific_wait_frame(timeout=timeout, exception=exception)
		if frame is not None:
			if self.logger.getEffectiveLevel() >= logging.DEBUG:
				self.logger.debug('Received %d bytes : [%s]' % (len(frame), binascii.hexlify(frame) ))
			else:
				self.logger.info('Received %d bytes' % ( len(frame) ))
		return frame
	
	@abstractmethod
	def specific_send(self, payload):
		pass

	@abstractmethod
	def specific_wait_frame(self, timeout=2, exception=False):
		pass


class SocketConnection(BaseConnection):
	def __init__(self, sock, bufsize=4095, name=None):

		BaseConnection.__init__(self, name)

		self.rxqueue = queue.Queue()
		self.exit_requested = False
		self.opened = False
		self.rxthread = threading.Thread(target=self.rxthread_task)
		self.sock = sock
		self.sock.settimeout(0.1)	# for recv
		self.bufsize=bufsize


	def open(self):
		self.exit_requested = False
		self.rxthread.start()
		self.opened = True
		return self

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def is_open(self):
		return self.opened

	def rxthread_task(self):
		while not self.exit_requested:
			try:
				data = self.sock.recv(self.bufsize)
				if data is not None:
					self.rxqueue.put(data)
			except socket.timeout:
				pass
			except Exception:
				self.exit_requested = True


	def close(self):
		self.exit_requested = True
		self.opened = False

	def specific_send(self, payload):
		self.sock.send(payload)

	def specific_wait_frame(self, timeout=2, exception=False):
		if not self.opened:
			if exception:
				raise RuntimeError("Connection is not opened")
			else:
				return None

		timedout = False
		frame = None
		try:
			frame = self.rxqueue.get(block=True, timeout=timeout)

		except queue.Empty:
			timedout = True
			
		if exception and timedout:
			raise TimeoutException("Did not received frame in time (timeout=%s sec)" % timeout)

		return frame

	def empty_rxqueue(self):
		while not self.rxqueue.empty():
			self.rxqueue.get()

class IsoTPConnection(BaseConnection):
	def __init__(self, interface, rxid, txid, name=None, tpsock=None):
		import isotp
		BaseConnection.__init__(self, name)

		self.interface=interface
		self.rxid=rxid
		self.txid=txid
		self.rxqueue = queue.Queue()
		self.exit_requested = False
		self.opened = False

		self.rxthread = threading.Thread(target=self.rxthread_task)
		self.tpsock = isotp.socket(timeout=0.1) if tpsock is None else tpsock


	def open(self):
		self.tpsock.bind(self.interface, rxid=self.rxid, txid=self.txid)
		self.exit_requested = False
		self.rxthread.start()
		self.opened = True
		return self

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def is_open(self):
		return self.tpsock.bound

	def rxthread_task(self):
		while not self.exit_requested:
			try:
				data = self.tpsock.recv()
				if data is not None:
					self.rxqueue.put(data)
			except socket.timeout:
				pass
			except Exception:
				self.exit_requested = True


	def close(self):
		self.exit_requested = True
		self.tpsock.close()
		self.opened = False

	def specific_send(self, payload):
		self.tpsock.send(payload)

	def specific_wait_frame(self, timeout=2, exception=False):
		if not self.opened:
			if exception:
				raise RuntimeError("Connection is not opened")
			else:
				return None

		timedout = False
		frame = None
		try:
			frame = self.rxqueue.get(block=True, timeout=timeout)

		except queue.Empty:
			timedout = True
			
		if exception and timedout:
			raise TimeoutException("Did not received ISOTP frame in time (timeout=%s sec)" % timeout)

		return frame

	def empty_rxqueue(self):
		while not self.rxqueue.empty():
			self.rxqueue.get()