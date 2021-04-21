import socket
import queue
import threading
import logging
import binascii
import sys
from abc import ABC, abstractmethod
import functools
import time

try:
    import can
    _import_can_err = None
except Exception as e:
    _import_can_err = e

try:
    import isotp
    _import_isotp_err = None
except Exception as e:
    _import_isotp_err = e

try:
    from udsoncan.j2534 import J2534
    from udsoncan.j2534 import Protocol_ID
    _import_j2534_err = None
except Exception as e:
    _import_j2534_err = e



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
        self.rxthread = None
        self.sock = sock
        self.sock.settimeout(0.1)	# for recv
        self.bufsize=bufsize


    def open(self):
        self.exit_requested = False
        self.rxthread = threading.Thread(target=self.rxthread_task)
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
        self.rxthread.join()
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



class IsoTPSocketConnection(BaseConnection):
    """
    Sends and receives data through an ISO-TP socket. Makes cleaner code than SocketConnection but offers no additional functionality.
    The `can-isotp module <https://github.com/pylessard/python-can-isotp>`_ must be installed in order to use this connection

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
    :param args: Optional parameters list passed to ISO-TP socket binding method.
    :type args: list
    :param kwargs: Optional parameters dictionary passed to ISO-TP socket binding method.
    :type kwargs: dict

    """
    def __init__(self, interface, rxid, txid, name=None, tpsock=None, *args, **kwargs):

        BaseConnection.__init__(self, name)

        self.interface=interface
        self.rxid=rxid
        self.txid=txid
        self.rxqueue = queue.Queue()
        self.exit_requested = False
        self.opened = False
        self.tpsock_bind_args = args
        self.tpsock_bind_kwargs = kwargs

        if tpsock is None:
            if 'isotp' not in sys.modules:
                if _import_isotp_err is None:
                    raise ImportError('isotp module is not loaded')
                else:
                    raise _import_isotp_err
            self.tpsock = isotp.socket(timeout=0.1)
        else:
            self.tpsock = tpsock


    def open(self):
        self.tpsock.bind(self.interface, rxid=self.rxid, txid=self.txid, *self.tpsock_bind_args, **self.tpsock_bind_kwargs)
        self.exit_requested = False
        self.rxthread = threading.Thread(target=self.rxthread_task)
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
        self.rxthread.join()
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


class IsoTPConnection(IsoTPSocketConnection):
    """
    Same as :class:`IsoTPSocketConnection <udsoncan.connections.IsoTPSocketConnection.Session>`. Exists only for backward compatibility. 
    """
    pass

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
            raise RuntimeError("Connection is not open")

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


