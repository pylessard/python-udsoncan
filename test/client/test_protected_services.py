from udsoncan import services
from udsoncan.exceptions import *
from udsoncan import DidCodec
import struct

from test.ClientServerTest import ClientServerTest


class StubbedDidCodec(DidCodec):
    def encode(self, did_value):
        return struct.pack('B', did_value + 1)

    def decode(self, did_payload):
        return struct.unpack('B', did_payload)[0] - 1

    def __len__(self):
        return 1


class TestProtectedServicesBase(ClientServerTest):
    def __init__(self, *args, **kwargs):
        ClientServerTest.__init__(self, *args, **kwargs)

    def dummy_algo(self, level, seed, params=None):
        key = bytearray(seed)
        for i in range(len(key)):
            key[i] = (params + level + i + key[i])
        return bytes(key)

    def postClientSetUp(self):
        self.udsclient.config["data_identifiers"] = {
            0x1234: '>H',
            0x5678: '>H',
        }


class TestProtectedServicesConfiguration(TestProtectedServicesBase):

    def test_protected_service_access_denied_without_unlock(self):
        pass

    def _test_protected_service_access_denied_without_unlock(self):
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }

        with self.assertRaises(SecurityAccessDeniedException) as context:
            self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)

        self.assertEqual(context.exception.required_level, 0x05)
        self.assertEqual(context.exception.resource_type, 'service')
        self.assertEqual(context.exception.resource_id, services.WriteDataByIdentifier._sid)

    def test_protected_service_access_granted_after_unlock(self):
        self.conn.fromuserqueue.put(b"\x67\x05\x11\x22\x33\x44")
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x27\x05")
        key = bytearray([(0x10 + 0x05 + 0 + 0x11), (0x10 + 0x05 + 1 + 0x22), (0x10 + 0x05 + 2 + 0x33), (0x10 + 0x05 + 3 + 0x44)])
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x27\x06" + bytes(key))
        self.conn.fromuserqueue.put(b"\x67\x06")

        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2E\x12\x34\x12\x34")
        self.conn.fromuserqueue.put(b"\x6E\x12\x34")

    def _test_protected_service_access_granted_after_unlock(self):
        self.udsclient.config['security_algo'] = self.dummy_algo
        self.udsclient.config['security_algo_params'] = 0x10
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }

        self.udsclient.unlock_security_access(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        response = self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)
        self.assertTrue(response.positive)

    def test_protected_did_access_denied_without_unlock(self):
        pass

    def _test_protected_did_access_denied_without_unlock(self):
        self.udsclient.config['protected_dids'] = {
            0x1234: 0x05
        }

        with self.assertRaises(SecurityAccessDeniedException) as context:
            self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)

        self.assertEqual(context.exception.required_level, 0x05)
        self.assertEqual(context.exception.resource_type, 'DID')
        self.assertEqual(context.exception.resource_id, 0x1234)

    def test_protected_did_access_granted_after_unlock(self):
        self.conn.fromuserqueue.put(b"\x67\x05\x11\x22\x33\x44")
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x27\x05")
        key = bytearray([(0x10 + 0x05 + 0 + 0x11), (0x10 + 0x05 + 1 + 0x22), (0x10 + 0x05 + 2 + 0x33), (0x10 + 0x05 + 3 + 0x44)])
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x27\x06" + bytes(key))
        self.conn.fromuserqueue.put(b"\x67\x06")

        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x2E\x12\x34\x12\x34")
        self.conn.fromuserqueue.put(b"\x6E\x12\x34")

    def _test_protected_did_access_granted_after_unlock(self):
        self.udsclient.config['security_algo'] = self.dummy_algo
        self.udsclient.config['security_algo_params'] = 0x10
        self.udsclient.config['protected_dids'] = {
            0x1234: 0x05
        }

        self.udsclient.unlock_security_access(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        response = self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)
        self.assertTrue(response.positive)

    def test_unprotected_did_access_allowed(self):
        self.conn.fromuserqueue.put(b"\x6E\x56\x78")

    def _test_unprotected_did_access_allowed(self):
        self.udsclient.config['protected_dids'] = {
            0x1234: 0x05
        }

        response = self.udsclient.write_data_by_identifier(did=0x5678, value=0x1234)
        self.assertTrue(response.positive)

    def test_protected_routine_access_denied_without_unlock(self):
        pass

    def _test_protected_routine_access_denied_without_unlock(self):
        self.udsclient.config['protected_routines'] = {
            0xFF00: 0x07
        }

        with self.assertRaises(SecurityAccessDeniedException) as context:
            self.udsclient.start_routine(0xFF00)

        self.assertEqual(context.exception.required_level, 0x07)
        self.assertEqual(context.exception.resource_type, 'routine')
        self.assertEqual(context.exception.resource_id, 0xFF00)

    def test_protected_routine_access_granted_after_unlock(self):
        self.conn.fromuserqueue.put(b"\x67\x07\x11\x22\x33\x44")
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x27\x07")
        key = bytearray([(0x10 + 0x07 + 0 + 0x11), (0x10 + 0x07 + 1 + 0x22), (0x10 + 0x07 + 2 + 0x33), (0x10 + 0x07 + 3 + 0x44)])
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x27\x08" + bytes(key))
        self.conn.fromuserqueue.put(b"\x67\x08")

        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x31\x01\xFF\x00")
        self.conn.fromuserqueue.put(b"\x71\x01\xFF\x00")

    def _test_protected_routine_access_granted_after_unlock(self):
        self.udsclient.config['security_algo'] = self.dummy_algo
        self.udsclient.config['security_algo_params'] = 0x10
        self.udsclient.config['protected_routines'] = {
            0xFF00: 0x07
        }

        self.udsclient.unlock_security_access(0x07)
        self.assertIn(0x07, self.udsclient.get_unlocked_security_levels())

        response = self.udsclient.start_routine(0xFF00)
        self.assertTrue(response.positive)

    def test_no_config_means_no_protection(self):
        self.conn.fromuserqueue.put(b"\x6E\x12\x34")

    def _test_no_config_means_no_protection(self):
        response = self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)
        self.assertTrue(response.positive)


