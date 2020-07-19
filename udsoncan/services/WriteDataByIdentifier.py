from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class WriteDataByIdentifier(BaseService):
    _sid = 0x2E
    _use_subfunction = False

    supported_negative_response = [	 Response.Code.IncorrectMessageLengthOrInvalidFormat,
                                                    Response.Code.ConditionsNotCorrect,
                                                    Response.Code.RequestOutOfRange,
                                                    Response.Code.SecurityAccessDenied,
                                                    Response.Code.GeneralProgrammingFailure
                                                    ]

    @classmethod
    def make_request(cls, did, value, didconfig):
        """
        Generates a request for WriteDataByIdentifier

        :param did: The data identifier to write
        :type did: int

        :param value: Value given to the :ref:`DidCodec <DidCodec>`.encode method. If involved codec is defined with a pack string (default codec), multiple values may be passed with a tuple.
        :type value: object

        :param didconfig: Definition of DID codecs. Dictionary mapping a DID (int) to a valid :ref:`DidCodec <DidCodec>` class or pack/unpack string 
        :type didconfig: dict[int] = :ref:`DidCodec <DidCodec>`

        :raises ValueError: If parameters are out of range, missing or wrong type
        :raises ConfigError: If ``didlist`` contains a DID not defined in ``didconfig``
        """	

        from udsoncan import Request, DidCodec
        ServiceHelper.validate_int(did, min=0, max=0xFFFF, name='Data Identifier')
        req = Request(cls)
        didconfig = ServiceHelper.check_did_config(did, didconfig=didconfig)	# Make sure all DIDs are correctly defined in client config
        req.data = struct.pack('>H', did)	# encode DID number
        codec = DidCodec.from_config(didconfig[did])
        if codec.__class__ == DidCodec and isinstance(value, tuple):
            req.data += codec.encode(*value)    # Fixes issue #29
        else:
            req.data += codec.encode(value)

        return req

    @classmethod
    def interpret_response(cls, response):
        """
        Populates the response ``service_data`` property with an instance of :class:`WriteDataByIdentifier.ResponseData<udsoncan.services.WriteDataByIdentifier.ResponseData>`

        :param response: The received response to interpret
        :type response: :ref:`Response<Response>`

        :raises InvalidResponseException: If length of ``response.data`` is too short
        """			
        if len(response.data) < 2:
            raise InvalidResponseException(response, "Response must be at least 2 bytes long")

        response.service_data = cls.ResponseData()
        response.service_data.did_echo = struct.unpack(">H", response.data[0:2])[0]


    class ResponseData(BaseResponseData):
        """
        .. data:: did_echo

                The DID echoed back by the server
        """			
        def __init__(self):
            super().__init__(WriteDataByIdentifier)

            self.did_echo = None
