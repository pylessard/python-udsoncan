from udsoncan import sessions, services, Request, Connection
from udsoncan.client import Client
import time

conn = Connection('vcan0', rxid=0x123, txid=0x456)

with Client(conn, request_timeout=1) as client:
	client.unlock_security_access(3)
