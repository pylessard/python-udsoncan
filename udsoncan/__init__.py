import isotp
import threading
import queue
import inspect
import struct

class Connection(object):
	def __init__(self, interface, rxid, txid):
		self.interface=interface
		self.rxid=rxid
		self.txid=txid
		self.rxqueue = queue.Queue()
		self.exit_requested = False

		self.rxthread = threading.Thread(target=self.rxthread_task)
		self.tpsock = isotp.socket()

	def open(self):
		self.tpsock.bind(self.interface, rxid=self.rxid, txid=self.txid)

	def isOpen(self):
		return self.tpsock.bound

	def rxthread_task(self):
		while not self.exit_requested:
			try:
				self.rxqueue.put(self.tpsock.recv())
			except:
				self.exit_requested = True

	def close(self):
		self.self.exit_requested = True
		self.tpsock.close()

	def send(self, request):
		payload = request.get_payload() if isinstance(request, Request) else request
		self.tpsock.send(payload)


class Request:
	def __init__(self, service, suppressPosResponse = False):
		if not isinstance(service, services.BaseService):
			raise ValueError("Request first parameter must be either a valid UDS Service or Service Subfunction")

		self.service = service
		self.suppressPosResponse = suppressPosResponse
		self.payload = None

	def get_payload(self):
		requestid = self.service.request_id()
		subfunction = self.service.subfunction_id()
		if self.suppressPosResponse:
			subfunction |= 0x80
		payload = struct.pack("BB", requestid, subfunction) + self.service.make_payload()

		return payload
