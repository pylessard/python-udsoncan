from udsoncan import services, MemoryLocation, DataFormatIdentifier, DynamicDidDefinition
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest

class TestDynamicallyDefineDataIdentifier(ClientServerTest):
    def __init__(self, *args, **kwargs):
        ClientServerTest.__init__(self, *args, **kwargs)

    # ====== Define by DID ==========

    def test_define_by_did_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x01\xf2\x01\x12\x34\x01\x02")
        self.conn.fromuserqueue.put(b"\x6c\x01\xf2\x01")    # Positive response

    def _test_define_by_did_success(self):
        response = self.udsclient.dynamically_define_did(0xf201, DynamicDidDefinition(source_did = 0x1234, position=1, memorysize=2))
        self.assertEqual(response.service_data.subfunction_echo, 1)
        self.assertEqual(response.service_data.did_echo, 0xf201)

    def test_define_by_did_composite_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x01\xf2\x02\x12\x34\x01\x02\x56\x78\x01\x04\x12\x34\x05\x02")
        self.conn.fromuserqueue.put(b"\x6c\x01\xf2\x02")    # Positive response

    def _test_define_by_did_composite_success(self):
        diddef = DynamicDidDefinition(source_did = 0x1234, position=1, memorysize=2)
        diddef.add(source_did = 0x5678, position=1, memorysize=4)
        diddef.add(source_did = 0x1234, position=5, memorysize=2)

        response = self.udsclient.dynamically_define_did(0xf202, diddef)
        self.assertEqual(response.service_data.subfunction_echo, 1)
        self.assertEqual(response.service_data.did_echo, 0xf202)

    def test_define_by_did_composite_wrong_subfunction_echo(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c\x02\xf3\x03")    # Positive response

    def _test_define_by_did_composite_wrong_subfunction_echo(self):
        diddef = DynamicDidDefinition(source_did = 0x1234, position=1, memorysize=2)
        diddef.add(source_did = 0x5678, position=1, memorysize=4)
        diddef.add(source_did = 0x1234, position=5, memorysize=2)

        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.dynamically_define_did(0xf203, diddef)

    def test_define_by_did_composite_wrong_did_echo(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c\x01\xf3\x05")    # Positive response

    def _test_define_by_did_composite_wrong_did_echo(self):
        diddef = DynamicDidDefinition(source_did = 0x1234, position=1, memorysize=2)
        diddef.add(source_did = 0x5678, position=1, memorysize=4)
        diddef.add(source_did = 0x1234, position=5, memorysize=2)

        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.dynamically_define_did(0xf204, diddef)

    def test_define_by_did_incomplete_response(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c") 

    def _test_define_by_did_incomplete_response(self):
        with self.assertRaises(InvalidResponseException):
            self.udsclient.dynamically_define_did(0xf201, DynamicDidDefinition(source_did = 0x1234, position=1, memorysize=2))




    # ====== Define by Memory Address ==========
    def test_define_by_memloc_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x02\xf3\x01\x12\x56\x78\x45")
        self.conn.fromuserqueue.put(b"\x6c\x02\xf3\x01")    # Positive response

    def _test_define_by_memloc_success(self):
        memloc = MemoryLocation(address=0x5678, memorysize=0x45 ,address_format=16, memorysize_format=8)
        response = self.udsclient.dynamically_define_did(0xf301, memloc)
        self.assertEqual(response.service_data.subfunction_echo, 2)
        self.assertEqual(response.service_data.did_echo, 0xf301)

    def test_define_by_memloc_composite_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x02\xf3\x02\x12\x11\x22\x02\x33\x44\x04\x55\x66\x08")
        self.conn.fromuserqueue.put(b"\x6c\x02\xf3\x02")    # Positive response

    def _test_define_by_memloc_composite_success(self):
        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x5566, memorysize=8, address_format=16, memorysize_format=8))

        response = self.udsclient.dynamically_define_did(0xf302, diddef)
        self.assertEqual(response.service_data.subfunction_echo, 2)
        self.assertEqual(response.service_data.did_echo, 0xf302)

    def test_define_by_memloc_composite_success_default_format(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x02\xf3\x02\x24\x00\x00\x11\x22\x00\x02\x00\x00\x33\x44\x00\x04\x00\x00\x55\x66\x00\x08")
        self.conn.fromuserqueue.put(b"\x6c\x02\xf3\x02")    # Positive response

    def _test_define_by_memloc_composite_success_default_format(self):
        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4))
        diddef.add(MemoryLocation(address=0x5566, memorysize=8))

        self.udsclient.set_config('server_address_format', 32)
        self.udsclient.set_config('server_memorysize_format', 16)

        response = self.udsclient.dynamically_define_did(0xf302, diddef)
        self.assertEqual(response.service_data.subfunction_echo, 2)
        self.assertEqual(response.service_data.did_echo, 0xf302)

    def test_inconsistent_composite_memloc(self):
        pass

    def _test_inconsistent_composite_memloc(self):
        self.udsclient.set_config('server_address_format', 16)
        self.udsclient.set_config('server_memorysize_format', 8)

        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x11, memorysize=2, address_format=8, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=16, memorysize_format=8))
        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(0xf300, diddef)

        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=16, memorysize_format=16))
        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(0xf300, diddef)

        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=32, memorysize_format=8))
        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(0xf300, diddef)

        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=16, memorysize_format=16))
        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(0xf300, diddef)

    def test_define_by_memloc_composite_wrong_subfunction_echo(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c\x03\xf3\x02")    # Positive response

    def _test_define_by_memloc_composite_wrong_subfunction_echo(self):
        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x5566, memorysize=8, address_format=16, memorysize_format=8))

        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.dynamically_define_did(0xf302, diddef)
 
    def test_define_by_memloc_composite_wrong_did_echo(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c\x02\xf3\x03")    # Positive response

    def _test_define_by_memloc_composite_wrong_did_echo(self):
        diddef = DynamicDidDefinition()
        diddef.add(MemoryLocation(address=0x1122, memorysize=2, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x3344, memorysize=4, address_format=16, memorysize_format=8))
        diddef.add(MemoryLocation(address=0x5566, memorysize=8, address_format=16, memorysize_format=8))

        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.dynamically_define_did(0xf302, diddef)       



    # ====== Clear ==========

    def test_clear_dynamic_did(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x03\xf2\x00")
        self.conn.fromuserqueue.put(b"\x6c\x03\xf2\x00")    # Positive response

    def _test_clear_dynamic_did(self):
        response = self.udsclient.clear_dynamically_defined_did(0xF200)
        self.assertEqual(response.service_data.subfunction_echo, 3)
        self.assertEqual(response.service_data.did_echo,0xf200)

    def test_clear_all_dynamic_did(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x03")
        self.conn.fromuserqueue.put(b"\x6c\x03")    # Positive response

    def _test_clear_all_dynamic_did(self):
        response = self.udsclient.clear_all_dynamically_defined_did()
        self.assertEqual(response.service_data.subfunction_echo, 3)


    # Error handling

    def test_clear_dynamic_did_wrong_subfunction_echo(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c\x02\xf2\x00")    # Positive response

    def _test_clear_dynamic_did_wrong_subfunction_echo(self):
        with self.assertRaises(UnexpectedResponseException) as handle:
            self.udsclient.clear_dynamically_defined_did(0xF200)

    def test_clear_dynamic_did_wrong_did_echo(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.conn.fromuserqueue.put(b"\x6c\x03\xf2\x01")    # Positive response

    def _test_clear_dynamic_did_wrong_did_echo(self):
        with self.assertRaises(UnexpectedResponseException) as handle:
            self.udsclient.clear_dynamically_defined_did(0xF200)


    def test_clear_all_dynamic_did_negative_response(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2C\x03")
        self.conn.fromuserqueue.put(b"\x7F\x2C\x10")    # General Reject

    def _test_clear_all_dynamic_did_negative_response(self):
        with self.assertRaises(NegativeResponseException) as handle:
            self.udsclient.clear_all_dynamically_defined_did()
        response = handle.exception.response

        self.assertTrue(response.valid)
        self.assertTrue(issubclass(response.service, services.DynamicallyDefineDataIdentifier))
        self.assertEqual(response.code, 0x10)

    def test_clear_all_dynamic_did_negative_response_no_exception(self):
        self.wait_request_and_respond(b"\x7F\x2C\x10")  # General Reject

    def _test_clear_all_dynamic_did_negative_response_no_exception(self):
        self.udsclient.config['exception_on_negative_response'] = False
        response = self.udsclient.clear_all_dynamically_defined_did()

        self.assertTrue(response.valid)
        self.assertFalse(response.positive)
        self.assertTrue(issubclass(response.service, services.DynamicallyDefineDataIdentifier))
        self.assertEqual(response.code, 0x10)


    def test_clear_all_dynamic_did_invalidservice_exception(self):
        self.wait_request_and_respond(b"\x00\x03")  #Inexistent Service

    def _test_clear_all_dynamic_did_invalidservice_exception(self):
        with self.assertRaises(InvalidResponseException) as handle:
            self.udsclient.clear_all_dynamically_defined_did()

    def test_clear_all_dynamic_did_invalidservice_no_exception(self):
        self.wait_request_and_respond(b"\x00\x03") #Inexistent Service

    def _test_clear_all_dynamic_did_invalidservice_no_exception(self):
        self.udsclient.config['exception_on_invalid_response'] = False
        response = self.udsclient.clear_all_dynamically_defined_did()
        self.assertFalse(response.valid)

    def test_clear_all_dynamic_did_wrongservice_exception(self):
        self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

    def _test_clear_all_dynamic_did_wrongservice_exception(self):
        with self.assertRaises(UnexpectedResponseException) as handle:
            self.udsclient.clear_all_dynamically_defined_did()

    def test_clear_all_dynamic_did_wrongservice_no_exception(self):
        self.wait_request_and_respond(b"\x7E\x00") # Valid but wrong service (Tester Present)

    def _test_clear_all_dynamic_did_wrongservice_no_exception(self):
        self.udsclient.config['exception_on_unexpected_response'] = False
        response = self.udsclient.clear_all_dynamically_defined_did()
        self.assertTrue(response.valid)
        self.assertTrue(response.unexpected)


    # ====== Others ==========
    def test_bad_params(self):
        pass

    def _test_bad_params(self):
        empty_diddef = DynamicDidDefinition()
        valid_diddef = DynamicDidDefinition(source_did = 0x1234, position=1, memorysize=1)

        with self.assertRaises(ValueError):
            self.udsclient.clear_dynamically_defined_did(-1)

        with self.assertRaises(ValueError):
            self.udsclient.clear_dynamically_defined_did(0x10000)

        with self.assertRaises(ValueError):
            self.udsclient.clear_dynamically_defined_did('aaa')

        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(-1, valid_diddef)

        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(0x10000, valid_diddef)

        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did(0xF200, empty_diddef)

        with self.assertRaises(Exception):
            self.udsclient.dynamically_define_did(0xF200, 'aaa')

        with self.assertRaises(ValueError):
            self.udsclient.dynamically_define_did('aaa', valid_diddef)

