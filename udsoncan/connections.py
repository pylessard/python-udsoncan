import socket
import queue
import threading
import logging
import binascii
from abc import ABC, abstractmethod

try:
	import ics
except ImportError as ie:
	logging.getLogger(__name__).warning(
		"You won't be able to use the ICS NeoVi can backend without the "
		"python-ics module installed!: %s", ie
	)
	ics = None

from udsoncan.Request import Request
from udsoncan.Response import Response
from udsoncan.exceptions import TimeoutException

class BaseConnection(ABC):

	def __init__(self, name=None):
		if name is None:
			self.name = 'Connection'
		else:
			self.name = 'Connection[%s]' % (name)

		self.logger = logging.getLogger(self.name)

	def send(self, data):
		"""Sends data to the underlying transport protocol

		:param data: The data or object to send. If a Request or Response is given, the value returned by get_payload() will be sent.
		:type data: bytes, Request, Response

		:returns: None
		"""

		if isinstance(data, Request) or isinstance(data, Response):
			payload = data.get_payload()  
		else :
			payload = data

		self.logger.debug('Sending %d bytes : [%s]' % (len(payload), binascii.hexlify(payload) ))
		self.specific_send(payload)

	def wait_frame(self, timeout=2, exception=False):
		"""Waits for the reception of a frame of data from the underlying transport protocol

		:param timeout: The maximum amount of time to wait before giving up in seconds
		:type timeout: int
		:param exception: Boolean value indicating if this function may return exceptions.
			When ``True``, all exceptions may be raised, including ``TimeoutException``
			When ``False``, all exceptions will be logged as ``DEBUG`` and ``None`` will be returned.
		:type exception: bool

		:returns: Received data
		:rtype: bytes or None
		"""
		try:
			frame = self.specific_wait_frame(timeout=timeout)
		except Exception as e:
			self.logger.debug('No data received: [%s] - %s ' % (e.__class__.__name__, str(e)))

			if exception == True:
				raise
			else:
				frame = None

		if frame is not None:
			self.logger.debug('Received %d bytes : [%s]' % (len(frame), binascii.hexlify(frame) ))
		return frame
	
	def __enter__(self):
		return self

	@abstractmethod
	def specific_send(self, payload):
		"""The implementation of the send method.

		:param payload: Data to send
		:type payload: bytes
		
		:returns: None
		"""
		pass

	@abstractmethod
	def specific_wait_frame(self, timeout=2):
		"""The implementation of the ``wait_frame`` method. 

		:param timeout: The maximum amount of time to wait before giving up
		:type timeout: int
		
		:returns: Received data
		:rtype: bytes or None
		"""
		pass

	@abstractmethod
	def open(self):
		""" Set up the connection object. 

		:returns: None
		"""
		pass

	@abstractmethod
	def close(self):
		""" Close the connection object
		
		:returns: None
		"""
		pass	

	@abstractmethod
	def empty_rxqueue(self):
		""" Empty all unread data in the reception buffer.
		
		:returns: None
		"""
		pass
	
	def __exit__(self, type, value, traceback):
		pass


class SocketConnection(BaseConnection):
	"""
	Sends and receives data through a socket.

	:param sock: The socket to use. This socket must be bound and ready to use. Only ``send()`` and ``recv()`` will be called by this Connection
	:type sock: socket.socket
	:param bufsize: Maximum buffer size of the socket, this value is passed to ``recv()``
	:type bufsize: int
	:param name: This name is included in the logger name so that its output can be redirected. The logger name will be ``Connection[<name>]``
	:type name: string

	"""
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
		self.logger.info('Connection opened')
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
		self.logger.info('Connection closed')

	def specific_send(self, payload):
		self.sock.send(payload)

	def specific_wait_frame(self, timeout=2):
		if not self.opened:
			raise RuntimeError("Connection is not open")

		timedout = False
		frame = None
		try:
			frame = self.rxqueue.get(block=True, timeout=timeout)

		except queue.Empty:
			timedout = True
			
		if timedout:
			raise TimeoutException("Did not received frame in time (timeout=%s sec)" % timeout)

		return frame

	def empty_rxqueue(self):
		while not self.rxqueue.empty():
			self.rxqueue.get()


