from udsoncan.Request import Request
from udsoncan.Response import Response
from udsoncan import CommunicationType
from udsoncan.exceptions import *
from udsoncan.BaseService import BaseService, BaseSubfunction, BaseResponseData
from udsoncan.ResponseCode import ResponseCode
import udsoncan.tools as tools

from typing import cast, Union


class CommunicationControl(BaseService):
    _sid = 0x28

    class ControlType(BaseSubfunction):
        """
        CommunicationControl defined subfunctions
        """
        __pretty_name__ = 'control type'

        enableRxAndTx = 0
        enableRxAndDisableTx = 1
        disableRxAndEnableTx = 2
        disableRxAndTx = 3

    supported_negative_response = [ResponseCode.SubFunctionNotSupported,
                                   ResponseCode.IncorrectMessageLengthOrInvalidFormat,
                                   ResponseCode.ConditionsNotCorrect,
                                   ResponseCode.RequestOutOfRange
                                   ]

    class ResponseData(BaseResponseData):
        """
        .. data:: control_type_echo

                Request subfunction echoed back by the server
        """
        control_type_echo: int

        def __init__(self, control_type_echo: int):
            super().__init__(CommunicationControl)
            self.control_type_echo = control_type_echo

    class InterpretedResponse(Response):
        service_data: "CommunicationControl.ResponseData"

    @classmethod
    def normalize_communication_type(self, communication_type: Union[int, bytes, CommunicationType]) -> CommunicationType:
        if not isinstance(communication_type, CommunicationType) and not isinstance(communication_type, int) and not isinstance(communication_type, bytes):
            raise ValueError('communication_type must either be a CommunicationType object or an integer')

        if isinstance(communication_type, int) or isinstance(communication_type, bytes):
            communication_type = CommunicationType.from_byte(communication_type)

        return communication_type

    @classmethod
    def make_request(cls, control_type: int, communication_type: CommunicationType) -> Request:
        """
        Generates a request for CommunicationControl

        :param control_type: Service subfunction. Allowed values are from 0 to 0x7F
        :type control_type: int

        :param communication_type: The communication type requested.
        :type communication_type: :ref:`CommunicationType <CommunicationType>`, int, bytes

        :raises ValueError: If parameters are out of range, missing or wrong type
        """
        tools.validate_int(control_type, min=0, max=0x7F, name='Control type')

        communication_type = cls.normalize_communication_type(communication_type)
        request = Request(service=cls, subfunction=control_type)
        request.data = communication_type.get_byte()

        return request

    @classmethod
    def interpret_response(cls, response: Response) -> InterpretedResponse:
        """
        Populates the response ``service_data`` property with an instance of :class:`CommunicationControl.ResponseData<udsoncan.services.CommunicationControl.ResponseData>`

        :param response: The received response to interpret
        :type response: :ref:`Response<Response>`

        :raises InvalidResponseException: If length of ``response.data`` is too short
        """
        if response.data is None:
            raise InvalidResponseException(response, "No data in response")

        if len(response.data) < 1:
            raise InvalidResponseException(response, "Response data must be at least 1 byte")

        response.service_data = cls.ResponseData(
            control_type_echo=response.data[0]
        )

        return cast(CommunicationControl.InterpretedResponse, response)
