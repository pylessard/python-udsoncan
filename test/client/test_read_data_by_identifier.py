from udsoncan.exceptions import *
from udsoncan import DidCodec, AsciiCodec
import struct
from copy import deepcopy
from test.ClientServerTest import ClientServerTest


class StubbedDidCodec(DidCodec):
    def encode(self, did_value):
        return struct.pack('B', did_value + 1)

    def decode(self, did_payload):
        return struct.unpack('B', did_payload)[0] - 1

    def __len__(self):
        return 1


class ReadRemainingDataCodec(DidCodec):

    def encode(self, *args, **kwargs):
        return b''

    def decode(self, did_payload):
        return did_payload

    def __len__(self):
        raise self.ReadAllRemainingData


class CodecWithNoLength(DidCodec):

    def encode(self, *args, **kwargs):
        return b''

    def decode(self, did_payload):
        return did_payload


class TestReadDataByIdentifier(ClientServerTest):
    def __init__(self, *args, **kwargs):
        ClientServerTest.__init__(self, *args, **kwargs)

    def postClientSetUp(self):
        self.udsclient.config["data_identifiers"] = {
            1: '>H',
            2: '<H',
            3: StubbedDidCodec,
            4: AsciiCodec(5),
            5: ReadRemainingDataCodec,
            6: CodecWithNoLength
        }

    def test_rdbi_single_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x22\x00\x01")
        self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34")  # Positive response

    def _test_rdbi_single_success(self):
        response = self.udsclient.read_data_by_identifier(didlist=1)
        self.assertTrue(response.positive)
        values = response.service_data.values
        self.assertEqual(values[1], (0x1234,))

    def test_peek_rdbi_single_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x22\x11\x22")
        self.conn.fromuserqueue.put(b"\x62\x11\x22\x12\x34")  # Positive response

    def _test_peek_rdbi_single_success(self):
        response = self.udsclient.test_data_identifier(0x1122)  # not in config, but this is OK
        self.assertTrue(response.positive)
        self.assertIsNone(response.service_data)
        self.assertEqual(response.data, b"\x11\x22\x12\x34")

    def test_rdbi_single_success_default_did(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x22\x00\x01")
        self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34")  # Positive response

    def _test_rdbi_single_success_default_did(self):
        self.udsclient.config["data_identifiers"] = {
            'default': '>H',
            2: '<H',
            3: StubbedDidCodec
        }
        original_config = deepcopy(self.udsclient.config)
        response = self.udsclient.read_data_by_identifier(didlist=1)
        self.assertTrue(response.positive)
        values = response.service_data.values
        self.assertEqual(values[1], (0x1234,))
        self.assertEqual(original_config, self.udsclient.config)    # MAke sure it is not changed

    def test_rdbi_single_success_spr_no_effect(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x22\x00\x01")
        self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34")  # Positive response

    def _test_rdbi_single_success_spr_no_effect(self):
        with self.udsclient.suppress_positive_response:
            response = self.udsclient.read_data_by_identifier(didlist=1)
            self.assertTrue(response.positive)
            values = response.service_data.values
            self.assertEqual(values[1], (0x1234,))

    def test_rdbi_multiple_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x22\x00\x01\x00\x02\x00\x04\x00\x03")
        self.conn.fromuserqueue.put(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x04\x61\x62\x63\x64\x65\x00\x03\x11")  # Positive response

    def _test_rdbi_multiple_success(self):
        response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 4, 3])
        self.assertTrue(response.positive)
        values = response.service_data.values
        self.assertEqual(values[1], (0x1234,))
        self.assertEqual(values[2], (0x7856,))
        self.assertEqual(values[3], 0x10)
        self.assertEqual(values[4], 'abcde')

    def test_peek_rdbi_multiple_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x22\x11\x22\x33\x44")
        self.conn.fromuserqueue.put(b"\x62\xaa")  # Positive response, content can be invalid. we don't check with the peek method

    def _test_peek_rdbi_multiple_success(self):
        response = self.udsclient.test_data_identifier([0x1122, 0x3344])
        self.assertTrue(response.positive)
        self.assertIsNone(response.service_data)

    def test_rdbi_multiple_zero_padding1_success(self):
        data = b'\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11'
        for i in range(8):
            self.wait_request_and_respond(data + b"\x00" * (i + 1))

    def _test_rdbi_multiple_zero_padding1_success(self):
        self.udsclient.config['tolerate_zero_padding'] = True
        for i in range(8):
            response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])
            self.assertTrue(response.positive)
            values = response.service_data.values
            self.assertEqual(values[1], (0x1234,))
            self.assertEqual(values[2], (0x7856,))
            self.assertEqual(values[3], 0x10)
            self.assertFalse(0 in values)

    def test_rdbi_multiple_zero_padding_not_tolerated_exception(self):
        data = b'\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11'

        self.wait_request_and_respond(data + b"\x00")  # One extra byte is incomplete DID = invalid response

        for i in range(1, 7):
            # 2 extra bytes = valid DID. Make sure to have data in payload as library do not allow empty pack string
            self.wait_request_and_respond(data + b"\x00" * (i + 2))

    def _test_rdbi_multiple_zero_padding_not_tolerated_exception(self):
        self.udsclient.config['tolerate_zero_padding'] = False
        for i in range(1):
            with self.assertRaises(InvalidResponseException):
                self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])

        for i in range(1, 7):
            with self.assertRaises(UnexpectedResponseException):  # Not requested DID 0x0000
                self.udsclient.config['data_identifiers'][0] = 'B' * i
                self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])

    def test_rdbi_multiple_zero_padding_not_tolerated_no_exception(self):
        data = b'\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11'
        self.wait_request_and_respond(data + b"\x00")  # One extra byte is incomplete DID = invalid response

        for i in range(1, 7):
            # 2 extra bytes = valid DID. Make sure to have data in payload as library do not allow empty pack string
            self.wait_request_and_respond(data + b"\x00" * (i + 2))

    def _test_rdbi_multiple_zero_padding_not_tolerated_no_exception(self):
        self.udsclient.config['tolerate_zero_padding'] = False

        self.udsclient.config['exception_on_invalid_response'] = False
        self.udsclient.config['exception_on_unexpected_response'] = True

        response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])
        self.assertFalse(response.valid)

        self.udsclient.config['exception_on_invalid_response'] = True
        self.udsclient.config['exception_on_unexpected_response'] = False
        for i in range(1, 7):
            self.udsclient.config['data_identifiers'][0] = 'B' * i
            response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])
            self.assertTrue(response.valid)
            self.assertTrue(response.unexpected)

    def test_rdbi_variable_size_did(self):
        self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x05\xaa\xbb\xcc\xdd")

    def _test_rdbi_variable_size_did(self):
        response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 5])
        self.assertTrue(response.positive)
        values = response.service_data.values
        self.assertEqual(values[1], (0x1234,))
        self.assertEqual(values[2], (0x7856,))
        self.assertEqual(values[5], b'\xaa\xbb\xcc\xdd')

    # DID 5 read all the data up to the end. Makes no sense to read another DID after that.
    def test_rdbi_variable_size_did_not_last(self):
        pass

    def _test_rdbi_variable_size_did_not_last(self):
        with self.assertRaises(ValueError):
            self.udsclient.read_data_by_identifier(didlist=[1, 2, 5, 3])

    def test_rdbi_incomplete_response_exception(self):
        self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03")

    def _test_rdbi_incomplete_response_exception(self):
        with self.assertRaises(InvalidResponseException):
            self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])

    def test_rdbi_incomplete_response_no_exception(self):
        self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03")

    def _test_rdbi_incomplete_response_no_exception(self):
        self.udsclient.config['exception_on_invalid_response'] = False
        response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])
        self.assertFalse(response.valid)

    def test_rdbi_unknown_did_exception(self):
        self.wait_request_and_respond(b"\x62\x00\x09\x12\x34\x00\x02\x56\x78\x00\x03\x11")

    def _test_rdbi_unknown_did_exception(self):
        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])

    def test_rdbi_unknown_did_no_exception(self):
        self.wait_request_and_respond(b"\x62\x00\x09\x12\x34\x00\x02\x56\x78\x00\x03\x11")

    def _test_rdbi_unknown_did_no_exception(self):
        self.udsclient.config['exception_on_unexpected_response'] = False
        response = self.udsclient.read_data_by_identifier(didlist=[1, 2, 3])
        self.assertTrue(response.valid)
        self.assertTrue(response.unexpected)

    def test_rdbi_unwanted_did_exception(self):
        self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")

    def _test_rdbi_unwanted_did_exception(self):
        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.read_data_by_identifier(didlist=[1, 3])

    def test_rdbi_unwanted_did_no_exception(self):
        self.wait_request_and_respond(b"\x62\x00\x01\x12\x34\x00\x02\x56\x78\x00\x03\x11")

    def _test_rdbi_unwanted_did_no_exception(self):
        self.udsclient.config['exception_on_unexpected_response'] = False
        response = self.udsclient.read_data_by_identifier(didlist=[1, 3])
        self.assertTrue(response.valid)
        self.assertTrue(response.unexpected)

    def test_rdbi_invalidservice_exception(self):
        self.wait_request_and_respond(b"\x00\x00\x01\x12\x34")  # Service is inexistant

    def _test_rdbi_invalidservice_exception(self):
        with self.assertRaises(InvalidResponseException) as handle:
            self.udsclient.read_data_by_identifier(didlist=1)

    def test_rdbi_invalidservice_no_exception(self):
        self.wait_request_and_respond(b"\x00\x00\x01\x12\x34")  # Service is inexistant

    def _test_rdbi_invalidservice_no_exception(self):
        self.udsclient.config['exception_on_invalid_response'] = False
        response = self.udsclient.read_data_by_identifier(didlist=1)
        self.assertFalse(response.valid)

    def test_rdbi_wrongservice_exception(self):
        self.wait_request_and_respond(b"\x50\x00\x01\x12\x34")  # Valid service, but not the one requested

    def _test_rdbi_wrongservice_exception(self):
        with self.assertRaises(UnexpectedResponseException) as handle:
            self.udsclient.read_data_by_identifier(didlist=1)

    def test_rdbi_wrongservice_no_exception(self):
        self.wait_request_and_respond(b"\x50\x00\x01\x12\x34")  # Valid service, but not the one requested

    def _test_rdbi_wrongservice_no_exception(self):
        self.udsclient.config['exception_on_unexpected_response'] = False
        response = self.udsclient.read_data_by_identifier(didlist=1)
        self.assertTrue(response.valid)
        self.assertTrue(response.unexpected)

    def test_peek_rdbi_wrongservice_exception(self):
        self.wait_request_and_respond(b"\x50\x00\x01\x12\x34")  # Valid service, but not the one requested

    def _test_peek_rdbi_wrongservice_exception(self):
        with self.assertRaises(UnexpectedResponseException) as handle:
            self.udsclient.test_data_identifier(0x1122)

    def test_peek_rdbi_wrongservice_no_exception(self):
        self.wait_request_and_respond(b"\x50\x00\x01\x12\x34")  # Valid service, but not the one requested

    def _test_peek_rdbi_wrongservice_no_exception(self):
        self.udsclient.config['exception_on_unexpected_response'] = False
        response = self.udsclient.test_data_identifier(0x1122)
        self.assertTrue(response.valid)
        self.assertTrue(response.unexpected)

    def test_peek_rdbi_negative_exception(self):
        self.wait_request_and_respond(b"\x7F\x22\x10")  # general reject

    def _test_peek_rdbi_negative_exception(self):
        with self.assertRaises(NegativeResponseException) as handle:
            self.udsclient.test_data_identifier(0x1122)

    def test_peek_rdbi_negative_no_exception(self):
        self.wait_request_and_respond(b"\x7F\x22\x10")  # general reject

    def _test_peek_rdbi_negative_no_exception(self):
        self.udsclient.config['exception_on_negative_response'] = False
        response = self.udsclient.test_data_identifier(0x1122)
        self.assertTrue(response.valid)
        self.assertFalse(response.unexpected)
        self.assertFalse(response.positive)

    def test_no_config(self):
        pass

    def _test_no_config(self):
        with self.assertRaises(ConfigError):
            self.udsclient.read_data_by_identifier(didlist=[1, 2, 3, 99])

    def test_no_length(self):
        pass

    def _test_no_length(self):
        with self.assertRaises(NotImplementedError):
            self.udsclient.read_data_by_identifier(didlist=[6])
