from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *

class SecuredDataTransmission(BaseService):
	_sid = 0x84

	class Code:
		GeneralSecurityViolation 			= Response.Code.GeneralSecurityViolation			- 0x38
		SecuredModeRequested 				= Response.Code.SecuredModeRequested				- 0x38
		InsufficientProtection 				= Response.Code.InsufficientProtection				- 0x38
		TerminationWithSignatureRequested 	= Response.Code.TerminationWithSignatureRequested	- 0x38
		AccessDenied 						= Response.Code.AccessDenied						- 0x38
		VersionNotSupported 				= Response.Code.VersionNotSupported					- 0x38
		SecuredLinkNotSupported 			= Response.Code.SecuredLinkNotSupported				- 0x38
		CertificateNotAvailable 			= Response.Code.CertificateNotAvailable				- 0x38
		AuditTrailInformationNotAvailable 	= Response.Code.AuditTrailInformationNotAvailable	- 0x38

	supported_negative_response = [	Response.Code.SubFunctionNotSupported, 
							Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.GeneralSecurityViolation,
							Response.Code.SecuredModeRequested,
							Response.Code.InsufficientProtection,
							Response.Code.TerminationWithSignatureRequested,
							Response.Code.AccessDenied,
							Response.Code.VersionNotSupported,
							Response.Code.SecuredLinkNotSupported,
							Response.Code.CertificateNotAvailable,
							Response.Code.AuditTrailInformationNotAvailable
							]

	@classmethod
	def make_request(cls):
		raise NotImplementedError('Service is not implemented')

	@classmethod
	def interpret_response(cls, response):
		raise NotImplementedError('Service is not implemented')

	class ResponseData(BaseResponseData):	
		def __init__(self):
			super().__init__(SecuredDataTransmission)
