from udsoncan.client import Client
from udsoncan import services
from udsoncan.exceptions import *

from test.ClientServerTest import ClientServerTest
from udsoncan import Dtc

class TestReportNumberOfDTCByStatusMask(ClientServerTest):	# Subfn = 0x1
	pass

class TestReportDTCByStatusMask(ClientServerTest):	# Subfn = 0x2
	
	def test_simple_success(self):
		request = self.conn.touserqueue.get(timeout=0.5)
		self.assertEqual(request, b"\x19\x02\x5A")
		self.conn.fromuserqueue.put(b"\x59\x02\xFB\x12\x34\x56\x20\x12\x34\x57\x60")	

	def _test_simple_success(self):
		response = self.udsclient.get_dtc_by_status_mask(0x5A)
		self.assertEqual(response.status_availability, 0xFB)

		self.assertEqual(len(response.dtcs), 2)

		self.assertEqual(response.dtcs[0].id, 0x123456)
		self.assertEqual(response.dtcs[0].status.get_byte(), b'\x20')
		self.assertEqual(response.dtcs[0].severity, Dtc.Severity.NotAvailable)

		self.assertEqual(response.dtcs[1].id, 0x123457)
		self.assertEqual(response.dtcs[1].status.get_byte(),b'\x60')
		self.assertEqual(response.dtcs[1].severity, Dtc.Severity.NotAvailable)


class TestReportDTCSnapshotIdentification(ClientServerTest):	# Subfn = 0x3
	pass

class TestReportDTCSnapshotRecordByDTCNumber(ClientServerTest):	# Subfn = 0x4
	pass

class TestReportDTCSnapshotRecordByRecordNumber(ClientServerTest):	# Subfn = 0x5
	pass

class TestReportDTCExtendedDataRecordByDTCNumber(ClientServerTest):	# Subfn = 0x6
	pass

class TestReportNumberOfDTCBySeverityMaskRecord(ClientServerTest):	# Subfn = 0x7
	pass

class TestReportDTCBySeverityMaskRecord(ClientServerTest):	# Subfn = 0x8
	pass

class TestReportSeverityInformationOfDTC(ClientServerTest):	# Subfn = 0x9
	pass

class TestReportSupportedDTC(ClientServerTest):	# Subfn =- 0xA
	pass

class TestReportFirstTestFailedDTC(ClientServerTest):	# Subfn = 0xB
	pass

class TestReportFirstConfirmedDTC(ClientServerTest):	# Subfn = 0xC
	pass

class TestReportMostRecentTestFailedDTC(ClientServerTest):	# Subfn = 0xD
	pass

class TestReportMostRecentConfirmedDTC(ClientServerTest):	# Subfn = 0xE
	pass

class TestReportMirrorMemoryDTCByStatusMask(ClientServerTest):	# Subfn = 0xF
	pass

class TestReportMirrorMemoryDTCExtendedDataRecordByDTCNumber(ClientServerTest):	# Subfn = 0x10
	pass

class TestReportNumberOfMirrorMemoryDTCByStatusMask(ClientServerTest):	# Subfn = 0x11
	pass

class TestReportNumberOfEmissionsRelatedOBDDTCByStatusMask(ClientServerTest):	# Subfn = 0x12
	pass

class TestReportEmissionsRelatedOBDDTCByStatusMask(ClientServerTest):	# Subfn = 0x13
	pass

class TestReportDTCFaultDetectionCounter(ClientServerTest):	# Subfn = 0x14
	pass

class TestReportDTCWithPermanentStatus(ClientServerTest):	# Subfn = 0x15
	pass