class TestSecurityStateReset(TestProtectedServicesBase):

    def test_session_change_resets_security_access(self):
        self.conn.fromuserqueue.put(b"\x50\x03\x00\x0A\x00\x14")

    def _test_session_change_resets_security_access(self):
        self.udsclient.config['standard_version'] = 2013
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }

        self.udsclient._unlocked_security_levels.add(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        self.udsclient.change_session(0x03)
        self.assertEqual(self.udsclient.get_unlocked_security_levels(), set())

        with self.assertRaises(SecurityAccessDeniedException):
            self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)

    def test_ecu_reset_resets_security_access(self):
        self.conn.fromuserqueue.put(b"\x51\x01")

    def _test_ecu_reset_resets_security_access(self):
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }

        self.udsclient._unlocked_security_levels.add(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        self.udsclient.ecu_reset(0x01)
        self.assertEqual(self.udsclient.get_unlocked_security_levels(), set())

        with self.assertRaises(SecurityAccessDeniedException):
            self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)

    def test_connection_close_resets_security_access(self):
        pass

    def _test_connection_close_resets_security_access(self):
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }

        self.udsclient._unlocked_security_levels.add(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        self.udsclient.close()
        self.assertEqual(self.udsclient.get_unlocked_security_levels(), set())


class TestCombinedProtection(TestProtectedServicesBase):

    def test_both_service_and_did_protected(self):
        self.conn.fromuserqueue.put(b"\x6E\x12\x34")

    def _test_both_service_and_did_protected(self):
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }
        self.udsclient.config['protected_dids'] = {
            0x1234: 0x05
        }

        self.udsclient._unlocked_security_levels.add(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        response = self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)
        self.assertTrue(response.positive)

    def test_service_and_did_require_different_levels(self):
        self.conn.fromuserqueue.put(b"\x6E\x12\x34")

    def _test_service_and_did_require_different_levels(self):
        self.udsclient.config['protected_services'] = {
            services.WriteDataByIdentifier._sid: 0x05
        }
        self.udsclient.config['protected_dids'] = {
            0x1234: 0x07
        }

        self.udsclient._unlocked_security_levels.add(0x05)
        self.assertIn(0x05, self.udsclient.get_unlocked_security_levels())

        with self.assertRaises(SecurityAccessDeniedException) as context:
            self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)
        self.assertEqual(context.exception.required_level, 0x07)

        self.udsclient._unlocked_security_levels.add(0x07)
        self.assertIn(0x07, self.udsclient.get_unlocked_security_levels())

        response = self.udsclient.write_data_by_identifier(did=0x1234, value=0x1234)
        self.assertTrue(response.positive)
