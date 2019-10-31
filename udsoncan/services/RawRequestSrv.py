from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct






class RawRequestSrv(BaseService):
    _sid = None
    _use_subfunction = False


    supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
                                                    Response.Code.ConditionsNotCorrect,
                                                    Response.Code.RequestOutOfRange,
                                                    Response.Code.SecurityAccessDenied
                                                    ]

    @classmethod
    def make_request(cls, rawcmd):
        """
        Generates a request for ReadDataByIdentifier

        :param rawcmd: the raw data without length information
        :type rawcmd: hex str

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises ConfigError: If didlist contains a DID not defined in didconfig
        """
        from udsoncan import Request
        length = len(rawcmd)
        if length % 2 or length > 255:
            raise ValueError
        cls._sid = int(rawcmd[:2], 16)
        req = Request(cls, data=bytes.fromhex(rawcmd), raw_request = True)

        return req

    def get_payload(self, suppress_positive_response=None):
        return self.data

    @classmethod
    def interpret_response(cls, response,tolerate_zero_padding=True):
        """
        Populates the response ``service_data`` property with an instance of :class:`ReadDataByIdentifier.ResponseData<udsoncan.services.ReadDataByIdentifier.ResponseData>`

        :param response: The received response to interpret
        :type response: :ref:`Response<Response>`


        :param tolerate_zero_padding: Ignore trailing zeros in the response data avoiding raising false :class:`InvalidResponseException<udsoncan.exceptions.InvalidResponseException>`.
        :type tolerate_zero_padding: bool

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises ConfigError: If ``didlist`` parameter or response contains a DID not defined in ``didconfig``.
        :raises InvalidResponseException: If response data is incomplete or if DID data does not match codec length.
        """	
        from udsoncan import DidCodec


        response.service_data = cls.ResponseData()
        response.service_data.values = {}

        # Parsing algorithm to extract DID value
        offset = 0

        return response

    class ResponseData(BaseResponseData):
        """
        .. data:: values

                Dictionary mapping the DID (int) with the value returned by the associated :ref:`DidCodec<DidCodec>`.decode method
        """				
        def __init__(self):
            super().__init__(ReadDataByIdentifier)

            self.values = None

