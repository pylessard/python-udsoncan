def test_algo(seed):
	key = bytearray(seed)
	for i in range(len(key)):
		key[i] ^= 0xFF	
	return key

default_client_config  = {
	'security_algo' : test_algo
}