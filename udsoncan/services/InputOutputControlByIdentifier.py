from . import BaseService, BaseSubfunction
from udsoncan.Response import Response
from udsoncan.exceptions import *

class InputOutputControlByIdentifier(BaseService):
	_sid = 0x2F
	_use_subfunction = False

	#As defined by ISO-14229:2006, Annex E
	class ControlParam(BaseSubfunction):
		__pretty_name__ = 'control parameter'

		returnControlToECU = 0
		resetToDefault = 1
		freezeCurrentState = 2
		shortTermAdjustment = 3

	supported_negative_response = [	 Response.Code.IncorrectMessageLegthOrInvalidFormat,
							Response.Code.ConditionsNotCorrect,
							Response.Code.RequestOutOfRange,
							Response.Code.SecurityAccessDenied
							]

	def __init__(self, did, control_param=None, values=None, masks=None):
		from udsoncan import IOValues, IOMasks
		if not isinstance(did, int):
			raise ValueError("did  must be a valid integer")

		if did < 0 or did > 0xFFFF:
			raise ValueError('did must either be an integer between 0 and 0xFFFF. %d given' % did)
	

		if control_param is not None:
			if not isinstance(control_param, int):
				raise ValueError("control_param  must be a valid integer")

			if control_param < 0 or control_param > 3:
				raise ValueError('control_param must either be returnControlToECU(0), resetToDefault(1), freezeCurrentState(2), shortTermAdjustment(3). %d given.' % control_param)
		
		if values is not None:
			if isinstance(values, list):
				values = IOValues(*values)
			if isinstance(values, dict):
				values = IOValues(**values)

			if not isinstance(values, IOValues):
				raise ValueError("values must be an instance of IOValues")

		if masks is not None:
			if isinstance(masks, list):
				masks = IOMasks(*masks)
			if isinstance(masks, dict):
				masks = IOMasks(**masks)

			if not isinstance(masks, IOMasks) and not isinstance(masks, bool):
				raise ValueError("masks must be an instance of IOMask or a boolean value")

		if values is None and masks is not None:
			raise ValueError('An IOValue must be given if a IOMask is provided.')


		self.did = did
		self.control_param = control_param
		self.values=values;
		self.masks=masks