class IsoTPConnection(BaseConnection):
	"""
	Sends and receives data through an ISO-TP socket. Makes cleaner code than SocketConnection but offers no additional functionality.
	The `isotp module <https://github.com/pylessard/python-can-isotp>`_ must be installed in order to use this connection

	:param interface: The can interface to use (example: `can0`)
	:type interface: string
	:param rxid: The reception CAN id
	:type rxid: int 
	:param txid: The transmission CAN id
	:type txid: int
	:param name: This name is included in the logger name so that its output can be redirected. The logger name will be ``Connection[<name>]``
	:type name: string
	:param tpsock: An optional ISO-TP socket to use instead of creating one.
	:type tpsock: isotp.socket

	"""
	def __init__(self, interface, rxid, txid, name=None, tpsock=None):
		
		BaseConnection.__init__(self, name)

		self.interface=interface
		self.rxid=rxid
		self.txid=txid
		self.rxqueue = queue.Queue()
		self.exit_requested = False
		self.opened = False

		self.rxthread = threading.Thread(target=self.rxthread_task)
		if tpsock is None:
			import isotp
			self.tpsock = isotp.socket(timeout=0.1)
		else:
			self.tpsock = tpsock


	def open(self):
		self.tpsock.bind(self.interface, rxid=self.rxid, txid=self.txid)
		self.exit_requested = False
		self.rxthread.start()
		self.opened = True
		self.logger.info('Connection opened')
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
		self.logger.info('Connection closed')

	def specific_send(self, payload):
		self.tpsock.send(payload)

	def specific_wait_frame(self, timeout=2):
		if not self.opened:
			raise RuntimeError("Connection is not open")

		timedout = False
		frame = None
		try:
			frame = self.rxqueue.get(block=True, timeout=timeout)

		except queue.Empty:
			timedout = True
			
		if timedout:
			raise TimeoutException("Did not received ISOTP frame in time (timeout=%s sec)" % timeout)

		return frame

	def empty_rxqueue(self):
		while not self.rxqueue.empty():
			self.rxqueue.get()


class IcsNeoVIConnection(BaseConnection):
	"""
	Sends and receives data through an Intrepid control systems interface.
	The `python-ics module <https://github.com/intrepidcs/python-ics>`_ must be installed in order to use this connection

	:param serial: The can interface serial number to connect to (example: `171423`)
	:type serial: string
	:param rxid: The reception CAN id
	:type rxid: int 
	:param txid: The transmission CAN id
	:type txid: int
	:param name: This name is included in the logger name so that its output can be redirected. The logger name will be ``Connection[<name>]``
	:type name: string
	:param is_fd: True if this connection will be using CANFD (high data rate)
	:type is_fd: bool

	"""
	def __init__(self, serial, rxid, txid, name=None,
				 padding=0x00, st_min=100, block_size=100, is_canfd=False):
		if ics is None:
			raise ImportError('Please install python-ics')

		BaseConnection.__init__(self, name)

		self.serial=serial
		self.rxid=rxid
		self.txid=txid
		self.padding = padding
		self.st_min = st_min
		self.block_size = block_size
		self.is_canfd = is_canfd
		self.rxqueue = queue.Queue()
		self.exit_requested = False
		self.opened = False
		self.device = None

		self.rxthread = threading.Thread(target=self.rxthread_task)


	def open(self):
		device_list = ics.find_devices()
		self.device = next( (dev for dev in device_list if dev.SerialNumber == self.serial), device_list[0])

		ics.open_device(self.device)
		ics.iso15765_enable_networks(self.device, ics.NETID_HSCAN)
		self.exit_requested = False
		self.rxthread.start()
		self.opened = True
		self.logger.info('Connection opened')
		return self

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def is_open(self):
		return self.opened

	def rxthread_task(self):
		# First, configure rx flow control
		msg = ics.CmISO157652RxMessage()
		msg.vs_netid = ics.NETID_HSCAN
		msg.id = self.rxid
		msg.id_mask = 0xFFF
		msg.padding = self.padding
		msg.fc_id = self.txid
		msg.stMin = self.st_min
		msg.cf_timeout = 1000
		msg.blockSize = self.block_size
		msg.flags = 0
		# enableFlowControlTransmission = 1
		msg.flags |= (1 << 4)
		# paddingEnable
		msg.flags |= (1 << 5)
		# CANFD: Enable + BRS
		if self.is_canfd:
			msg.flags |= (1 << 6) | (1 << 7)
		# This is not a real RX, it just sets up the ISO stack
		ret = ics.iso15765_receive_message(self.device, msg.vs_netid, msg)
		deframing_state = 'idle'
		deframing_bytes_to_go = 0
		reconstructed_message = []
		while not self.exit_requested:
			try:
				msgs, errors = ics.get_messages(self.device)
				filtered_msgs = [msg for msg in msgs if msg.ArbIDOrHeader == self.rxid]
				self.logger.debug("Got {} messages, {} matched filter of {}".format(len(msgs), len(filtered_msgs), self.rxid))
				for msg in filtered_msgs:
					if deframing_state == 'idle':
						if msg.Data[0] & 0xF0 == 0x10:
							deframing_state = 'ff_rcvd'
							data_as_bytes = bytearray(msg.Data)
							deframing_bytes_to_go = data_as_bytes[1]
							payload_data = data_as_bytes[2:]
							reconstructed_message = payload_data
							deframing_bytes_to_go -= len(payload_data)
						else:
							data_as_bytes = bytearray(msg.Data)
							msg_len = data_as_bytes[0]
							payload_data = data_as_bytes[1:msg_len+1]
							self.rxqueue.put(payload_data)


					if deframing_state == 'ff_rcvd':
						if msg.Data[0] & 0xF0 == 0x20:
							data_as_bytes = bytearray(msg.Data)
							sequence_number = data_as_bytes[0] & 0x0F
							payload_data = data_as_bytes[1:min(deframing_bytes_to_go, 7)+1]
							reconstructed_message.extend(payload_data)
							deframing_bytes_to_go -= len(payload_data)
							if deframing_bytes_to_go <= 0:
								self.rxqueue.put(reconstructed_message)
								deframing_state = 'idle'

			except ics.RuntimeError as e:
				self.logger.debug("ics.RuntimeError while processing rx data")
				self.exit_requested = True
		ics.iso15765_disable_networks(self.device)


	def close(self):
		self.exit_requested = True
		ics.close_device(self.device)
		self.opened = False
		self.logger.info('Connection closed')

	def specific_send(self, payload):
		msg = ics.CmISO157652TxMessage()
		msg.vs_netid = ics.NETID_HSCAN
		msg.id = self.txid
		# This is a hack. We should also paramaterize these timeouts and paddings
		msg.fc_id = self.rxid
		msg.fs_timeout = 100
		msg.fs_wait = 2000
		msg.flags = 0
		# paddingEnable
		msg.flags |= (1 << 5)
		# CANFD: Enable + BRS
		if self.is_canfd:
			msg.flags |= (1 << 6) | (1 << 7)
		# tx_dl
		msg.flags |= (8 << 23)

		msg.data = list(payload)
		msg.num_bytes = len(payload)
		msg.padding = self.padding
		ics.iso15765_transmit_message(self.device, msg.vs_netid, msg, 1000)

	def specific_wait_frame(self, timeout=2):
		if not self.opened:
			raise RuntimeError("Connection is not open")

		timedout = False
		frame = None
		try:
			frame = self.rxqueue.get(block=True, timeout=timeout)

		except queue.Empty:
			timedout = True
			
		if timedout:
			raise TimeoutException("Did not received ISOTP frame in time (timeout=%s sec)" % timeout)

		return frame

	def empty_rxqueue(self):
		while not self.rxqueue.empty():
			self.rxqueue.get()


