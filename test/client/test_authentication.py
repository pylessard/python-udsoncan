from udsoncan import Response
from udsoncan.services.Authentication import AuthenticationReturnParameter, Authentication
from udsoncan.exceptions import NegativeResponseException, InvalidResponseException, UnexpectedResponseException

from test.ClientServerTest import ClientServerTest


class TestAuthentication(ClientServerTest):
    def __init__(self, *args, **kwargs):
        ClientServerTest.__init__(self, *args, **kwargs)

    def test_deauthentication_success(self) -> None:
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x00')
        self.conn.fromuserqueue.put(b'\x69\x00\x10')

    def _test_deauthentication_success(self) -> None:
        response: Authentication.InterpretedResponse = self.udsclient.deauthenticate()
        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.deAuthenticate)
        self.assertEqual(response.service_data.return_value, AuthenticationReturnParameter.DeAuthentication_successful)
        self.assertIsNone(response.service_data.challenge_server)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)
        self.assertIsNone(response.service_data.session_key_info)
        self.assertIsNone(response.service_data.algorithm_indicator)

    def test_deauthentication_success_spr(self) -> None:
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x80')
        self.conn.fromuserqueue.put('wait')  # Synchronize

    def _test_deauthentication_success_spr(self) -> None:
        with self.udsclient.suppress_positive_response:
            response: Authentication.InterpretedResponse = self.udsclient.deauthenticate()
            self.assertIsNone(response)
        self.conn.fromuserqueue.get(timeout=0.2)  # Avoid closing connection prematurely

    def test_verifyCertificateUnidirectional_success(self) -> None:
        # ISO 14229-1:2020 Table 89 / 90
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x01\x00\x01\xF4\x30' + bytes(498) + b'\xAD\x00\x20\xAA' + bytes(30) + b'\x44')
        self.conn.fromuserqueue.put(b'\x69\x01\x11\x00\x40\xAA' + bytes(62) + b'\x44\x00\x00')

    def _test_verifyCertificateUnidirectional_success(self) -> None:
        # ISO 14229-1:2020 Table 89 / 90
        response: Authentication.InterpretedResponse = self.udsclient.verify_certificate_unidirectional(
            communication_configuration=0,
            certificate_client=b'\x30' + bytes(498) + b'\xAD',
            challenge_client=b'\xAA' + bytes(30) + b'\x44',
        )
        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.verifyCertificateUnidirectional)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.CertificateVerified_OwnershipVerificationNecessary)
        self.assertEqual(response.service_data.challenge_server, b'\xAA' + bytes(62) + b'\x44')
        self.assertEqual(response.service_data.ephemeral_public_key_server, b'')
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)
        self.assertIsNone(response.service_data.session_key_info)
        self.assertIsNone(response.service_data.algorithm_indicator)

    def test_verifyCertificateBidirectional_success(self) -> None:
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x02\xAA\x00\x7D\xAA' + bytes(123) + b'\xBB\x01\xCA\xCC' + bytes(456) + b'\xDD')
        self.conn.fromuserqueue.put(b'\x69\x02\x13\x00\x0F\xEE' + bytes(13) + b'\xFF\x07\xC5' + bytes(1989)
                                    + b'\x00\x0Bmy precious\x00\x02\x12\x34')

    def _test_verifyCertificateBidirectional_success(self) -> None:
        response: Authentication.InterpretedResponse = self.udsclient.verify_certificate_bidirectional(
            communication_configuration=0xAA,
            certificate_client=b'\xAA' + bytes(123) + b'\xBB',
            challenge_client=b'\xCC' + bytes(456) + b'\xDD',
        )
        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.verifyCertificateBidirectional)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.CertificateVerified)
        self.assertEqual(response.service_data.challenge_server, b'\xEE' + bytes(13) + b'\xFF')
        self.assertEqual(response.service_data.certificate_server, bytes(1989))
        self.assertEqual(response.service_data.proof_of_ownership_server, b'my precious')
        self.assertEqual(response.service_data.ephemeral_public_key_server, b'\x12\x34')
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.session_key_info)
        self.assertIsNone(response.service_data.algorithm_indicator)

    def test_proofOfOwnership_success(self) -> None:
        # ISO 14229-1:2020 Table 91 / 92
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x03\x01\x50\x7F' + bytes(334) + b'\xB7\x00\x00')
        self.conn.fromuserqueue.put(b'\x69\x03\x12\x00\x00')

    def _test_proofOfOwnership_success(self) -> None:
        # ISO 14229-1:2020 Table 91 / 92
        response: Authentication.InterpretedResponse = self.udsclient.proof_of_ownership(
            proof_of_ownership_client=b'\x7F' + bytes(334) + b'\xB7'
        )

        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.proofOfOwnership)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.OwnershipVerified_AuthenticationComplete)
        self.assertEqual(response.service_data.session_key_info, b'')
        self.assertIsNone(response.service_data.challenge_server)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)
        self.assertIsNone(response.service_data.algorithm_indicator)

    def test_transmitCertificate_success(self) -> None:
        # ISO 14229-1:2020 Table 99 / 100
        # (the table missing "certificate evaluation id" - it's also not fixed in ISO 14229-1:2020 Amendment 1)
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x04\x24\x09\x01\xF4\x31' + bytes(498) + b'\xAC')
        self.conn.fromuserqueue.put(b'\x69\x04\x13')

    def _test_transmitCertificate_success(self) -> None:
        # ISO 14229-1:2020 Table 99 / 100
        # (the table missing "certificate evaluation id" - it's also not fixed in ISO 14229-1:2020 Amendment 1)
        response: Authentication.InterpretedResponse = self.udsclient.transmit_certificate(
            certificate_evaluation_id=0x2409,
            certificate_data=b'\x31' + bytes(498) + b'\xAC',
        )

        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.transmitCertificate)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.CertificateVerified)
        self.assertIsNone(response.service_data.session_key_info)
        self.assertIsNone(response.service_data.challenge_server)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)
        self.assertIsNone(response.service_data.algorithm_indicator)

    def test_requestChallengeForAuthentication(self) -> None:
        # ISO 14229-1:2020 Table 103 / 104
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x05\x00\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00')
        self.conn.fromuserqueue.put(b'\x69\x05\x00\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00\x00\x40\xAA'
                                    + bytes(62) + b'\x44\x00\x00')

    def _test_requestChallengeForAuthentication(self) -> None:
        # ISO 14229-1:2020 Table 103 / 104
        response: Authentication.InterpretedResponse = self.udsclient.request_challenge_for_authentication(
            communication_configuration=0,
            algorithm_indicator=b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00'
        )

        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.requestChallengeForAuthentication)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.RequestAccepted)
        self.assertEqual(response.service_data.algorithm_indicator, b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00')
        self.assertEqual(response.service_data.challenge_server, b'\xAA' + bytes(62) + b'\x44')
        self.assertEqual(response.service_data.needed_additional_parameter, b'')
        self.assertIsNone(response.service_data.session_key_info)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)

    def test_verifyProofOfOwnershipUnidirectional(self) -> None:
        # ISO 14229-1:2020 Table 105 / 106
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x06\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00\x01\x50'
                         + bytes.fromhex('7F2182014B7F4E44') + bytes(67) + bytes.fromhex('5F37820100') + bytes(256)
                         + b'\x00\x20\xAA' + bytes(30) + b'\x44\x00\x00')
        self.conn.fromuserqueue.put(b'\x69\x06\x12\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00\x00\x00')

    def _test_verifyProofOfOwnershipUnidirectional(self) -> None:
        # ISO 14229-1:2020 Table 105 / 106
        response: Authentication.InterpretedResponse = self.udsclient.verify_proof_of_ownership_unidirectional(
            algorithm_indicator=b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00',
            proof_of_ownership_client=bytes.fromhex('7F2182014B7F4E44') + bytes(67) + bytes.fromhex('5F37820100')
                                      + bytes(256),
            challenge_client=b'\xAA' + bytes(30) + b'\x44'
        )

        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.verifyProofOfOwnershipUnidirectional)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.OwnershipVerified_AuthenticationComplete)
        self.assertEqual(response.service_data.algorithm_indicator, b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00')
        self.assertEqual(response.service_data.session_key_info, b'')
        self.assertIsNone(response.service_data.challenge_server)
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)

    def test_verifyProofOfOwnershipBidirectional(self) -> None:
        # ISO 14229-1:2020 Table 105 / 106
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x07\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00\x01\x50'
                         + bytes.fromhex('7F2182014B7F4E44') + bytes(67) + bytes.fromhex('5F37820100') + bytes(256)
                         + b'\x00\x20\xAA' + bytes(30) + b'\x44\x00\x0819480514')
        self.conn.fromuserqueue.put(b'\x69\x07\x12\x06' + bytes(9) + b'\x0A' + bytes(4)
                                    + b'\x00\x00\x0829111947\x00\x04ETAD')

    def _test_verifyProofOfOwnershipBidirectional(self) -> None:
        # ISO 14229-1:2020 Table 105 / 106
        response: Authentication.InterpretedResponse = self.udsclient.verify_proof_of_ownership_bidirectional(
            algorithm_indicator=b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00',
            proof_of_ownership_client=bytes.fromhex('7F2182014B7F4E44') + bytes(67) + bytes.fromhex('5F37820100')
                                      + bytes(256),
            challenge_client=b'\xAA' + bytes(30) + b'\x44',
            additional_parameter=b'19480514'
        )

        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.verifyProofOfOwnershipBidirectional)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.OwnershipVerified_AuthenticationComplete)
        self.assertEqual(response.service_data.algorithm_indicator, b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00')
        self.assertEqual(response.service_data.proof_of_ownership_server, b'29111947')
        self.assertEqual(response.service_data.session_key_info, b'ETAD')
        self.assertIsNone(response.service_data.challenge_server)
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.certificate_server)

    def test_authenticationConfiguration_success(self) -> None:
        # ISO 14229-1:2020 Table 87 / 88
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x08')
        self.conn.fromuserqueue.put(b'\x69\x08\x02')

    def _test_authenticationConfiguration_success(self) -> None:
        # ISO 14229-1:2020 Table 87 / 88
        response: Authentication.InterpretedResponse = self.udsclient.authentication_configuration()
        self.assertTrue(response.positive)
        self.assertEqual(response.service_data.authentication_task_echo,
                         Authentication.AuthenticationTask.authenticationConfiguration)
        self.assertEqual(response.service_data.return_value,
                         AuthenticationReturnParameter.AuthenticationConfiguration_APCE)
        self.assertIsNone(response.service_data.challenge_server)
        self.assertIsNone(response.service_data.ephemeral_public_key_server)
        self.assertIsNone(response.service_data.needed_additional_parameter)
        self.assertIsNone(response.service_data.proof_of_ownership_server)
        self.assertIsNone(response.service_data.certificate_server)
        self.assertIsNone(response.service_data.session_key_info)
        self.assertIsNone(response.service_data.algorithm_indicator)

    def test_verifyCertificateUnidirectional_negative(self) -> None:
        # ISO 14229-1:2020 Table 95 / 96
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b'\x29\x01\x00\x01\xF4\x30' + bytes(498) + b'\xAD\x00\x20\xAA' + bytes(30) + b'\x44')
        self.conn.fromuserqueue.put(b'\x7F\x29\x50')

    def _test_verifyCertificateUnidirectional_negative(self) -> None:
        # ISO 14229-1:2020 Table 95 / 96
        with self.assertRaises(NegativeResponseException) as handle:
            self.udsclient.verify_certificate_unidirectional(
                communication_configuration=0,
                certificate_client=b'\x30' + bytes(498) + b'\xAD',
                challenge_client=b'\xAA' + bytes(30) + b'\x44',
            )

        response: Response = handle.exception.response

        self.assertTrue(response.valid)
        self.assertTrue(issubclass(response.service, Authentication))  # type: ignore
        self.assertEqual(response.code, Response.Code.CertificateVerificationFailed_InvalidTimePeriod)

    def test_authentication_unexpected_service_exception(self) -> None:
        self.wait_request_and_respond(b"\x51\x01")  # Positive ECU Reset

    def _test_authentication_unexpected_service_exception(self) -> None:
        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.authentication_configuration()

    def test_authentication_unexpected_service_no_exception(self) -> None:
        self.wait_request_and_respond(b"\x51\x01")  # Positive ECU Reset

    def _test_authentication_unexpected_service_no_exception(self) -> None:
        self.udsclient.config['exception_on_unexpected_response'] = False
        response: Response = self.udsclient.authentication_configuration()
        self.assertTrue(response.valid)
        self.assertTrue(response.unexpected)

    def test_authentication_invalid_response_no_exception(self) -> None:
        self.wait_request_and_respond(b"\x69\x08")  # no return value

    def _test_authentication_invalid_response_no_exception(self) -> None:
        self.udsclient.config['exception_on_invalid_response'] = False
        response = self.udsclient.authentication_configuration()
        self.assertFalse(response.valid)

    def test_authentication_unexpected_subfunction_exception(self) -> None:
        self.wait_request_and_respond(b'\x69\x00\x10')  # Deauthenticate

    def _test_authentication_unexpected_subfunction_exception(self):
        with self.assertRaises(UnexpectedResponseException):
            self.udsclient.authentication_configuration()

    def test_invalid_response(self) -> None:
        self.wait_request_and_respond(b'\x69')  # #0 no data
        self.wait_request_and_respond(b'\x69\x00')  # #1 no return value
        self.wait_request_and_respond(b'\x69\x00\x10\x00')  # #2 one extra byte
        self.wait_request_and_respond(b'\x69\x01\x10')  # #3 no length field
        self.wait_request_and_respond(b'\x69\x01\x10\x00')  # #4 only one byte length field
        self.wait_request_and_respond(b'\x69\x01\x10\x00\x02\x01')  # #5 data smaller than length field
        self.wait_request_and_respond(b'\x69\x05\x10')  # #6 no algorithIndicator
        self.wait_request_and_respond(b'\x69\x05\x10\x00\x00\x00\x00')  # #7 small algorithIndicator
        self.wait_request_and_respond(b'\x69\x09\x10')  # #8 Unknown Subfunction

    def _test_invalid_response(self) -> None:
        with self.assertRaises(InvalidResponseException):  # #0 no data
            self.udsclient.deauthenticate()

        with self.assertRaises(InvalidResponseException):  # #1 no return value
            self.udsclient.deauthenticate()

        with self.assertRaises(InvalidResponseException):  # #2 one extra byte
            self.udsclient.deauthenticate()

        with self.assertRaises(InvalidResponseException):  # #3 no length field
            self.udsclient.verify_certificate_unidirectional(
                communication_configuration=0,
                certificate_client=b'\x30' + bytes(498) + b'\xAD',
                challenge_client=b'\xAA' + bytes(30) + b'\x44',
            )

        with self.assertRaises(InvalidResponseException):  # #4 only one byte length field
            self.udsclient.verify_certificate_unidirectional(
                communication_configuration=0,
                certificate_client=b'\x30' + bytes(498) + b'\xAD',
                challenge_client=b'\xAA' + bytes(30) + b'\x44',
            )

        with self.assertRaises(InvalidResponseException):  # #5 data smaller than length field
            self.udsclient.verify_certificate_unidirectional(
                communication_configuration=0,
                certificate_client=b'\x30' + bytes(498) + b'\xAD',
                challenge_client=b'\xAA' + bytes(30) + b'\x44',
            )

        with self.assertRaises(InvalidResponseException):  # #6 no algorithIndicator
            self.udsclient.request_challenge_for_authentication(
                communication_configuration=0,
                algorithm_indicator=b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00'
            )

        with self.assertRaises(InvalidResponseException):  # #7 small algorithIndicator
            self.udsclient.request_challenge_for_authentication(
                communication_configuration=0,
                algorithm_indicator=b'\x06' + bytes(9) + b'\x0A' + bytes(4) + b'\x00'
            )

        with self.assertRaises(InvalidResponseException):  # #8 Unknown Subfunction
            self.udsclient.deauthenticate()

    def test_bad_param(self) -> None:
        pass

    def _test_bad_param(self) -> None:
        with self.assertRaises(ValueError):
            self.udsclient.authentication(9)

        with self.assertRaises(ValueError):
            self.udsclient.verify_certificate_unidirectional(b'asdf', bytes(1), bytes(1))

        with self.assertRaises(ValueError):
            self.udsclient.verify_certificate_unidirectional(0x100, bytes(1), bytes(1))

        with self.assertRaises(ValueError):
            self.udsclient.verify_certificate_unidirectional(0, bytes(0x10000), bytes(1))

        with self.assertRaises(ValueError):
            self.udsclient.verify_certificate_unidirectional(1, 1, bytes(1))

        with self.assertRaises(ValueError):
            self.udsclient.request_challenge_for_authentication(communication_configuration=0,
                                                                algorithm_indicator=b'\x06' + bytes(9) + b'\x0A'
                                                                                    + bytes(4)
                                                                )

        with self.assertRaises(ValueError):
            self.udsclient.request_challenge_for_authentication(communication_configuration=0,
                                                                algorithm_indicator=b'\x06' + bytes(9) + b'\x0A'
                                                                                    + bytes(4) + b'\x00\x00'
                                                                )

        with self.assertRaises(ValueError):
            self.udsclient.request_challenge_for_authentication(communication_configuration=0,
                                                                algorithm_indicator=[0]*16
                                                                )

        with self.assertRaises(ValueError):
            self.udsclient.transmit_certificate(0x10000, bytes(1))
