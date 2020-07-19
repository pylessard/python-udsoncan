from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class TesterPresent(BaseService):
    _sid = 0x3E

    supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
                                                    Response.Code.IncorrectMessageLengthOrInvalidFormat
                                                    ]	

    @classmethod
    def make_request(cls):
        """
        Generates a request for TesterPresent
        """		
        from udsoncan import Request
        return Request(service=cls, subfunction=0)

    @classmethod
    def interpret_response(cls, response):
        """
        Populates the response ``service_data`` property with an instance of :class:`TesterPresent.ResponseData<udsoncan.services.TesterPresent.ResponseData>`

        :param response: The received response to interpret
        :type response: :ref:`Response<Response>`

        :raises InvalidResponseException: If length of ``response.data`` is too short
        """		
        if  len(response.data) < 1:
            raise InvalidResponseException(response, "Response data must be at least 1 bytes")

        response.service_data = cls.ResponseData()
        response.service_data.subfunction_echo = response.data[0]

    class ResponseData(BaseResponseData):
        """
        .. data:: subfunction_echo

                Requests subfunction echoed back by the server. This value should always be 0
        """		
        def __init__(self):
            super().__init__(TesterPresent)
            self.subfunction_echo = None
