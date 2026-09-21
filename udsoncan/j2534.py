from enum import Enum
from ctypes import Structure, WINFUNCTYPE, POINTER, cdll, c_char, c_long, c_void_p, c_ubyte, c_ulong, byref  # type: ignore


class Error_ID(Enum):
    ERR_SUCCESS = 0x00
    STATUS_NOERROR = 0x00
    ERR_NOT_SUPPORTED = 0x01
    ERR_INVALID_CHANNEL_ID = 0x02
    ERR_INVALID_PROTOCOL_ID = 0x03
    ERR_NULL_PARAMETER = 0x04
    ERR_INVALID_IOCTL_VALUE = 0x05
    ERR_INVALID_FLAGS = 0x06
    ERR_FAILED = 0x07
    ERR_DEVICE_NOT_CONNECTED = 0x08
    ERR_TIMEOUT = 0x09
    ERR_INVALID_MSG = 0x0A
    ERR_INVALID_TIME_INTERVAL = 0x0B
    ERR_EXCEEDED_LIMIT = 0x0C
    ERR_INVALID_MSG_ID = 0x0D
    ERR_DEVICE_IN_USE = 0x0E
    ERR_INVALID_IOCTL_ID = 0x0F
    ERR_BUFFER_EMPTY = 0x10
    ERR_BUFFER_FULL = 0x11
    ERR_BUFFER_OVERFLOW = 0x12
    ERR_PIN_INVALID = 0x13
    ERR_CHANNEL_IN_USE = 0x14
    ERR_MSG_PROTOCOL_ID = 0x15
    ERR_INVALID_FILTER_ID = 0x16
    ERR_NO_FLOW_CONTROL = 0x17
    ERR_NOT_UNIQUE = 0x18
    ERR_INVALID_BAUDRATE = 0x19
    ERR_INVALID_DEVICE_ID = 0x1A


class Protocol_ID(Enum):
    J1850VPW         = 1
    J1850PWM         = 2
    ISO9141          = 3
    ISO14230         = 4
    CAN              = 5
    ISO15765         = 6
    SCI_A_ENGINE     = 7  # OP2.0: Not supported
    SCI_A_TRANS      = 8  # OP2.0: Not supported
    SCI_B_ENGINE     = 9  # OP2.0: Not supported
    SCI_B_TRANS      = 10 # OP2.0: Not supported

    J1850VPW_PS      = 0x8000
    J1850PWM_PS      = 0x8001
    ISO9141_PS       = 0x8002
    ISO14230_PS      = 0x8003
    CAN_PS           = 0x8004
    ISO15765_PS      = 0x8005
    J2610_PS         = 0x8006
    SW_ISO15765_PS   = 0x8007
    SW_CAN_PS        = 0x8008
    GM_UART_PS       = 0x8009
    CAN_XON_XOFF_PS  = 0x800A
    ANALOG_IN_1      = 0x800B
    ANALOG_IN_2      = 0x800C
    ANALOG_IN_3      = 0x800D
    ANALOG_IN_4      = 0x800E
    ANALOG_IN_5      = 0x800F
    ANALOG_IN_6      = 0x8010
    ANALOG_IN_7      = 0x8011
    ANALOG_IN_8      = 0x8012
    ANALOG_IN_9      = 0x8013
    ANALOG_IN_10     = 0x8014
    ANALOG_IN_11     = 0x8015
    ANALOG_IN_12     = 0x8016
    ANALOG_IN_13     = 0x8017
    ANALOG_IN_14     = 0x8018
    ANALOG_IN_15     = 0x8019
    ANALOG_IN_16     = 0x801A
    ANALOG_IN_17     = 0x801B
    ANALOG_IN_18     = 0x801C
    ANALOG_IN_19     = 0x801D
    ANALOG_IN_20     = 0x801E
    ANALOG_IN_21     = 0x801F
    ANALOG_IN_22     = 0x8020
    ANALOG_IN_23     = 0x8021
    ANALOG_IN_24     = 0x8022
    ANALOG_IN_25     = 0x8023
    ANALOG_IN_26     = 0x8024
    ANALOG_IN_27     = 0x8025
    ANALOG_IN_28     = 0x8026
    ANALOG_IN_29     = 0x8027
    ANALOG_IN_30     = 0x8028
    ANALOG_IN_31     = 0x8029
    ANALOG_IN_32     = 0x802A