class PythonIsoTpConnection(BaseConnection):
    """
    Sends and receives data using a `can-isotp <https://github.com/pylessard/python-can-isotp>`_ Python module which is a Python implementation of the IsoTp transport protocol
    which can be coupled with `python-can <https://python-can.readthedocs.io>`_ module to interract with CAN hardware

    `can-isotp <https://github.com/pylessard/python-can-isotp>`_ must be installed in order to use this connection.

    See an :ref:`example<example_using_python_can>`

    :param isotp_layer: The IsoTP Transport layer object coming from the ``isotp`` module.
    :type isotp_layer: :class:`isotp.TransportLayer<isotp.TransportLayer>`

    :param name: This name is included in the logger name so that its output can be redirected. The logger name will be ``Connection[<name>]``
    :type name: string

    """
    mtu = 4095

    def __init__(self, isotp_layer, name=None):
        BaseConnection.__init__(self, name)
        self.toIsoTPQueue = queue.Queue()
        self.fromIsoTPQueue = queue.Queue()	
        self.rxthread = None
        self.exit_requested = False
        self.opened = False
        self.isotp_layer = isotp_layer

        assert isinstance(self.isotp_layer, isotp.TransportLayer) , 'isotp_layer must be a valid isotp.TransportLayer '

    def open(self, bus=None):
        if bus is not None:
            self.isotp_layer.set_bus(bus)

        self.exit_requested = False
        self.rxthread = threading.Thread(target=self.rxthread_task)
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

    def close(self):
        self.empty_rxqueue()
        self.empty_txqueue()
        self.exit_requested=True
        self.rxthread.join()
        self.isotp_layer.reset()
        self.opened = False
        self.logger.info('Connection closed')	

    def specific_send(self, payload):
        if self.mtu is not None:
            if len(payload) > self.mtu:
                self.logger.warning("Truncating payload to be set to a length of %d" % (self.mtu))
                payload = payload[0:self.mtu]

        self.toIsoTPQueue.put(bytearray(payload)) # isotp.protocol.TransportLayer uses byte array. udsoncan is strict on bytes format

    def specific_wait_frame(self, timeout=2):
        if not self.opened:
            raise RuntimeError("Connection is not open")

        timedout = False
        frame = None
        try:
            frame = self.fromIsoTPQueue.get(block=True, timeout=timeout)
        except queue.Empty:
            timedout = True

        if timedout:
            raise TimeoutException("Did not receive frame IsoTP Transport layer in time (timeout=%s sec)" % timeout)

        if self.mtu is not None:
            if frame is not None and len(frame) > self.mtu:
                self.logger.warning("Truncating received payload to a length of %d" % (self.mtu))
                frame = frame[0:self.mtu]

        return bytes(frame)	# isotp.protocol.TransportLayer uses bytearray. udsoncan is strict on bytes format

    def empty_rxqueue(self):
        while not self.fromIsoTPQueue.empty():
            self.fromIsoTPQueue.get()

    def empty_txqueue(self):
        while not self.toIsoTPQueue.empty():
            self.toIsoTPQueue.get()			

    def rxthread_task(self):
        while not self.exit_requested:
            try:
                while not self.toIsoTPQueue.empty():
                    self.isotp_layer.send(self.toIsoTPQueue.get())

                self.isotp_layer.process()

                while self.isotp_layer.available():
                    self.fromIsoTPQueue.put(self.isotp_layer.recv())

                time.sleep(self.isotp_layer.sleep_time())

            except Exception as e:
                self.exit_requested = True
                self.logger.error(str(e))

