from udsoncan import services
import inspect
import struct

class Request:
	def __init__(self, service = None, subfunction = None, suppress_positive_response = False, data=None):
		if service is None:
			self.service = None
		elif isinstance(service, services.BaseService):
			self.service = service.__class__
		elif inspect.isclass(service) and issubclass(service, services.BaseService):
			self.service = service
		elif service is not None:
			raise ValueError("Given service must be a service class or instance")

		if not isinstance(suppress_positive_response, bool):
			raise ValueError("suppress_positive_response must be a boolean value")

		if subfunction is not None:
			if isinstance(subfunction, int):
				self.subfunction = subfunction
			else:
				raise ValueError("Given subfunction must be a valid integer")
		else:
			self.subfunction = None

		self.suppress_positive_response = suppress_positive_response
		
		if data is not None and not isinstance(data, bytes):
			raise ValueError("data must be a valid bytes object")

		self.data = data

	def get_payload(self):
		if not issubclass(self.service, services.BaseService):
			raise ValueError("Cannot generate a payload. Given service is not a subclass of BaseService")

		if self.service.use_subfunction() and not isinstance(self.subfunction, int):
			raise ValueError("Cannot generate a payload. Given subfunction is not a valid integer")

		requestid = self.service.request_id()	# Return the service ID used to make a client request
			
		payload = struct.pack("B", requestid)
		if self.service.use_subfunction():
			subfunction = self.subfunction
			if self.suppress_positive_response:
				subfunction |= 0x80
			payload += struct.pack("B", subfunction)

		if self.data is not None:
			 payload += self.data

		return payload

	@classmethod
	def from_payload(cls, payload):
		req = cls()

		if len(payload) >= 1:
			req.service = services.cls_from_request_id(payload[0])
			if req.service is not None:		# Invalid service ID will make service None
				offset = 0
				if req.service.use_subfunction():
					offset += 1
					if len(payload) >= offset+1: 
						req.subfunction = int(payload[1]) & 0x7F
						req.suppress_positive_response = True if payload[1] & 0x80 > 0 else False
				if len(payload) > offset+1:
					req.data = payload[offset+1:]
		return req

	def __repr__(self):
		suppress_positive_response = '[SuppressPosResponse] ' if self.suppress_positive_response else ''
		subfunction_name = '(subfunction=%d) ' % self.subfunction if self.service.use_subfunction() and self.subfunction is not None else ''
		bytesize = len(self.data) if self.data is not None else 0
		return '<Request: [%s] %s- %d data bytes %sat 0x%08x>' % (self.service.get_name(), subfunction_name, bytesize, suppress_positive_response, id(self))

	def __len__(self):
		try:
			return len(self.get_payload())
		except:
			return 0