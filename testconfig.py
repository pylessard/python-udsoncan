import struct
from udsoncan import DidCodec

def test_algo(seed):
	key = bytearray(seed)
	for i in range(len(key)):
		key[i] ^= 0xFF	
	return key

class MyDidCodec(DidCodec):
	def encode(self, did_value):
		return struct.pack('B', did_value+1)

	def decode(self, did_payload):
		return struct.unpack('B', did_payload)[0] - 1

	def __len__(self):
		return 1

client_config  = {
	'security_algo' : test_algo,
	'data_identifiers' : {
		1 : '>H',
		2 : '<H',
		3 : MyDidCodec
	}
}