class J2534Connection(BaseConnection):
    """
    Sends and receives data through a J2534 Interface. 
    A windows DLL and a J2534 interface must be installed in order to use this connection

    :param windll: The path to the windows DLL for the J2534 interface (example: 'C:/Program Files{x86}../../openport 2.0/op20pt32.dll')
    :type interface: string
    :param rxid: The reception CAN id
    :type rxid: int 
    :param txid: The transmission CAN id
    :type txid: int
    :param name: This name is included in the logger name so that its output can be redirected. The logger name will be ``Connection[<name>]``
    :type name: string
    :param debug: This will enable windows debugging mode in the dll (see tactrix doc for additional information)
    :type debug: boolean
    :param args: Optional parameters list (Unused right now).
    :type args: list
    :param kwargs: Optional parameters dictionary Unused right now).
    :type kwargs: dict

    """
    def __init__(self, windll, rxid, txid, name=None, debug = False, *args, **kwargs):

        BaseConnection.__init__(self, name)

        #Set up a J2534 interface using the DLL provided
        self.interface = J2534(windll = windll, rxid = rxid, txid = txid)

        #Set the protocol to ISO15765, Baud rate to 500000
        self.protocol = Protocol_ID.ISO15765
        self.baudrate = 500000

        #Open the interface (connect to the DLL)
        result, self.devID = self.interface.PassThruOpen()

        if debug:
            result = self.interface.PassThruIoctl(Handle = 0,IoctlID = Ioctl_Flags.TX_IOCTL_SET_DLL_DEBUG_FLAGS, ioctlInput = Ioctl_Flags.TX_IOCTL_DLL_DEBUG_FLAG_J2534_CALLS)

        #Get the firmeware and DLL version etc, mainly for debugging output
        self.result, self.firmwareVersion, self.dllVersion, self.apiVersion = self.interface.PassThruReadVersion(self.devID)
        self.logger.info("J2534 FirmwareVersion: " + str(self.firmwareVersion.value) + ", dllVersoin: " + str(self.dllVersion.value) + ", apiVersion" + str(self.apiVersion.value))

        #get the channel ID of the interface (used for subsequent communication)
        self.result, self.channelID = self.interface.PassThruConnect(self.devID, self.protocol.value, self.baudrate)

        #Set the filters and clear the read buffer (filters will be set based on tx/rxids)
        self.result = self.interface.PassThruStartMsgFilter(self.channelID, self.protocol.value)
        self.result = self.interface.PassThruIoctl(self.channelID, Ioctl_ID.CLEAR_RX_BUFFER)


        self.rxqueue = queue.Queue()
        self.exit_requested = False
        self.opened = False

    def open(self):
        self.exit_requested = False
        self.rxthread = threading.Thread(target=self.rxthread_task)
        self.rxthread.daemon = True
        self.rxthread.start()
        self.opened = True
        self.logger.info('J2534 Connection opened')
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
                result, data, numMessages = self.interface.PassThruReadMsgs(self.channelID, self.protocol.value, 1, 1)
                
                if data is not None:
                    self.rxqueue.put(data)
            except Exception:
                self.logger.critical("Exiting J2534 rx thread")
                self.exit_requested = True


    def close(self):
        self.exit_requested = True
        self.rxthread.join()
        result = self.interface.PassThruDisconnect(self.channelID)
        self.opened = False
        self.logger.info('J2534 Connection closed')

    def specific_send(self, payload):
        result = self.interface.PassThruWriteMsgs(self.channelID, payload, self.protocol.value)

    def specific_wait_frame(self, timeout=4):
        if not self.opened:
            raise RuntimeError("J2534 Connection is not open")

        timedout = False
        frame = None
        try:
            frame = self.rxqueue.get(block=True, timeout=timeout)

        except queue.Empty:
            timedout = True

        if timedout:
            raise TimeoutException("Did not received response from J2534 RxQueue (timeout=%s sec)" % timeout)

        return frame

    def empty_rxqueue(self):
        while not self.rxqueue.empty():
            self.rxqueue.get()

class FakeConnection(BaseConnection):
    """
    Sends and receives STATIC data defined in a local dict. 
    Used so that an application can be tested without a live can network
    """
    def __init__(self, name=None, debug = False, *args, **kwargs):

        BaseConnection.__init__(self, name)

        self.rxqueue = queue.Queue()
        
        self.exit_requested = False
        self.opened = False

        self.ResponseData = {b'\x10\x03': b'\x50\x03\x12\x23\x34\x45',
                b'\x22\xf1\x90\xf1\x89\xf1\x91\xf8\x06\xf1\xa3': b'\x22\xf1\x90\xf1\x89\xf1\x91\xf8\x06\xf1\xa3'}


    def open(self):
        self.opened = True
        self.logger.info('Fake Connection opened')
        return self

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def is_open(self):
        return self.opened

    def close(self):
        self.exit_requested = True
        self.opened = False
        self.logger.info('Fake Connection closed')

    def specific_send(self, payload):
        self.rxqueue.put(self.ResponseData[payload])

    def specific_wait_frame(self, timeout=4):
        if not self.opened:
            raise RuntimeError("Fake Connection is not open")

        timedout = False
        frame = None
        try:
            frame = self.rxqueue.get(block=True, timeout=timeout)
            #frame = self.rxqueue.get(block=True, timeout=5)

        except queue.Empty:
            timedout = True

        if timedout:
            raise TimeoutException("Did not received response from J2534 RxQueue (timeout=%s sec)" % timeout)

        return frame

    def empty_rxqueue(self):
        while not self.rxqueue.empty():
            self.rxqueue.get()

    

