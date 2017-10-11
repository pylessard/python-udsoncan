from udsoncan import sessions, services, Request, Response, Connection
from udsoncan.server import Server


import time
server_conn = Connection('vcan0', 0x456, 0x123)
server_conn.open()
try:
	payload = server_conn.wait_frame(timeout=None)
	print("Got Payload : " + str(payload))
	if payload is not None:
		req = Request.from_payload(payload)
		if req.service == services.DiagnosticSessionControl:
			if sessions.from_id(req.subfunction) == sessions.ExtendedDiagnosticSession:
				response = Response(req.service, Response.Code.PositiveResponse)
			else:
				response = Response(req.service, Response.Code.SubFunctionNotSupported)
		else:
			response = Response(req.service, Response.Code.ServiceNotSupported)
		server_conn.send(response)
except:
	server_conn.close()
	raise
server_conn.close()