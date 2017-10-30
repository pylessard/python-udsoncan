from udsoncan import services, Request, Connection
from udsoncan.client import Client
from testconfig import client_config

conn = Connection('vcan0', rxid=0x123, txid=0x456)

with Client(conn, request_timeout=1, config=client_config) as client:
	client.ecu_reset(services.ECUReset.enableRapidPowerShutDown, 1)
