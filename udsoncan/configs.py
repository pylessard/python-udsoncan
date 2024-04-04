from udsoncan.typing import ClientConfig
from udsoncan import latest_standard
from typing import cast

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
    'data_identifiers': {},
    'input_output': {},
    'request_timeout': 10,
    'p2_timeout': 10,
    'p2_star_timeout': 10,
    'standard_version': latest_standard,  # 2006, 2013, 2020
    'use_server_timing': False,
    'extended_data_size': None
})
