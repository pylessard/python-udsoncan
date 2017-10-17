from udsoncan import sessions, services, Request, Response, Connection
from udsoncan.server import Server


import time
conn = Connection('vcan0', rxid=0x456, txid=0x123)
with conn.open():
	while True:
		payload = conn.wait_frame(timeout=None)
		if payload is not None:
			print("Got Payload : " + str(payload))
			req = Request.from_payload(payload)
			response = Response(req.service, Response.Code.GeneralReject)

			## DiagnosticSessionControl
			if req.service == services.DiagnosticSessionControl:
				if sessions.from_id(req.subfunction) == sessions.ExtendedDiagnosticSession:
					response = Response(req.service, Response.Code.PositiveResponse)
				else:
					response = Response(req.service, Response.Code.SubFunctionNotSupported)
			
			## SecurityAccess
			elif req.service == services.SecurityAccess:
				if req.subfunction == 3:
					response = Response(req.service, Response.Code.PositiveResponse, service_data=b"\x12\x34\x56\x78")
				elif req.subfunction == 4:
					if req.service_data == b"\xed\xcb\xa9\x87":
						response = Response(req.service, Response.Code.PositiveResponse)
					else:
						response = Response(req.service, Response.Code.SecurityAccessDenied)
				else:
					response = Response(req.service, Response.Code.SubFunctionNotSupported)

			else:
				response = Response(req.service, Response.Code.ServiceNotSupported)
			
			if response.response_code != Response.Code.PositiveResponse or not req.suppress_positive_response:
				conn.send(response)
			else:
				print ("Suppressing positive response.")