from udsoncan import Response, Request, services
from udsoncan.exceptions import *
from udsoncan.configs import default_client_config

class Client:
	def __init__(self, conn, config=default_client_config, request_timeout = 1):
		self.conn = conn
		self.request_timeout = request_timeout
		self.config = config

	def __enter__(self):
		if not self.conn.is_open():
			self.conn.open()
		return self
	
	def __exit__(self, type, value, traceback):
		self.conn.close()

## 	DiagnosticSessionControl
	def change_session(self, newsession):
		service = services.DiagnosticSessionControl(newsession)
		req = Request(service)
		#No service params
		return self.send_request(req, timeout = self.request_timeout)

##  SecurityAccess
	def request_key(self, level):
		service = services.SecurityAccess(level, mode=services.SecurityAccess.Mode.RequestSeed)
		req = Request(service)
		return self.send_request(req, timeout = self.request_timeout)

	def send_key(self, level, key):
		service = services.SecurityAccess(level, mode=services.SecurityAccess.Mode.SendKey)
		req = Request(service)
		req.service_data = key
		return self.send_request(req, timeout = self.request_timeout)

	def unlock_security_access(self, level):
		if not callable(self.config['security_algo']):
			raise NotImplementedError("Client configuration does not provide a security algorithm")
		
		request_seed_response = self.request_key(level)
		seed = request_seed_response.service_data
		key = self.config['security_algo'].__call__(seed)
		self.send_key(level, key)




	def send_request(self, request, timeout=1, validate_response=True):
		self.conn.empty_rxqueue()
		self.conn.send(request)


		payload = self.conn.wait_frame(timeout=timeout, exception=True)
		response = Response.from_payload(payload)
		if not response.valid:
			raise InvalidResponseException(service)

		if not response.positive:
			raise NegativeResponseException(response)

		return response

