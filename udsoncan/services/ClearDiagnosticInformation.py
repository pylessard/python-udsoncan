from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
from udsoncan.configs import latest_standard
import struct

class ClearDiagnosticInformation(BaseService):
    _sid = 0x14
    _use_subfunction = False
    _no_response_data = True

    supported_negative_response = [	 Response.Code.IncorrectMessageLengthOrInvalidFormat,
                                                    Response.Code.ConditionsNotCorrect,
                                                    Response.Code.RequestOutOfRange
                                                    ]

    @classmethod
    def make_request(cls, group=0xFFFFFF, memory_selection=None, standard_version = latest_standard):
        """
        Generates a request for ClearDiagnosticInformation

        :param group: DTC mask ranging from 0 to 0xFFFFFF. 0xFFFFFF means all DTCs
        :type group: int

        :raises ValueError: If parameters are out of range, missing or wrong type
        """		
        from udsoncan import Request
        ServiceHelper.validate_int(group, min=0, max=0xFFFFFF, name='Group of DTC')
        request = Request(service=cls)
        hb = (group >> 16) & 0xFF
        mb = (group >> 8) & 0xFF
        lb = (group >> 0) & 0xFF 
        request.data = struct.pack("BBB", hb,mb,lb)

        # Introduced in ISO-14229-1:2020
        if memory_selection is not None:
            if standard_version < 2020:
                raise NotImplementedError('ClearDiagnosticInformation with Memory Selection is only possible with 2020 version of the standard or above.')

            ServiceHelper.validate_int(memory_selection, min=0, max=0xFF, name='Memory Selection')
            request.data += struct.pack("B", memory_selection)
        return request

    @classmethod
    def interpret_response(cls, response):
        """
        Populates the response ``service_data`` property with an instance of :class:`ClearDiagnosticInformation.ResponseData<udsoncan.services.ClearDiagnosticInformation.ResponseData>`

        :param response: The received response to interpret
        :type response: :ref:`Response<Response>`
        """		
        response.service_data = cls.ResponseData()

    class ResponseData(BaseResponseData):
        """
        Empty object
        """		
        def __init__(self):
            super().__init__(ClearDiagnosticInformation)
