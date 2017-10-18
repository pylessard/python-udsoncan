import inspect
def service_name(service):
	if inspect.isclass(service):
		return service.__name__
	else:
		return service.__class__.__name__

class TimeoutException(Exception):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class NegativeResponseException(Exception):
	def __init__(self, response, *args, **kwargs):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response):
		return "%s service execution returned a negative response %s (0x%x)" % (service_name(response.service), response.response_code_name, response.response_code)

class InvalidResponseException(Exception):
	def __init__(self, service, *args, **kwargs):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response):
		return "%s service execution returned an invalid response." % (service_name(response.service))