class Filter(Enum):
    PASS_FILTER = 0x00000001
    BLOCK_FILTER = 0x00000002
    FLOW_CONTROL_FILTER = 0x00000003


class ConnectFlags(Enum):
    NONE = 0
    CAN_29_BIT_ID = 0x100
    ISO9141_NO_CHECKSUM = 0x200
    CAN_ID_BOTH = 0x800
    ISO9141_K_LINE_ONLY = 0x1000


class TxFlags(Enum):
    NONE = 0
    # 0 = no padding
    # 1 = pad all flow controlled messages to a full CAN frame using zeroes
    ISO15765_FRAME_PAD = 0x00000040

    ISO15765_ADDR_TYPE = 0x00000080
    CAN_29_BIT_ID = 0x00000100

    # 0 = Interface message timing as specified in ISO 14230
    # 1 = After a response is received for a physical request, the wait time shall be reduced to P3_MIN
    # Does not affect timing on responses to functional requests
    WAIT_P3_MIN_ONLY = 0x00000200

    SW_CAN_HV_TX = 0x00000400

    # 0 = Transmit using SCI Full duplex mode
    # 1 = Transmit using SCI Half duplex mode
    SCI_MODE = 0x00400000

    # 0 = no voltage after message transmit
    # 1 = apply 20V after message transmit
    SCI_TX_VOLTAGE = 0x00800000

    DT_PERIODIC_UPDATE = 0x10000000


class RxStatus(Enum):
    NONE = 0
    # 0 = received
    # 1 = transmitted
    TX_MSG_TYPE  = 0x00000001

    # 0 = Not a start of message indication
    # 1 = First byte or frame received
    START_OF_MESSAGE = 0x00000002
    ISO15765_FIRST_FRAME = 0x00000002  

    # 0 = No break received
    # 1 = Break received
    RX_BREAK = 0x00000004

    # 0 = No TxDone
    # 1 = TxDone
    TX_INDICATION = 0x00000008
    TX_DONE = 0x00000008

    # 0 = No Error
    # 1 = Padding Error
    ISO15765_PADDING_ERROR = 0x00000010

    # 0 = no extended address,
    # 1 = extended address is first byte after the CAN ID
    ISO15765_ADDR_TYPE = 0x00000080

    CAN_29_BIT_ID = 0x00000100

    SW_CAN_NS_RX = 0x00040000
    SW_CAN_HS_RX = 0x00020000
    SW_CAN_HV_RX = 0x00010000


