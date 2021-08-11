from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class DynamicallyDefineDataIdentifier(BaseService):
    _sid = 0x2C

    supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
                                                    Response.Code.IncorrectMessageLengthOrInvalidFormat,
                                                    Response.Code.ConditionsNotCorrect,
                                                    Response.Code.RequestOutOfRange
                                                    ]

    class Subfunction(BaseSubfunction):
        """
        DynamicallyDefineDataIdentifier defined subfunctions
        """     
        __pretty_name__ = 'subfunction' 

        defineByIdentifier = 1
        defineByMemoryAddress = 2
        clearDynamicallyDefinedDataIdentifier = 3

    @classmethod
    def make_request(cls, subfunction, did=None, diddef = None):
        """
        Generates a request for DynamicallyDefineDataIdentifier

        :param subfunction: Service subfunction. Allowed values are from 1 to 3
        :type subfunction: int

        :param did: The Data Identifier to define. Values from 0x0000 to 0xFFFF
        :type did: int

        :param diddef: Definition of the DID. Either by source DID or memory address. This parameter is only needed with subfunctions defineByIdentifie (1)` and defineByMemoryAddress (2)
        :type diddef: :ref:`DynamicDidDefinition<DynamicDidDefinition>`

        :raises ValueError: If parameters are out of range, missing or wrong type
        """         
        from udsoncan import Request, DynamicDidDefinition
        ServiceHelper.validate_int(subfunction, min=1, max=3, name='Subfunction')
        req = Request(service=cls, subfunction=subfunction)
        
        if subfunction in [cls.Subfunction.defineByIdentifier, cls.Subfunction.defineByMemoryAddress]:
            if not isinstance(diddef, DynamicDidDefinition):
                raise ValueError('A DynamicDidDefinition must be given to define a dynamic did with subfunction %d' % (subfunction))

            if did is None:
                raise ValueError('A DID number must be given with subfunction %d' % (subfunction))                

        if did is not None:
            ServiceHelper.validate_int(did, min=0, max=0xFFFF, name='DID number')

        if subfunction in [cls.Subfunction.defineByIdentifier, cls.Subfunction.defineByMemoryAddress]:
            if diddef is None:
                raise ValueError('DynamicDidDefinition must be given for this subfunction')

            diddef_entries = diddef.get()
            if len(diddef_entries) == 0:
                raise ValueError('DynamicDidDefinition object must have at least one DID specification')
            req.data = struct.pack('>H', did)

        if subfunction == cls.Subfunction.defineByIdentifier:
            if not diddef.is_by_source_did():
                raise ValueError("DynamicDidDefinition must be defined by source DID when used with subfunction 'defineByIdentifier'")
            for entry in diddef_entries:
                req.data += struct.pack('>HBB', entry.source_did, entry.position, entry.memorysize)
        
        elif subfunction == cls.Subfunction.defineByMemoryAddress:
            if not diddef.is_by_memory_address():
                raise ValueError("DynamicDidDefinition must be defined by memory address when used with subfunction 'defineByMemoryAddress'")

            req.data += diddef.get_alfid().get_byte()
            for entry in diddef_entries:
                req.data += entry.memloc.get_address_bytes()
                req.data += entry.memloc.get_memorysize_bytes()

        elif subfunction == cls.Subfunction.clearDynamicallyDefinedDataIdentifier:
            if did is not None:
                req.data = struct.pack('>H', did)


        return req

    @classmethod
    def interpret_response(cls, response):
        """
        Populates the response ``service_data`` property with an instance of :class:`DynamicallyDefineDataIdentifier.ResponseData<udsoncan.services.DynamicallyDefineDataIdentifier.ResponseData>`

        :param response: The received response to interpret
        :type response: :ref:`Response<Response>`

        :raises InvalidResponseException: If length of ``response.data`` is too short
        """

        if len(response.data) < 1:
            raise InvalidResponseException(response, "Response data must be at least 1 bytes") 
        
        response.service_data = cls.ResponseData()
        response.service_data.subfunction_echo = int(response.data[0])

        if response.service_data.subfunction_echo in [cls.Subfunction.defineByIdentifier, cls.Subfunction.defineByMemoryAddress]:
            if len(response.data) < 3:
                raise InvalidResponseException(response, "Missing or incomplete DID echo in response")

        if len(response.data) >= 3:
            response.service_data.did_echo = struct.unpack('>H', response.data[1:3])[0]


    class ResponseData(BaseResponseData):	
        def __init__(self):
            super().__init__(DynamicallyDefineDataIdentifier)
            self.subfunction_echo = None
            self.did_echo = None
