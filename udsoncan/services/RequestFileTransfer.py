from . import *
from udsoncan.Response import Response
from udsoncan.exceptions import *
import struct

class RequestFileTransfer(BaseService):
    _sid = 0x38
    _use_subfunction = False

    supported_negative_response = [	
                                        Response.Code.IncorrectMessageLegthOrInvalidFormat,
                                        Response.Code.ConditionsNotCorrect,
                                        Response.Code.RequestOutOfRange,
                                        Response.Code.UploadDownloadNotAccepted
                                        ]
    class ModeOfOperation(BaseSubfunction):
        """
        RequestFileTransfer Mode Of Operation (MOOP). Represent the action that can be done on the server filesystem.
        See ISO-14229:2013 Annex G
        """

        __pretty_name__ = 'mode of operation'

        AddFile = 1
        DeleteFile = 2
        ReplaceFile = 3
        ReadFile = 4
        ReadDir = 5

    @classmethod
    def normalize_data_format_identifier(cls, dfi):
        from udsoncan import DataFormatIdentifier
        if dfi is None:
            dfi = DataFormatIdentifier()

        if not isinstance(dfi, DataFormatIdentifier):
            raise ValueError('dfi must be an instance of DataFormatIdentifier')

        return dfi

    @classmethod
    def make_request(cls, moop, path, dfi = None, filesize = None):
        from udsoncan import Request, Filesize
        if not isinstance(moop, int):
            raise ValueError('Mode of operation must be an integer')

        if moop not in [cls.ModeOfOperation.AddFile,
                            cls.ModeOfOperation.DeleteFile,
                            cls.ModeOfOperation.ReplaceFile,
                            cls.ModeOfOperation.ReadFile,
                            cls.ModeOfOperation.ReadDir]:
            raise ValueError("Mode of operation of %d is not a known mode" % moop)

        if not isinstance(path, str):
            raise ValueError('Given path must be a valid string')

        if len(path) <= 0:
            raise ValueError('Path must be a string longer than 0 character')

        path_ascii = path.encode('ascii')
        if len(path_ascii) > 0xFF:
            raise ValueError('Path length must be smaller or equal than 255 bytes when encoded in ASCII')

        use_dfi = moop in [cls.ModeOfOperation.AddFile, cls.ModeOfOperation.ReplaceFile, cls.ModeOfOperation.ReadFile]
        use_filesize = moop in [cls.ModeOfOperation.AddFile, cls.ModeOfOperation.ReplaceFile]
       
        if use_dfi:
            dfi = cls.normalize_data_format_identifier(dfi)
        else:
            if dfi is not None:
                raise ValueError('DataFormatIdentifier is not needed with ModeOfOperation=%d' % moop)
        
        if use_filesize:  
            if filesize is None:
                raise ValueError('A filesize must be given for this mode of operation')

            if isinstance(filesize, int):
                filesize = Filesize(filesize)

            if not isinstance(filesize, Filesize):
                raise ValueError('Given filesize must be a valid Filesize object or an integer') 

            if filesize.uncompressed is None:
                raise ValueError('Filesize needs at least an Uncompressed file size')

            if filesize.compressed is None:
                filesize = Filesize(uncompressed=filesize.uncompressed, compressed=filesize.uncompressed, width=filesize.get_width())
        else:
            if filesize is not None:
                raise ValueError('Filesize is not needed with ModeOfOperation=%d' % moop)               

        data = moop.to_bytes(1, 'big')
        data += len(path_ascii).to_bytes(1, 'big')
        data += path_ascii
        if use_dfi:
            data += dfi.get_byte()
        if use_filesize:
            data += filesize.get_width().to_bytes(1, 'big')
            data += filesize.get_uncompressed_bytes()
            data += filesize.get_compressed_bytes()

        request = Request(cls, data=data)
        return request



    @classmethod
    def interpret_response(cls, response, tolerate_zero_padding=True):
        from udsoncan import Filesize, DataFormatIdentifier
        response.service_data = cls.ResponseData()
        if len(response.data) < 1:
            raise InvalidResponseException(response, 'Response payload must be at least 1 byte long')
        response.service_data.moop_echo = int(response.data[0])

        has_lfid                    = response.service_data.moop_echo in [cls.ModeOfOperation.AddFile, cls.ModeOfOperation.ReplaceFile, cls.ModeOfOperation.ReadFile, cls.ModeOfOperation.ReadDir]
        has_dfi                     = response.service_data.moop_echo in [cls.ModeOfOperation.AddFile, cls.ModeOfOperation.ReplaceFile, cls.ModeOfOperation.ReadFile, cls.ModeOfOperation.ReadDir]
        has_filesize_length         = response.service_data.moop_echo in [cls.ModeOfOperation.ReadFile, cls.ModeOfOperation.ReadDir]
        has_uncompressed_filesize   = response.service_data.moop_echo in [cls.ModeOfOperation.ReadFile, cls.ModeOfOperation.ReadDir]
        has_compressed_filesize     = response.service_data.moop_echo in [cls.ModeOfOperation.ReadFile]

        cursor = 1
        if has_lfid:
            if len(response.data) < 2:
                raise InvalidResponseException(response, 'Response payload must be at least 2 byte long for Mode of operation %d' % response.service_data.moop_echo)
            lfid = int(response.data[1])
            cursor=2

            if lfid > 8:
                raise NotImplementedError('This client does not support number bigger than %d bits, but MaxNumberOfBlock is encoded on %d bits' % ((8*8), (lfid*8)))

            if lfid == 0:
                raise InvalidResponseException(response, 'Received a MaxNumberOfBlockLength of 0 which is impossible')

            if len(response.data) < 2+lfid:
                raise InvalidResponseException(response, 'Response payload says that MaxNumberOfBlock is encoded on %d bytes, but only %d bytes are present' % (lfid, (len(response.data)-2)))

            todecode = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
            for i in range(1,lfid+1):
                todecode[-i] = response.data[cursor+lfid-i]
            response.service_data.max_length = struct.unpack('>q', todecode)[0]
            cursor += lfid
        
        if has_dfi:
            if len(response.data) < cursor+1:
                raise InvalidResponseException(response, 'Missing DataFormatIdentifier in received response')

            response.service_data.dfi = DataFormatIdentifier.from_byte(response.data[cursor])
            cursor += 1
            dfi = response.service_data.dfi.get_byte_as_int()
            
            if response.service_data.moop_echo == cls.ModeOfOperation.ReadDir and dfi != 0:
                raise InvalidResponseException(response, 'DataFormatIdentifier for ReadDir can only be 0x00 as per ISO-14229, but its value was set to 0x%02x' % (dfi))

        if has_filesize_length:
            if len(response.data) < cursor+2:
                raise InvalidResponseException(response, 'Missing or incomplete FileSizeOrDirInfoParameterLength in received response')
            fsodipl = struct.unpack('>H', response.data[cursor:cursor+2])[0]
            cursor += 2

            if fsodipl > 8:
                raise NotImplementedError(response, 'This client does not support number bigger than %d bits, but FileSizeOrDirInfoLength is encoded on %d bits' % ((8*8), (fsodipl*8)))

            if fsodipl == 0:
                raise InvalidResponseException(response, 'Received a FileSizeOrDirInfoParameterLength of 0 which is impossible')

            if has_uncompressed_filesize:
                if len(response.data) < cursor+fsodipl:
                    raise InvalidResponseException(response, 'Missing or incomplete fileSizeUncompressedOrDirInfoLength in received response')

                todecode = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
                for i in range(1,lfid+1):
                    todecode[-i] = response.data[cursor+fsodipl-i]
                uncompressed_size = struct.unpack('>q', todecode)[0]
                cursor+= fsodipl
            else:
                uncompressed_size = None

            if has_compressed_filesize:
                if len(response.data) < cursor+fsodipl:
                    raise InvalidResponseException(response, 'Missing or incomplete fileSizeCompressed in received response')

                todecode = bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00')
                for i in range(1,lfid+1):
                    todecode[-i] = response.data[cursor+fsodipl-i]
                compressed_size = struct.unpack('>q', todecode)[0]
                cursor += fsodipl
            else:
                compressed_size = None

        
        if has_uncompressed_filesize and response.service_data.moop_echo == cls.ModeOfOperation.ReadDir:
            response.service_data.dirinfo_length = uncompressed_size
        else:
            if has_uncompressed_filesize or has_compressed_filesize:
                response.service_data.filesize=Filesize(uncompressed = uncompressed_size, compressed=compressed_size)

        if len(response.data) > cursor:
            if response.data[cursor:] == b'\x00' * (len(response.data) - cursor) and tolerate_zero_padding:
                pass
            else:
                raise InvalidResponseException(response, 'Response payload has extra data that has no meaning')
        #from IPython import embed
        #embed()
        response.service_data = response.service_data

    class ResponseData(BaseResponseData):
        __slots__ = 'moop_echo', 'max_length', 'dfi', 'filesize', 'dirinfo_length'
        
        def __init__(self):
            super().__init__(RequestFileTransfer)
            self.moop_echo          = None
            self.max_length         = None
            self.dfi           = None
            self.filesize           = None
            self.dirinfo_length     = None
