from udsoncan import sessions, services, Request, Response, Connection
from udsoncan.server import Server


import time
conn = Connection('vcan0', rxid=0x456, txid=0x123)
with conn.open():
	while True:
		payload = conn.wait_frame(timeout=None)
		if payload is not None:
			print("Received: " + ''.join(['%02X' % b for b in payload]))
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
					response = Response(req.service, Response.Code.PositiveResponse, data=b"\x12\x34\x56\x78")
				elif req.subfunction == 4:
					if req.data == b"\xed\xcb\xa9\x87":
						response = Response(req.service, Response.Code.PositiveResponse)
					else:
						response = Response(req.service, Response.Code.InvalidKey)
				else:
					response = Response(req.service, Response.Code.SubFunctionNotSupported)
			## Tester present
			elif req.service == services.TesterPresent:
				response = Response(req.service, Response.Code.PositiveResponse)

			## Read Data By identifier
			elif req.service == services.ReadDataByIdentifier:

				if req.data == b"\x00\x01" :
					response = Response(req.service, Response.Code.PositiveResponse, data=b'\x12\x34')
				elif req.data == b"\x00\x02" :
					response = Response(req.service, Response.Code.PositiveResponse, data=b'\x56\x78')
				elif req.data == b"\x00\x03" :
					response = Response(req.service, Response.Code.PositiveResponse, data=b'\x9a\xbc')
				elif req.data == b"\x00\x01\x00\x02" :
					response = Response(req.service, Response.Code.PositiveResponse, data=b'\x12\x34\x56\x78')
				else :
					response = Response(req.service, Response.Code.RequestOutOfRange)
			## Read Data By identifier
			elif req.service == services.WriteDataByIdentifier:
				if req.data[0:2] in [b"\x00\x01", b"\x00\x02", b"\x00\x03"] :
					response = Response(req.service, Response.Code.PositiveResponse, req.data[0:2])
				else:
					response = Response(req.service, Response.Code.RequestOutOfRange)

			else:
				response = Response(req.service, Response.Code.ServiceNotSupported)
			
			if response.response_code != Response.Code.PositiveResponse or not req.suppress_positive_response:
				print("Sending: " + ''.join(['%02X' % b for b in response.get_payload()]))
				conn.send(response)
			else:
				print ("Suppressing positive response.")