from udsoncan import sessions, services, Request, Connection
from udsoncan.client import Client

import time
client_conn = Connection('vcan0', 0x123, 0x456)
client_conn.open()

client = Client(client_conn, request_timeout=5)

try:
	client.change_session(sessions.ExtendedDiagnosticSession)

except:
	client_conn.close()
	raise
client_conn.close()