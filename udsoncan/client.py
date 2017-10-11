from udsoncan import Response, Request, services
from udsoncan.exceptions import *

class Client:
	def __init__(self, conn, request_timeout = 1):
		self.conn = conn
		self.request_timeout = request_timeout

	def change_session(self, newsession):
		service = services.DiagnosticSessionControl(newsession)
		req = Request(service)
		#No service params
		self.send_request(req, timeout = self.request_timeout)


	def send_request(self, request, timeout=1, validate_response=True):
		self.conn.empty_rxqueue()
		self.conn.send(request)

		payload = self.conn.wait_frame(timeout=timeout, exception=True)
		response = Response.from_payload(payload)
		if not response.valid:
			raise InvalidResponseException(service)

		if not response.positive:
			raise NegativeResponseException(response)

