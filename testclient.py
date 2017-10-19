from udsoncan import sessions, services, Request, Connection
from udsoncan.client import Client
from testconfig import client_config
import time

conn = Connection('vcan0', rxid=0x123, txid=0x456)

with Client(conn, request_timeout=1, config=client_config) as client:
	client.write_data_by_identifier(2,0x9999)