class Ioctl_ID(Enum):
    GET_CONFIG = 0x01
    SET_CONFIG = 0x02
    READ_VBATT = 0x03
    FIVE_BAUD_INIT = 0x04
    FAST_INIT = 0x05
    CLEAR_TX_BUFFER = 0x07
    CLEAR_RX_BUFFER = 0x08
    CLEAR_PERIODIC_MSGS = 0x09
    CLEAR_MSG_FILTERS = 0x0A
    CLEAR_FUNCT_MSG_LOOKUP_TABLE = 0x0B
    ADD_TO_FUNCT_MSG_LOOKUP_TABLE = 0x0C
    DELETE_FROM_FUNCT_MSG_LOOKUP_TABLE = 0x0D
    READ_PROG_VOLTAGE = 0x0E

    DATA_RATE = 0x01  # 5 500000 	# Baud rate value used for vehicle network. No default value specified.
    LOOPBACK = 0x03  # 0(OFF)/1(ON)	# 0 = Do not echo transmitted messages to the Receive queue. 1 = Echo transmitted messages to the Receive queue.
    NODE_ADDRESS = 0x04  # 0x00-0xFF	# J1850PWM specific, physical address for node of interest in the vehicle network. Default is no nodes are recognized by scan tool.
    NETWORK_LINE = 0x05  # 0(BUS_NORMAL)/1(BUS_PLUS)/2(BUS_MINUS)	# J1850PWM specific, network line(s) active during message transfers. Default value is 0(BUS_NORMAL).
    P1_MIN = 0x06  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU inter-byte time for responses [02.02-API: ms]. Default value is 0 ms. 04.04-API: NOT ADJUSTABLE, 0ms.
    P1_MAX = 0x07  # 0x0/0x1-0xFFFF # ISO-9141/14230 specific, max. ECU inter-byte time for responses [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 20 ms.
    P2_MIN = 0x08  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU response time to a tester request or between ECU responses [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, 0ms. Default value is 25 ms.
    P2_MAX = 0x09  # 0x0-0xFFFF	# ISO-9141/14230 specific, max. ECU response time to a tester request or between ECU responses [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, all messages up to P3_MIN are receoved. Default value is 50 ms.
    P3_MIN = 0x0A  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. ECU response time between end of ECU response and next tester request [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 55 ms.
    P3_MAX = 0x0B  # 0x0-0xFFFF	# ISO-9141/14230 specific, max. ECU response time between end of ECU response and next tester request [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, messages can be sent at anytime after P3_MIN. Default value is 5000 ms.
    P4_MIN = 0x0C  # 0x0-0xFFFF	# ISO-9141/14230 specific, min. tester inter-byte time for a request [02.02-API: ms, 04.04-API: *0.5ms]. Default value is 5 ms.
    P4_MAX = 0x0D  # 0x0-0xFFFF	# ISO-9141/14230 specific, max. tester inter-byte time for a request [02.02-API: ms, 04.04-API: *0.5ms]. 04.04-API: NOT ADJUSTABLE, P4_MIN is always used. Default value is 20 ms.
    W1 = 0x0E  # 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] from the address byte end to synchronization pattern start. Default value is 300 ms.
    W2 = 0x0F  # 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] from the synchronization byte end to key byte 1 start. Default value is 20 ms.
    W3 = 0x10  # 0x0-0xFFFF	# ISO 9141 specific, max. time [ms] between key byte 1 and key byte 2. Default value is 20 ms.
    W4 = 0x11  # 0x0-0xFFFF	# ISO 9141 specific, 02.02-API: max. time [ms] between key byte 2 and its inversion from the tester. Default value is 50 ms.
    W5 = 0x12  # 0x0-0xFFFF	# ISO 9141 specific, min. time [ms] before the tester begins retransmission of the address byte. Default value is 300 ms.
    TIDLE = 0x13  # 0x0-0xFFFF	# ISO 9141 specific, bus idle time required before starting a fast initialization sequence. Default value is W5 value.
    TINL = 0x14  # 0x0-0xFFFF	# ISO 9141 specific, the duration [ms] of the fast initialization low pulse. Default value is 25 ms.
    TWUP = 0x15  # 0x0-0xFFFF	# ISO 9141 specific, the duration [ms] of the fast initialization wake-up pulse. Default value is 50 ms.
    PARITY = 0x16  # 0(NO_PARITY)/1(ODD_PARITY)/2(EVEN_PARITY)	# ISO9141 specific, parity type for detecting bit errors.  Default value is 0(NO_PARITY).
    BIT_SAMPLE_POINT = 0x17  # 0-100	# CAN specific, the desired bit sample point as a percentage of bit time. Default value is 80%.
    SYNCH_JUMP_WIDTH = 0x18  # 0-100	# CAN specific, the desired synchronization jump width as a percentage of the bit time. Default value is 15%.
    W0 = 0x19
    T1_MAX = 0x1A  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe response delay. Default value is 20 ms.
    T2_MAX = 0x1B  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. interframe request delay.Default value is 100 ms.
    T4_MAX = 0x1C  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage response delay. Default value is 20 ms.
    T5_MAX = 0x1D  # 0x0-0xFFFF	# SCI_X_XXXX specific, the max. intermessage request delay. Default value is 100 ms.
    ISO15765_BS = 0x1E  # 0x0-0xFF	# ISO15765 specific, the block size for segmented transfers.
    ISO15765_STMIN = 0x1F  # 0x0-0xFF	# ISO15765 specific, the separation time for segmented transfers.
    DATA_BITS = 0x20  # 04.04-API only
    FIVE_BAUD_MOD = 0x21
    BS_TX = 0x22
    STMIN_TX = 0x23
    T3_MAX = 0x24
    ISO15765_WFT_MAX = 0x25

    # Tatrix specific
    TX_IOCTL_APP_SERVICE             = 0x70000
    TX_IOCTL_SET_DLL_DEBUG_FLAGS     = 0x70001
    TX_IOCTL_SET_DEV_DEBUG_FLAGS     = 0x70002
    TX_IOCTL_SET_DLL_STATUS_CALLBACK = 0x70003

    # J2534-2
    CAN_MIXED_FORMAT          = 0x8000
    J1962_PINS                = 0x8001
    SW_CAN_HS_DATA_RATE       = 0x8010
    SW_CAN_SPEEDCHANGE_ENABLE = 0x8011
    SW_CAN_RES_SWITCH         = 0x8012
    ACTIVE_CHANNELS           = 0x8020 # Bitmask of channels being sampled
    SAMPLE_RATE               = 0x8021 # Samples/second or Seconds/sample
    SAMPLES_PER_READING       = 0x8022 # Samples to average into a single reading
    READINGS_PER_MSG          = 0x8023 # Number of readings for each active channel per PASSTHRU_MSG structure
    AVERAGING_METHOD          = 0x8024 # The way in which the samples will be averaged.
    SAMPLE_RESOLUTION         = 0x8025 # The number of bits of resolution for each channel in the subsystem. Read Only.
    INPUT_RANGE_LOW           = 0x8026 # Lower limit in millivolts of A/D input. Read Only.
    INPUT_RANGE_HIGH          = 0x8027 # Upper limit in millivolts of A/D input. Read Only.


# Tatrix specific
class Ioctl_Flags(Enum):
    TX_IOCTL_DLL_DEBUG_FLAG_J2534_CALLS   = 0x00000001
    TX_IOCTL_DLL_DEBUG_FLAG_ALL_DEV_COMMS = 0x00000002
    TX_IOCTL_DEV_DEBUG_FLAG_USB_COMMS     = 0x00000001


class PASSTHRU_MSG(Structure):
    _fields_ = [("ProtocolID", c_ulong),
                ("RxStatus", c_ulong),
                ("TxFlags", c_ulong),
                ("Timestamp", c_ulong),
                ("DataSize", c_ulong),
                ("ExtraDataIndex", c_ulong),
                ("Data", c_ubyte * 4128)]

    def setData(self, data: bytes):
        self.DataSize = len(data)
        for i in range(self.DataSize):
            self.Data[i] = data[i]

    def getData(self):
        addr_size = 5 if self.RxStatus & RxStatus.ISO15765_ADDR_TYPE.value else 4
        return bytes(self.Data[addr_size : self.DataSize])


class SCONFIG(Structure):
    _fields_ = [("Parameter", c_ulong),
                ("Value", c_ulong)]


class SCONFIG_LIST(Structure):
    _fields_ = [("NumOfParams", c_ulong),
                ("ConfigPtr", POINTER(SCONFIG))]

    def __init__(self, values):
        self.NumOfParams = len(values)
        self.ConfigPtr = (SCONFIG * self.NumOfParams)(*values)


class J2534():
    def __init__(self, windll: str):
        self.hDLL = cdll.LoadLibrary(windll)

        dllPassThruOpenProto = WINFUNCTYPE(
            c_long,
            c_void_p,
            POINTER(c_ulong),
        )
        dllPassThruOpenParams = (1, "pName", 0), (1, "pDeviceID", 0)
        self.dllPassThruOpen = dllPassThruOpenProto(("PassThruOpen", self.hDLL), dllPassThruOpenParams)

        dllPassThruCloseProto = WINFUNCTYPE(
            c_long,
            c_ulong,
        )
        dllPassThruCloseParams = (1, "DeviceID", 0),
        self.dllPassThruClose = dllPassThruCloseProto(("PassThruClose", self.hDLL), dllPassThruCloseParams)

        dllPassThruConnectProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            c_ulong,
            c_ulong,
            c_ulong,
            POINTER(c_ulong),
        )
        dllPassThruConnectParams = (1, "DeviceID", 0), (1, "ProtocolID", 0), (1, "Flags", 0), (1, "BaudRate", 500000), (1, "pChannelID", 0)
        self.dllPassThruConnect = dllPassThruConnectProto(("PassThruConnect", self.hDLL), dllPassThruConnectParams)

        dllPassThruDisconnectProto = WINFUNCTYPE(
            c_long,
            c_ulong,
        )
        dllPassThruDisconnectParams = (1, "ChannelID", 0),
        self.dllPassThruDisconnect = dllPassThruDisconnectProto(("PassThruDisconnect", self.hDLL), dllPassThruDisconnectParams)

        dllPassThruReadMsgsProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            POINTER(PASSTHRU_MSG),
            POINTER(c_ulong),
            c_ulong,
        )
        dllPassThruReadMsgsParams = (1, "ChannelID", 0), (1, "pMsg", 0), (1, "pNumMsgs", 0), (1, "Timeout", 0)
        self.dllPassThruReadMsgs = dllPassThruReadMsgsProto(("PassThruReadMsgs", self.hDLL), dllPassThruReadMsgsParams)

        dllPassThruWriteMsgsProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            POINTER(PASSTHRU_MSG),
            POINTER(c_ulong),
            c_ulong,
        )
        dllPassThruWriteMsgsParams = (1, "ChannelID", 0), (1, "pMsg", 0), (1, "pNumMsgs", 0), (1, "Timeout", 0)
        self.dllPassThruWriteMsgs = dllPassThruWriteMsgsProto(("PassThruWriteMsgs", self.hDLL), dllPassThruWriteMsgsParams)

        dllPassThruStartPeriodicMsgProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            POINTER(PASSTHRU_MSG),
            POINTER(c_ulong),
            c_ulong,
        )
        dllPassThruStartPeriodicMsgParams = (1, "ChannelID", 0), (1, "pMsg", 0), (1, "pMsgID", 0), (1, "TimeInterval", 0)
        self.dllPassThruStartPeriodicMsg = dllPassThruStartPeriodicMsgProto(("PassThruStartPeriodicMsg", self.hDLL), dllPassThruStartPeriodicMsgParams)

        dllPassThruStopPeriodicMsgProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            c_ulong,
        )
        dllPassThruStopPeriodicMsgParams = (1, "ChannelID", 0), (1, "MsgID", 0)
        self.dllPassThruStopPeriodicMsg = dllPassThruStopPeriodicMsgProto(("PassThruStopPeriodicMsg", self.hDLL), dllPassThruStopPeriodicMsgParams)

        dllPassThruReadVersionProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            POINTER(c_char),
            POINTER(c_char),
            POINTER(c_char),
        )
        dllPassThruReadVersionParams = (1, "DeviceID", 0), (1, "pFirmwareVersion", 0), (1, "pDllVersion", 0), (1, "pApiVersoin", 0)
        self.dllPassThruReadVersion = dllPassThruReadVersionProto(("PassThruReadVersion", self.hDLL), dllPassThruReadVersionParams)

        dllPassThruGetLastErrorProto = WINFUNCTYPE(
            c_long,
            POINTER(c_char),
        )
        dllPassThruGetLastErrorParams = (1, "pErrorDescription", 0),
        self.dllPassThruGetLastError = dllPassThruGetLastErrorProto(("PassThruGetLastError", self.hDLL), dllPassThruGetLastErrorParams)

        dllPassThruStartMsgFilterProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            c_ulong,
            POINTER(PASSTHRU_MSG),
            POINTER(PASSTHRU_MSG),
            POINTER(PASSTHRU_MSG),
            POINTER(c_ulong),
        )
        dllPassThruStartMsgFilterParams = (1,"ChannelID",0), (1,"FilterType",0),(1,"pMaskMsg",0),(1,"pPatternMsg",0),(1,"pFlowControlMsg",0),(1,"pMsgID",0)
        self.dllPassThruStartMsgFilter = dllPassThruStartMsgFilterProto(("PassThruStartMsgFilter", self.hDLL), dllPassThruStartMsgFilterParams)

        dllPassThruIoctlProto = WINFUNCTYPE(
            c_long,
            c_ulong,
            c_ulong,
            c_void_p,
            c_void_p,
        )
        dllPassThruIoctlParams = (1, "HandleID", 0), (1, "IoctlID", 0), (1, "pInput", 0), (1, "pOutput", 0)
        self.dllPassThruIoctl = dllPassThruIoctlProto(("PassThruIoctl", self.hDLL), dllPassThruIoctlParams)

    def PassThruOpen(self):
        DeviceID = c_ulong()

        result = self.dllPassThruOpen(bytes("J2534-2:", "ascii"), byref(DeviceID))
        return Error_ID(result), DeviceID

    def PassThruConnect(self, deviceID, protocol: Protocol_ID, baudrate: int):
        self.txFlags = TxFlags.NONE.value
        self.protocol = protocol
        if self.protocol in [Protocol_ID.ISO15765, Protocol_ID.ISO15765_PS, Protocol_ID.SW_ISO15765_PS]:
            self.txFlags |= TxFlags.ISO15765_FRAME_PAD.value

        connectFlags = ConnectFlags.CAN_ID_BOTH.value
        ChannelID = c_ulong()

        result = self.dllPassThruConnect(deviceID, self.protocol.value, connectFlags, baudrate, byref(ChannelID))
        return Error_ID(result), ChannelID

    def PassThruClose(self, DeviceID):
        result = self.dllPassThruClose(DeviceID)
        return Error_ID(result)

    def PassThruDisconnect(self, ChannelID):
        result = self.dllPassThruDisconnect(ChannelID)
        return Error_ID(result)

    def PassThruReadMsgs(self, ChannelID, pNumMsgs=1, Timeout=1000):
        pMsg = PASSTHRU_MSG()
        pMsg.ProtocolID = self.protocol.value

        pNumMsgs = c_ulong(pNumMsgs)

        while 1:
            # breakpoint()
            # Do not wrap in queue for avoid mixing timeout of usb connection and real server response Timeout.
            result = self.dllPassThruReadMsgs(ChannelID, byref(pMsg), byref(pNumMsgs), c_ulong(Timeout))

            if Error_ID(result) == Error_ID.ERR_SUCCESS and pMsg.RxStatus & (RxStatus.TX_INDICATION.value | RxStatus.TX_MSG_TYPE.value | RxStatus.START_OF_MESSAGE.value):
                continue

            return Error_ID(result), pMsg.getData(), pNumMsgs

    def PassThruWriteMsgs(self, ChannelID, Data, pNumMsgs=1, Timeout=1000):
        txmsg = PASSTHRU_MSG()
        txmsg.TxFlags = self.txFlags
        txmsg.ProtocolID = self.protocol.value
        txmsg.setData(self.txid + Data)

        result = self.dllPassThruWriteMsgs(ChannelID, byref(txmsg), byref(c_ulong(pNumMsgs)), c_ulong(Timeout))
        return Error_ID(result)

    def PassThruStartPeriodicMsg(self, ChannelID, Data, MsgID=0, TimeInterval=100):
        pMsg = PASSTHRU_MSG()
        pMsg.ProtocolID = self.protocol.value
        pMsg.setData(Data)

        result = self.dllPassThruStartPeriodicMsg(ChannelID, byref(pMsg), byref(c_ulong(MsgID)), c_ulong(TimeInterval))
        return Error_ID(result)

    def PassThruStopPeriodicMsg(self, ChannelID, MsgID):
        result = self.dllPassThruStopPeriodicMsg(ChannelID, MsgID)

        return Error_ID(result)

    def PassThruReadVersion(self, DeviceID):
        pFirmwareVersion = (c_char * 80)()
        pDllVersion = (c_char * 80)()
        pApiVersion = (c_char * 80)()

        result = self.dllPassThruReadVersion(DeviceID, pFirmwareVersion, pDllVersion, pApiVersion)
        return Error_ID(result), pFirmwareVersion.value.decode(), pDllVersion.value.decode(), pApiVersion.value.decode()

    def PassThruGetLastError(self):
        pErrorDescription = (c_char * 80)()

        result = self.dllPassThruGetLastError(pErrorDescription)
        return Error_ID(result), pErrorDescription.value.decode()

    def PassThruIoctl(self, HandleID, IoctlID: Ioctl_ID, ioctlInput=None, ioctlOutput=None):
        pInput = None if ioctlInput is None else byref(ioctlInput)
        pOutput = None if ioctlOutput is None else byref(ioctlOutput)

        result = self.dllPassThruIoctl(HandleID, c_ulong(IoctlID.value), pInput, pOutput)
        return Error_ID(result)

    def PassThruIoctl_READ_VBATT(self, DeviceID):
        vbatt = c_ulong()

        result = self.PassThruIoctl(DeviceID, Ioctl_ID.READ_VBATT, None, vbatt)
        return result, vbatt.value

    def PassThruStartMsgFilter(self, ChannelID, txid: int, rxid: int, extid = None):
        self.txid = txid.to_bytes(4, "big")
        self.rxid = rxid.to_bytes(4, "big")

        if extid is not None:
            self.txid += extid.to_bytes(1, "big")
            self.rxid += extid.to_bytes(1, "big")
            self.txFlags |= TxFlags.ISO15765_ADDR_TYPE.value
        else:
            self.txFlags &= ~TxFlags.ISO15765_ADDR_TYPE.value

        if txid >> 11:
            self.txFlags |= TxFlags.CAN_29_BIT_ID.value
        else:
            self.txFlags &= ~TxFlags.CAN_29_BIT_ID.value

        msgMask = PASSTHRU_MSG()
        msgMask.ProtocolID = self.protocol.value
        msgMask.TxFlags = self.txFlags
        msgMask.RxStatus = msgMask.ExtraDataIndex = 0xCCCC_CCCC
        msgMask.setData(b"\xFF" * len(self.rxid))

        msgPattern = PASSTHRU_MSG()
        msgPattern.ProtocolID = self.protocol.value
        msgPattern.TxFlags = self.txFlags
        msgPattern.RxStatus = msgPattern.ExtraDataIndex = 0xCCCC_CCCC
        msgPattern.setData(self.rxid)

        if self.protocol in [Protocol_ID.ISO15765, Protocol_ID.ISO15765_PS, Protocol_ID.SW_ISO15765_PS]:
            filterType = c_ulong(Filter.FLOW_CONTROL_FILTER.value)
            msgFlow = PASSTHRU_MSG()
            msgFlow.ProtocolID = self.protocol.value
            msgFlow.TxFlags = self.txFlags
            msgFlow.RxStatus = msgFlow.ExtraDataIndex = 0xCCCC_CCCC
            msgFlow.setData(self.txid)
            pMsgFlow = byref(msgFlow)
        else:
            filterType = c_ulong(Filter.PASS_FILTER.value)
            pMsgFlow = None

        FilterID = c_ulong(0)

        result = self.dllPassThruStartMsgFilter(ChannelID, filterType, byref(msgMask), byref(msgPattern), pMsgFlow, byref(FilterID))
        return Error_ID(result), FilterID
