import time

from udsoncan.exceptions import TimeoutException


SINGLE_FRAME = 0
FIRST_FRAME = 1
CONSECUTIVE_FRAME = 2
FLOW_CONTROL_FRAME = 3

CONTINUE_TO_SEND = 0
WAIT = 1
OVERFLOW = 2


class ISOTPError(Exception):
    pass


class ISOTPMixin:

    def __init__(self, block_size=0, st_min=0):
        self.block_size = block_size
        self.st_min = st_min

    def isotp_send(self, payload):
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
            data[0] = (FIRST_FRAME << 4) + (size >> 8)
            data[1] = size & 0xFF
            data[2:8] = payload[0:6]

            self.logger.debug('Sending first frame')
            self.send_raw(data)

            sequence_number = 1
            block_count = 0
            # Send a flow control frame after first message
            block_size = 1
            sent = 0

            while sent < size:
                block_count += 1

                if block_size and block_count >= block_size:
                    block_size, st_min = self._wait_for_flow_control()
                    block_count = 0

                if st_min < 0x80:
                    wait = st_min * 1e-3
                elif 0xF1 <= st_min <= 0xF9:
                    wait = (st_min - 0xF0) * 1e-6
                else:
                    raise ISOTPError('Invalid st_min (0x%X)' % st_min)
                time.sleep(wait)

                frame_payload = payload[sent:sent + 7]
                data = bytearray(8)
                data[0] = (CONSECUTIVE_FRAME << 4) + (sequence_number & 0xF)
                data[1:len(frame_payload) + 1] = frame_payload
                self.send_raw(data)

                sent += len(frame_payload)
                self.logger.debug('%d of %s bytes sent', sent, size)
                sequence_number += 1

    def _wait_for_flow_control(self):
        self.logger.info('Waiting for flow control frame...')
        while True:
            data = self.recv_raw(1.0)
            fs = data[0] & 0xF
            if fs == CONTINUE_TO_SEND:
                block_size = data[1]
                st_min = data[2]
                self.logger.info('Block size = %d, st_min = %d', block_size, st_min)
                return block_size, st_min
            elif fs == WAIT:
                pass
            elif fs == OVERFLOW:
                raise ISOTPError('Overflow/aborted')

    def isotp_recv(self, timeout=2):
        data = self.recv_raw(timeout)

        pci_type = data[0] >> 4

        if pci_type == SINGLE_FRAME:
            sf_dl = data[0] & 0xF
            self.logger.info('Received single frame of %d bytes', sf_dl)
            return data[1:sf_dl + 1]
        
        elif pci_type == FIRST_FRAME:
            buffer = bytearray()

            size = ((data[0] & 0xF) << 8) + data[1]
            self.logger.info('Receiving multi frame message of %d bytes', size)

            buffer.extend(data[2:size + 2])

            sequence_number = 1
            block_count = 0

            self._send_flow_control()

            while len(buffer) < size:
                data = self.recv_raw(timeout)
                if data[0] >> 4 != CONSECUTIVE_FRAME:
                    raise ISOTPError('Did not receive a consecutive frame')

                seq_no = data[0] & 0xF
                if seq_no != sequence_number & 0xF:
                    raise ISOTPError('Invalid sequence number')

                bytes_remaining = size - len(buffer)
                received_data = data[1:min(bytes_remaining, 7) + 1]
                buffer.extend(received_data)

                sequence_number += 1
                block_count += 1
                if block_count == self.block_size:
                    self._send_flow_control()
                    block_count = 0
            
            return bytes(buffer)

    def _send_flow_control(self):
        # send a flow control frame
        self.logger.info('Sending flow control frame')

        data = bytearray(3)
        data[0] = (FLOW_CONTROL_FRAME << 4) + CONTINUE_TO_SEND
        data[1] = self.block_size
        data[2] = self.st_min
        self.send_raw(data)
