from udsoncan.connections import QueueConnection
from test.ThreadableTest import ThreadableTest
from udsoncan.client import Client
from typing import Optional

class ClientServerTest(ThreadableTest):
    _standard_version:Optional[int]

    def __init__(self, *args, **kwargs):
        self._standard_version = None
        ThreadableTest.__init__(self, *args, **kwargs)
    
    def set_standard(self, version:int):
        self._standard_version = version

    def setUp(self):
        self.conn = QueueConnection(name='unittest', mtu=4095)

    def clientSetUp(self):
        self.udsclient = Client(self.conn, request_timeout=0.2)
        self.udsclient.set_config('logger_name', 'unittest')
        self.udsclient.set_config('exception_on_invalid_response', True)
        self.udsclient.set_config('exception_on_unexpected_response', True)
        self.udsclient.set_config('exception_on_negative_response', True)
        if self._standard_version is not None:
            self.udsclient.set_config('standard_version', self._standard_version)

        self.udsclient.open()
        if hasattr(self, "postClientSetUp"):
            self.postClientSetUp()

    def clientTearDown(self):
        self.udsclient.close()

    def wait_request_and_respond(self, bytes):
        self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(bytes) 
