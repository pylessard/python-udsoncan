from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ResponseOnEvent(BaseService):
    _sid = 0x86

    supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
                                                    Response.Code.IncorrectMessageLengthOrInvalidFormat,
                                                    Response.Code.ConditionsNotCorrect,
                                                    Response.Code.RequestOutOfRange
                                                    ]

    @classmethod
    def make_request(cls):
        raise NotImplementedError('Service is not implemented')

    @classmethod
    def interpret_response(cls, response):
        raise NotImplementedError('Service is not implemented')

    class ResponseData(BaseResponseData):	
        def __init__(self):
            super().__init__(ResponseOnEvent)
