class TimeoutException(Exception):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

class NegativeResponseException(Exception):
	def __init__(self, response):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		args[0] = msg
		super().__init__(*args, **kwargs)

	def make_msg(self, response):
		return "%s service execution returned a negative response %s (%s)" % (response.service.__class__.__name__, response.response_code_name, response.response_code)

class InvalidResponseException(Exception):
	def __init__(self, service, *args, **kwargs):
		self.response = response
		msg = self.make_msg(response)
		if len(args) > 0 :
			msg += "\n"+args[0]
		args[0] = msg
		super().__init__(*args, **kwargs)

	def make_msg(self, response):
		return "%s service execution returned an invalid response." % (response.service.__class__.__name__)