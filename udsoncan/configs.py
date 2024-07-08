from udsoncan.typing import ClientConfig
from udsoncan import latest_standard
from typing import cast
import udsoncan
from typing import Any
from udsoncan.exceptions import *

class HexCodec(udsoncan.DidCodec):
    hex_len: int 
    def __init__(self, hex_len: int):
        self.hex_len = hex_len

    def encode(self, string_hex: Any) -> bytes:
        if not isinstance(string_hex, str):
            raise ValueError('HexCodec requires hex for encoding')
        if len(string_hex) != self.hex_len:
            raise ValueError('Hex string must be %d characters long' % self.hex_len)
        
        try:
            byte_array = bytes.fromhex(string_hex)
        except ValueError as e:
            raise ValueError('Invalid hex string provided') from e

        return byte_array

    def decode(self, byte_array: bytes) -> Any:
        if not isinstance(byte_array, bytes):
            raise ValueError("HexCodec requires a byte array for decoding")
        if len(byte_array) != self.hex_len:
            raise ValueError(f"Byte array must be {self.hex_len} bytes long")

        return byte_array.hex()

    def __len__(self):
        return 8 


default_client_config: ClientConfig = cast(ClientConfig, {
    'exception_on_negative_response': False,
    'exception_on_invalid_response': False,
    'exception_on_unexpected_response': False,
    'security_algo': None,
    'security_algo_params': None,
    'tolerate_zero_padding': True,
    'ignore_all_zero_dtc': True,
    'dtc_snapshot_did_size': 2,		# Not specified in standard. 2 bytes matches other services format.
    'server_address_format': None,		# 8,16,24,32,40
    'server_memorysize_format': None,		# 8,16,24,32,40
    'data_identifiers': {
                            
    0xF180 : udsoncan.AsciiCodec(20),
    0xF181 : udsoncan.AsciiCodec(20),
    0xF184 : HexCodec(8),
    0xF186 : HexCodec(1),
    0xF18C : udsoncan.AsciiCodec(12),
    0xF193 : udsoncan.AsciiCodec(2),
    0xF190 : udsoncan.AsciiCodec(17),
    0xF195 : udsoncan.AsciiCodec(2),
    0x102 : HexCodec(2),     
    0x103 : HexCodec(2),          
    0x104 : HexCodec(2),  
    0x0111 : HexCodec(1),
    0x010F : HexCodec(1),
    0x0110: HexCodec(15),
    0x0100 : HexCodec(1),
    0x0101 : udsoncan.AsciiCodec(4),
    0x0105 : HexCodec(1),
    0x0106: udsoncan.AsciiCodec(33),
    0x0107 :udsoncan.AsciiCodec(32),
    0x0108 : udsoncan.AsciiCodec(32),
    0x0109 : udsoncan.AsciiCodec(64),
    0x010A: udsoncan.AsciiCodec(33),
    0x010B : udsoncan.AsciiCodec(33),
    0x010C : udsoncan.AsciiCodec(33),
    0x010D : udsoncan.AsciiCodec(33),
    0x010E : udsoncan.AsciiCodec(33)
    },
    'input_output': {},
    'request_timeout': 5,
    'p2_timeout': 5,
    'p2_star_timeout': 5,
    'standard_version': latest_standard,  # 2006, 2013, 2020
    'use_server_timing': False,
    'extended_data_size': None
})
