from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class ReadDTCInformation(BaseService):
	_sid = 0x19

	supported_negative_response = [	 Response.Code.SubFunctionNotSupported,
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.RequestOutOfRange
							]

	class Subfunction(BaseSubfunction):
		__pretty_name__ = 'subfunction'

		reportNumberOfDTCByStatusMask = 1
		reportDTCByStatusMask = 2
		reportDTCSnapshotIdentification = 3
		reportDTCSnapshotRecordByDTCNumber = 4
		reportDTCSnapshotRecordByRecordNumber = 5
		reportDTCExtendedDataRecordByDTCNumber = 6
		reportNumberOfDTCBySeverityMaskRecord = 7
		reportDTCBySeverityMaskRecord = 8
		reportSeverityInformationOfDTC = 9
		reportSupportedDTCs = 0xA
		reportFirstTestFailedDTC = 0xB
		reportFirstConfirmedDTC = 0xC
		reportMostRecentTestFailedDTC = 0xD
		reportMostRecentConfirmedDTC = 0xE
		reportMirrorMemoryDTCByStatusMask = 0xF
		reportMirrorMemoryDTCExtendedDataRecordByDTCNumber = 0x10
		reportNumberOfMirrorMemoryDTCByStatusMask = 0x11
		reportNumberOfEmissionsRelatedOBDDTCByStatusMask = 0x12
		reportEmissionsRelatedOBDDTCByStatusMask = 0x13
		reportDTCFaultDetectionCounter = 0x14
		reportDTCWithPermanentStatus = 0x15





	def __init__(self, subfunction):
		if not isinstance(subfunction, int):
			raise ValueError('subfunction must be an integer')

		if subfunction < 1 or subfunction > 0x15:
			raise ValueError('subfunction 0x%02x is not a supported subfunction ID. Value must be between 0x01 and 0x15' % subfunction)

		self.subfunction = subfunction

	def subfunction_id(self):
		return self.subfunction