from  udsoncan import Request, Response, SecurityLevel
from udsoncan.sessions import DefaultSession

class Server(object):
	def __init__(self, conn, config):
		self.conn = conn
		self.callbacks = {}
		self.security_levels = []
		self.config

	def attach_callback(self, service_cls, subfunction, callback):
		if service_cls not in self.callbacks:
			self.callbacks[service_cls] = {}
		
		self.callbacks[service_cls][subfunction] = callback

	def is_service_available(self, service, session, unlocked_seclvl):
		if session == DefaultSession:
			if service in [	DiagnosticSessionControl,
							ECUReset,
							TesterPresent,
							ResponseOnEvent,
							ReadDataByIdentifier,
							ReadMemoryByAddress,
							ReadScalingDataByIdentifier,
							DynamicallyDefineDataIdentifier,
							WriteDataByIdentifier,
							WriteMemoryByAddress,
							ClearDiagnosticInformation,
							ReadDTCInformation,
							RoutineControl]:
				return True

	def register_security_levels(self, levels):
		if levels is None:
			return

		if not isinstance(levels, list):
			levels = [levels]

		for level in levels:
			if not isinstance(level, SecurityLevel ):
				raise ValueError('%s is not an instance of SecurityLevel' % level)
		self.security_levels = levels


	def execute(self):
		while not self.conn.rxqueue.empty():
			payload = self.conn.rxqueue.get()

			if len(payload) == 0:
				continue

			servicecls = services.cls_from_request_id(payload[0])
			if len(payload) == 1:
				response = Response(service=servicecls, code=Response.Code.IncorrectMessageLegthOrInvalidFormat)
				self.conn.send(response.make_payload())
				continue

			if servicecls not in self.callbacks:
				response = Response(service=servicecls, code=Response.Code.ServiceNotSupported)
				self.conn.send(response.make_payload())
				continue

			subfunction = payload[1]
			if subfunction not in self.callbacks[servicecls]:
				response = Response(service=servicecls, code=Response.Code.SubFunctionNotSupported)
				self.conn.send(response.make_payload())
				continue

			try:
				pass
			except:
				pass

	def close(self):
		self.conn.close()
		self.conn=None