class QueueConnection(BaseConnection):
	"""
	Sends and receives data using 2 Python native queues.

	- ``MyConnection.fromuserqueue`` : Data read from this queue when ``wait_frame`` is called
	- ``MyConnection.touserqueue`` : Data written to this queue when ``send`` is called

	:param mtu: Optional maximum frame size. Messages will be truncated to this size
	:type mtu: int
	:param name: This name is included in the logger name so that its output can be redirected. The logger name will be ``Connection[<name>]``
	:type name: string

	"""
	def __init__(self, name=None, mtu=4095):
		BaseConnection.__init__(self, name)

		self.fromuserqueue = queue.Queue()	# Client reads from this queue. Other end is simulated
		self.touserqueue = queue.Queue()	# Client writes to this queue. Other end is simulated
		self.opened = False
		self.mtu = mtu

	def open(self):
		self.opened = True
		self.logger.info('Connection opened')
		return self

	def __enter__(self):
		return self

	def __exit__(self, type, value, traceback):
		self.close()

	def is_open(self):
		return self.opened 

	def close(self):
		self.empty_rxqueue()
		self.empty_txqueue()
		self.opened = False
		self.logger.info('Connection closed')	

	def specific_send(self, payload):
		if self.mtu is not None:
			if len(payload) > self.mtu:
				self.logger.warning("Truncating payload to be set to a length of %d" % (self.mtu))
				payload = payload[0:self.mtu]

		self.touserqueue.put(payload)

	def specific_wait_frame(self, timeout=2):
		if not self.opened:
			raise RuntimeException("Connection is not open")

		timedout = False
		frame = None
		try:
			frame = self.fromuserqueue.get(block=True, timeout=timeout)
		except queue.Empty:
			timedout = True
			
		if timedout:
			raise TimeoutException("Did not receive frame from user queue in time (timeout=%s sec)" % timeout)
		
		if self.mtu is not None:
			if frame is not None and len(frame) > self.mtu:
				self.logger.warning("Truncating received payload to a length of %d" % (self.mtu))
				frame = frame[0:self.mtu]

		return frame

	def empty_rxqueue(self):
		while not self.fromuserqueue.empty():
			self.fromuserqueue.get()

	def empty_txqueue(self):
		while not self.touserqueue.empty():
			self.touserqueue.get()

