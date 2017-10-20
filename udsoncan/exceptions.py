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
		
		return "%s service execution returned a negative response %s (0x%x)" % (response.service.get_name(), response.code_name, response.code)

class InvalidResponseException(Exception):
	def __init__(self, response, *args, **kwargs):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response):
		servicename = response.service.get_name() if response.service is not None else ""
		return "%s service execution returned an invalid response." % (servicename)

class UnexpectedResponseException(Exception):
	def __init__(self, response, details="<No details given>", *args, **kwargs):
		self.response = response
		msg = self.make_msg(response, details)
		if len(args) > 0 :
			msg += "\n"+args[0]
		super().__init__(msg, *args, **kwargs)

	def make_msg(self, response, details):
		servicename = response.service.get_name() if response.service is not None else ""
		return "%s service execution returned a valid response, but unexpected. Details : %s " % (servicename, details)

