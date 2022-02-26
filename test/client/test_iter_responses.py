
from queue import Empty

from test.ClientServerTest import ClientServerTest

class TestTterResponses(ClientServerTest):
    def __init__(self, *args, **kwargs):
        ClientServerTest.__init__(self, *args, **kwargs)

    def test_iter_responses_success(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x3E\x00")
        self.conn.fromuserqueue.put(b"\x7E\x00") # Positive response
        self.conn.fromuserqueue.put(b"\x7E\x00") # Positive response
        self.conn.fromuserqueue.put(b"\x7F\x3E\x78") # Response Pending
        self.conn.fromuserqueue.put(b"\x7F\x3E\x78") # Response Pending
        self.conn.fromuserqueue.put(b"\x7E\x00") # Positive response

        # Check that we received the request only once
        with self.assertRaises(Empty):
            self.conn.touserqueue.get(timeout=1)

    def _test_iter_responses_success(self):
        response = self.udsclient.tester_present()
        responses = self.udsclient.iter_responses(response)
        self.assertEqual(len(responses), 3)
        for res in responses:
            self.assertIsNotNone(res)
            self.assertIsNotNone(res.service_data)

    def test_iter_responses_error(self):
        request = self.conn.touserqueue.get(timeout=0.2)
        self.assertEqual(request, b"\x3E\x00")
        self.conn.fromuserqueue.put(b"\x7F\x3E\x10") # General Reject
        self.conn.fromuserqueue.put(b"\x7E\x00") # Positive response
        self.conn.fromuserqueue.put(b"\x7E\x00") # Positive response
        with self.assertRaises(Empty):
            # Check that we received the request only once
            self.conn.touserqueue.get(timeout=1)

    def _test_iter_responses_error(self):
        self.udsclient.set_config('exception_on_negative_response', False)
        responses = self.udsclient.iter_responses(self.udsclient.tester_present())
        self.assertEqual(len(responses), 3)
        for res in responses:
            self.assertIsNotNone(res)

        self.assertFalse(responses[0].positive)
        self.assertIsNotNone(responses[1].service_data)
        self.assertIsNotNone(responses[2].service_data)
