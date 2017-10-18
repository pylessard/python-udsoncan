from udsoncan import sessions, services, Request, Connection
from udsoncan.client import Client
from testconfig import client_config
import time

conn = Connection('vcan0', rxid=0x123, txid=0x456)

with Client(conn, request_timeout=1, config=client_config) as client:
	#client.unlock_security_access(3)
	print(client.read_data_by_identifier([1,2]))
