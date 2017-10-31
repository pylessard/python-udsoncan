from udsoncan import Connection, Request, Response
from udsoncan.exceptions import *
import queue
import logging
import socket

class StubbedIsoTPSocket(object):
	conns = {}

	def __init__(self, timeout=1):
		self.bound = False
		self.interface=None
		self.rxid=None
		self.txid=None
		self.timeout = timeout

		self.queue_in = queue.Queue()	# Client reads from this queue. Other end is simulated

	def bind(self, interface, rxid, txid):
		self.interface = interface
		self.rxid = rxid
		self.txid = txid
		self.bound = True
		sockkey = (self.interface, self.rxid, self.txid)
		if sockkey not in StubbedIsoTPSocket.conns:
			StubbedIsoTPSocket.conns[sockkey] = dict()
		StubbedIsoTPSocket.conns[sockkey][id(self)] = self

	def close(self):
		self.bound=False
		sockkey = (self.interface, self.rxid, self.txid)
		if sockkey in StubbedIsoTPSocket.conns:
			if id(self) in StubbedIsoTPSocket.conns[sockkey]:
				del StubbedIsoTPSocket.conns[sockkey][id(self)]
		while not self.queue_in.empty():
			self.queue_in.get()

	def send(self, payload):
		target_sockkey = (self.interface, self.txid, self.rxid)
		if target_sockkey in StubbedIsoTPSocket.conns:
			for sockid in StubbedIsoTPSocket.conns[target_sockkey]:
				StubbedIsoTPSocket.conns[target_sockkey][sockid].queue_in.put(payload)

	def recv(self):
		try:
			payload = self.queue_in.get(block=True, timeout=self.timeout)
		except queue.Empty:
			raise socket.timeout 
		return payload

class StubbedConnection(object):
	def __init__(self):
		self.fromuserqueue = queue.Queue()	# Client reads from this queue. Other end is simulated
		self.touserqueue = queue.Queue()	# Client writes to this queue. Other end is simulated
		self.opened = False
		self.logger = logging.getLogger("StubbedConnection")

	def open(self):
		self.logger.info("Connection opened")
		self.opened = True
		return self

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def is_open(self):
		return self.opened 

	def close(self):
		self.logger.info("Connection closed")
		self.empty_rxqueue()
		self.empty_txqueue()

		self.opened = False

	def send(self, obj):
		if isinstance(obj, Request) or isinstance(obj, Response):
			payload = obj.get_payload()  
		else :
			payload = obj

		if len(payload) > 4095:
			self.logger.warning("Truncating payload to be sent to a length of 4095")
			payload = payload[0:4095]

		self.logger.info("Sending payload of %d bytes" % len(payload))
		self.logger.debug("".join(["%02x" % b for b in payload]))
		self.touserqueue.put(payload)

	def wait_frame(self, timeout=2, exception=False):
		if not self.opened:
			if exception:
				raise RuntimeException("Connection is not opened")
			else:
				return None

		timedout = False
		frame = None
		try:
			frame = self.fromuserqueue.get(block=True, timeout=timeout)
			self.logger.info("Received payload of %d bytes" % len(frame))
			self.logger.debug("".join(["%02x" % b for b in frame]))
		except queue.Empty:
			timedout = True
			
		if exception and timedout:
			raise TimeoutException("Did not received frame from user in time (timeout=%s sec)" % timeout)

		if frame is not None and len(frame) > 4095:
			self.logger.warning("Truncating received payload to a length of 4095")
			frame = frame[0:4095]

		return frame

	def empty_rxqueue(self):
		while not self.fromuserqueue.empty():
			self.fromuserqueue.get()

	def empty_txqueue(self):
		while not self.touserqueue.empty():
			self.touserqueue.get()
