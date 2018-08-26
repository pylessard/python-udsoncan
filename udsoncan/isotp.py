"""Basic Python implementation of the ISO-TP (ISO-15765) protocol.

This module is only meant to be a last resort when there is no lower level
implementation available. It is not complete with respect to the standard and
the protocol timing requirements is likely to be violated on an OS like Windows.

Do not use in a production environment!
"""
import time
import struct

from udsoncan.exceptions import TimeoutException


SINGLE_FRAME = 0
FIRST_FRAME = 1
CONSECUTIVE_FRAME = 2
FLOW_CONTROL_FRAME = 3

CONTINUE_TO_SEND = 0
WAIT = 1
OVERFLOW = 2


class ISOTPError(Exception):
    """An error occurred related to the protocol."""
    pass


class ISOTPMixin:
    """Basic ISO-TP implementation.

    Should be used in a :class:`~udsoncan.connections.BaseConnection` subclass
    which must implement a send_raw and recv_raw method.
    """

    def __init__(self, block_size=0, st_min=0):
        self.block_size = block_size
        self.st_min = st_min

    def send_isotp(self, payload):
        """Transmit a message.

        :param bytes payload: Data to be transmitted.
        """
        size = len(payload)

        if size < 8:
            # Single frame
            data = bytearray(8)
            data[0] = (SINGLE_FRAME << 4) + size
            data[1:size + 1] = payload
            self.send_raw(data)
        else:
            # Create first frame
            data = bytearray(8)
            if size < 4096:
                data[0] = (FIRST_FRAME << 4) + (size >> 8)
                data[1] = size & 0xFF
                data[2:8] = payload[0:6]
                sent = 6
            else:
                data[0] = FIRST_FRAME << 4
                data[1] = 0
                struct.pack_into('>L', data, 2, size)
                data[6:8] = payload[0:2]
                sent = 2

            self.logger.debug('Sending first frame')
            self.send_raw(data)

            sequence_number = 1
            block_count = 0
            block_size, st_min = self._wait_for_flow_control()

            while True:
                frame_payload = payload[sent:sent + 7]
                data = bytearray()
                data.append((CONSECUTIVE_FRAME << 4) + (sequence_number & 0xF))
                data.extend(frame_payload)
                self.send_raw(data)

                sent += len(frame_payload)
                self.logger.debug('%d of %d bytes sent', sent, size)
                sequence_number += 1
                block_count += 1

                if sent >= size:
                    break
                elif block_size and block_count >= block_size:
                    block_size, st_min = self._wait_for_flow_control()
                    block_count = 0
                else:
                    if st_min < 0x80:
                        wait = st_min * 1e-3
                    elif 0xF1 <= st_min <= 0xF9:
                        wait = (st_min - 0xF0) * 1e-6
                    else:
                        wait = 0.127
                    time.sleep(wait)

    def _wait_for_flow_control(self):
        self.logger.debug('Waiting for flow control frame...')
        while True:
            data = self.recv_raw(1.0)
            byte1, block_size, st_min = struct.unpack_from('BBB', data)
            fs = byte1 & 0xF
            if fs == CONTINUE_TO_SEND:
                self.logger.debug('bs=%d, st_min=0x%X', block_size, st_min)
                return block_size, st_min
            elif fs == WAIT:
                pass
            elif fs == OVERFLOW:
                raise ISOTPError('Overflow/aborted')
            else:
                raise ISOTPError('Invalid flow status')

    def recv_isotp(self, timeout=2):
        """Receive a message.

        :param float timeout:
            Timeout waiting for start of message.
        """
        data = self.recv_raw(timeout)

        byte1, = struct.unpack_from('B', data)
        pci_type = byte1 >> 4

        if pci_type == SINGLE_FRAME:
            buffer = data[1:]
            size = byte1 & 0xF
            self.logger.info('Received single frame of %d bytes', size)

        elif pci_type == FIRST_FRAME:
            buffer = bytearray()
            size = ((data[0] & 0xF) << 8) + data[1]
            if not size:
                size = struct.unpack_from('>L', data, 2)
                frame_payload = data[6:]
            else:
                frame_payload = data[2:]
            buffer.extend(frame_payload)

            self.logger.info('Receiving multi frame message of %d bytes', size)

            sequence_number = 1
            block_count = 0

            self._send_flow_control()

            while True:
                data = self.recv_raw(1.0)
                if data[0] >> 4 != CONSECUTIVE_FRAME:
                    raise ISOTPError('Reception interrupted by new transfer')

                seq_no = data[0] & 0xF
                if seq_no != sequence_number & 0xF:
                    raise ISOTPError('Wrong sequence number')

                buffer.extend(data[1:])

                if len(buffer) >= size:
                    # Last data received
                    break

                sequence_number += 1
                block_count += 1
                if block_count == self.block_size:
                    self._send_flow_control()
                    block_count = 0

        return bytes(buffer[:size])

    def _send_flow_control(self, fs=CONTINUE_TO_SEND):
        self.logger.debug('Sending flow control frame')

        data = bytearray(3)
        data[0] = (FLOW_CONTROL_FRAME << 4) + fs
        data[1] = self.block_size
        data[2] = self.st_min
        self.send_raw(data)
