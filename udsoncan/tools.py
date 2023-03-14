from udsoncan.exceptions import ConfigError
from udsoncan.BaseService import BaseService
from copy import copy

from udsoncan.typing import IOConfigEntry

from typing import Any, Union, List, Dict, Type, Optional


def validate_int(value: Any, min: int = 0, max: int = 0xFF, name: str = 'value'):
    if not isinstance(value, int):
        raise ValueError("%s must be a valid integer" % (name))
    if value < min or value > max:
        raise ValueError("%s must be an integer between 0x%X and 0x%X" % (name, min, max))


# Make sure that the actual client configuration contains valid definitions for given Input/Output Data Identifiers
def check_io_config(didlist: Union[int, List[int]], ioconfig: Dict[Any, Any]) -> Dict[int, IOConfigEntry]:
    didlist = [didlist] if not isinstance(didlist, list) else didlist
    ioconfig = copy(ioconfig)
    if 'input_output' in ioconfig:
        ioconfig = ioconfig['input_output']

    if not isinstance(ioconfig, dict):
        raise ConfigError('input_output', msg='Configuration of Input/Output section must be a dict.')

    for did in didlist:
        if did not in ioconfig:
            raise ConfigError(key=did, msg='Actual Input/Output configuration contains no definition for data identifier 0x%04x' % did)
        if isinstance(ioconfig[did], dict):  # IO Control services has that concept of composite DID. We define them with dicts.
            if 'codec'not in ioconfig[did]:
                raise ConfigError('codec', msg='Configuration for Input/Output identifier 0x%04x is missing a codec')

            if 'mask' in ioconfig[did]:
                mask_def = ioconfig[did]['mask']
                for mask_name in mask_def:
                    if not isinstance(mask_def[mask_name], int):
                        raise ValueError('In Input/Output configuration for did 0x%04x, mask "%s" is not an integer' % (did, mask_name))

                    if mask_def[mask_name] < 0:
                        raise ValueError('In Input/Output configuration for did 0x%04x, mask "%s" is not a positive integer' % (did, mask_name))

            if 'mask_size' in ioconfig[did]:
                if not isinstance(ioconfig[did]['mask_size'], int):
                    raise ValueError('mask_size in Input/Output configuration for did 0x%04x must be a valid integer' % (did))

                if ioconfig[did]['mask_size'] < 0:
                    raise ValueError('mask_size in Input/Output configuration for did 0x%04x must be greater than 0' % (did))

                if 'mask' in ioconfig[did]:
                    mask_def = ioconfig[did]['mask']
                    for mask_name in mask_def:
                        if mask_def[mask_name] > 2**(ioconfig[did]['mask_size'] * 8) - 1:
                            raise ValueError(
                                'In Input/Output configuration for did 0x%04x, mask "%s" cannot fit in %d bytes (defined by mask_size)' % (did, mask_name, ioconfig[did]['mask_size']))

        else:
            ioconfig[did] = {
                'codec': ioconfig[did]
            }

    return ioconfig


def cls_from_request_id(given_id: int) -> Optional[Type[BaseService]]:
    return BaseService.from_request_id(given_id)


def is_valid_service(service_cls: Type) -> bool:
    return issubclass(service_cls, BaseService)
