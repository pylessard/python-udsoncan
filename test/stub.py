from udsoncan.exceptions import TimeoutException
from udsoncan import connections, Request, Response
import queue
import logging
import socket

class StubbedIsoTPSocket(object):
	conns = {}

	def __init__(self, name=None, timeout=1):
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


