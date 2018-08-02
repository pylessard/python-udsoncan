import inspect
def service_name(service):
	if inspect.isclass(service):
		return service.__name__
	else:
		return service.__class__.__name__

class TimeoutException(Exception):
	"""
	Simple extension of ``Exception`` with no additional property. Raised when a timeout in the communication happens.
	"""
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class NegativeResponseException(Exception):
	"""
	Raised when the server returns a negative response (response code starting by 0x7F).
	The response that triggered the exception is available in ``e.response``

	:param response: The response that triggered the exception
	:type response: :ref:`Response<Response>`
	"""
	def __init__(self, response, *args, **kwargs):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response):
		
		return "%s service execution returned a negative response %s (0x%x)" % (response.service.get_name(), response.code_name, response.code)

class InvalidResponseException(Exception):
	"""
	Raised when a service fails to decode a server response data. A bad message length or a value that is out of range may both be valid causes.
	The response that triggered the exception is available in ``e.response``

	:param response: The response that triggered the exception
	:type response: :ref:`Response<Response>`
	"""

	def __init__(self, response, *args, **kwargs):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response):
		servicename = response.service.get_name() if response.service is not None else ""
		return "%s service execution returned an invalid response. Reason : %s" % (servicename, response.invalid_reason)

class UnexpectedResponseException(Exception):
	"""
	Raised when the client receives a valid response but considers the one received to not be the expected response.
	The response that triggered the exception is available in ``e.response``

	:param response: The response that triggered the exception
	:type response: :ref:`Response<Response>`

	:param details: Additional details about the error
	:type details: string
	"""
	def __init__(self, response, details="<No details given>", *args, **kwargs):
		self.response = response
		msg = self.make_msg(response, details)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response, details):
		servicename = response.service.get_name() if response.service is not None else ""
		return "service execution returned a valid response for service %s, but unexpected. Details : %s " % (servicename, details)

class ConfigError(Exception):
	"""
	Raised when a bad configuration element is encountered.
	
	:param key: The configuration key that failed to resolve properly
	:type key: object

	"""
	def __init__(self, key, msg="<No details given>", *args, **kwargs):
		self.key=key
		super().__init__(msg, *args, **kwargs)
