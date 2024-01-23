from udsoncan.exceptions import TimeoutException
from udsoncan import connections, Request, Response
import queue
import logging
import socket
from dataclasses import dataclass


class StubbedIsoTPSocket(object):
    conns = {}

    def __init__(self, name=None, timeout=1):
        self.bound = False
        self.interface = None
        self.address = None
        self.timeout = timeout

        self.queue_in = queue.Queue()  # Client reads from this queue. Other end is simulated

    def bind(self, interface, address):
        self.interface = interface
        self.address = address
        self.bound = True
        sockkey = (self.interface, self.address)
        if sockkey not in StubbedIsoTPSocket.conns:
            StubbedIsoTPSocket.conns[sockkey] = dict()
        StubbedIsoTPSocket.conns[sockkey][id(self)] = self

    def close(self):
        self.bound = False
        sockkey = (self.interface, self.address)
        if sockkey in StubbedIsoTPSocket.conns:
            if id(self) in StubbedIsoTPSocket.conns[sockkey]:
                del StubbedIsoTPSocket.conns[sockkey][id(self)]
        while not self.queue_in.empty():
            self.queue_in.get()

    def must_receive(self, dst_interface: str, srcaddr: "isotp.Address", dstaddr: "isotp.Address"):
        if dst_interface != self.interface:
            return False

        @dataclass
        class StubbedCanMsg:
            is_extended_id: bool
            arbitration_id: int
            data: bytes

        # Simulate an isotp.CanMessage to work with addresses
        msg = StubbedCanMsg(
            is_extended_id=srcaddr.is_tx_29bits(),
            arbitration_id=srcaddr.get_tx_arbitration_id(),
            data=bytes([srcaddr.get_tx_extension_byte()]) if srcaddr.requires_tx_extension_byte() else bytes()
        )

        if dstaddr.is_for_me(msg):
            return True

        return False

    def send(self, payload):
        # if target_sockkey in StubbedIsoTPSocket.conns:
        for target_sockkey in StubbedIsoTPSocket.conns:
            dst_interface = target_sockkey[0]
            dstaddr = target_sockkey[1]
            if self.must_receive(dst_interface, self.address, dstaddr):
                for sockid in StubbedIsoTPSocket.conns[target_sockkey]:
                    StubbedIsoTPSocket.conns[target_sockkey][sockid].queue_in.put(payload)

    def recv(self):
        try:
            payload = self.queue_in.get(block=True, timeout=self.timeout)
        except queue.Empty:
            raise socket.timeout
        return payload
