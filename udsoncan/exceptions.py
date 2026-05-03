__all__ = [
    'TimeoutException',
    'NegativeResponseException',
    'InvalidResponseException',
    'UnexpectedResponseException',
    'ConfigError',
    'SecurityAccessDeniedException'
]
from udsoncan.Response import Response
from typing import Any


class TimeoutException(Exception):
    """
    Simple extension of ``Exception`` with no additional property. Raised when a timeout in the communication happens.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NegativeResponseException(Exception):
    """
    Raised when the server returns a negative response (response code starting by 0x7F).
    The response that triggered the exception is available in ``e.response``

    :param response: The response that triggered the exception
    :type response: :ref:`Response<Response>`
    """
    response: Response

    def __init__(self, response: Response, *args, **kwargs):
        self.response = response
        msg = self.make_msg(response)
        if len(args) > 0:
            msg += " " + str(args[0])
            args = tuple(list(args)[1:])
        super().__init__(msg, *args, **kwargs)

    def make_msg(self, response: Response):
        servicename = response.service.get_name() + " " if response.service is not None else ""
        codestr = ""
        if response.code is not None:
            codestr = " (0x%x)" % response.code
        return "%sservice execution returned a negative response %s%s" % (servicename, response.code_name, codestr)


class InvalidResponseException(Exception):
    """
    Raised when a service fails to decode a server response data. A bad message length or a value that is out of range may both be valid causes.
    The response that triggered the exception is available in ``e.response``

    :param response: The response that triggered the exception
    :type response: :ref:`Response<Response>`
    """
    response: Response

    def __init__(self, response, *args, **kwargs):
        self.response = response
        msg = self.make_msg(response)
        if len(args) > 0:
            msg += " " + str(args[0])
            args = tuple(list(args)[1:])
        super().__init__(msg, *args, **kwargs)

    def make_msg(self, response: Response):
        servicename = response.service.get_name() + " " if response.service is not None else ""
        reason = "" if response.valid else " Reason : %s" % (response.invalid_reason)
        return "%sservice execution returned an invalid response.%s" % (servicename, reason)


class UnexpectedResponseException(Exception):
    """
    Raised when the client receives a valid response but considers the one received to not be the expected response.
    The response that triggered the exception is available in ``e.response``

    :param response: The response that triggered the exception
    :type response: :ref:`Response<Response>`

    :param details: Additional details about the error
    :type details: string
    """
    response: Response

    def __init__(self, response: Response, details="<No details given>", *args, **kwargs):
        self.response = response
        msg = self.make_msg(response, details)
        if len(args) > 0:
            msg += " " + str(args[0])
            args = tuple(list(args)[1:])
        super().__init__(msg, *args, **kwargs)

    def make_msg(self, response: Response, details: str):
        servicename = response.service.get_name() + " " if response.service is not None else ""
        return "%sservice execution returned a valid response but unexpected. Details : %s " % (servicename, details)


class ConfigError(Exception):
    """
    Raised when a bad configuration element is encountered.

    :param key: The configuration key that failed to resolve properly
    :type key: object

    """
    key: Any

    def __init__(self, key: Any, msg="<No details given>", *args, **kwargs):
        self.key = key
        super().__init__(msg, *args, **kwargs)


class SecurityAccessDeniedException(Exception):
    """
    Raised when the client attempts to access a protected service, DID, or routine
    without having unlocked the required security level.

    :param required_level: The security level that is required but not unlocked
    :type required_level: int

    :param resource_type: The type of resource being accessed (service, did, routine)
    :type resource_type: str

    :param resource_id: The identifier of the resource being accessed
    :type resource_id: int

    """
    required_level: int
    resource_type: str
    resource_id: int

    def __init__(self, required_level: int, resource_type: str, resource_id: int, *args, **kwargs):
        self.required_level = required_level
        self.resource_type = resource_type
        self.resource_id = resource_id
        msg = "Security access denied: Required level 0x%02x not unlocked for %s 0x%04x" % (
            required_level, resource_type, resource_id
        )
        if len(args) > 0:
            msg += " " + str(args[0])
            args = tuple(list(args)[1:])
        super().__init__(msg, *args, **kwargs)
