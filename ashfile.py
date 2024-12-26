#!/usr/bin/env python3

################################  N8UR ASHCOMM  ################################
#
#	Copyright 2019 by John Ackermann, N8UR jra@febo.com https://febo.com
#	Version number can be found in the ashglobal.py file
#
#	This program is free software; you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation; either version 2 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
################################################################################

#############################   ashfile.py    ##################################

import time
import signal
import datetime

from ashserial import *
from ashcommand import *
from ashutil import *
from ashmessage import *
from ashposition import *
from ashtime import *
from ashrinex import *
from ashglobal import *
from ashopt import *
from asherror import *

# available from pip, but copy provided with this program
from xmodem import XMODEM, XMODEM1k, NAK

# to avoid xmodem logging messages
import logging
#logging.basicConfig(level=logging.ERROR)

###############################################################################
###############################################################################
# FILE DOWNLOAD ROUTINES
###############################################################################
###############################################################################


class AshtechFile:

    def __init__(self, serport, commands,g, verbose):
        self.Serial = serport
        self.Commands = commands
        self.g = g
        self.verbose = verbose


###############################################################################
# Z12 download routines
###############################################################################
###############################################################################
# ComposeRFileName -- build filename for downloaded file
###############################################################################
    def ComposeRFileName(self, SiteName, SessNum, SegWn, SegTime):
        t = GPS_Time(SegWn, SegTime)
        timestring = t.gpstime
        (sec, minute, hour, mday, mon, year, wday, yday) = timestring.split(",")

        str(SiteName).translate(str.maketrans(
            '?', '_'))  # Replace ???? with ____

        if (SessNum < 26):
            year = str((int(year) % 100))
            SessId = chr(65+SessNum) + year
        else:
            year = str((int(year) % 10))
            SessId = chr(65+(SessNum / 10)) + chr(65+(SessNum % 10)) + year

        FileName = "R" + SiteName + str(SessId) + (".%03d" % (int(yday)+1))

        return FileName

###############################################################################
# BuildImageHeader -- create binary struct to prepend to downloaded file
# data.  Much of this is a mystery; most named fields in remote33.pl are
# never filled.
###############################################################################
    def BuildImageHeader(self):

        RIDstring = self.rid
        # trim first and last elements of list,
        # convert to comma-delimited string
        RIDstring = ",".join(RIDstring[1:-1])
        # convert string to bytes object
        RIDstring = bytes(RIDstring, 'ascii')

        # remote33.pl identifies these variables,
        # but doesn't do anything with them
        # Note the clever way to assign multiple vars to 0 :-)
        (TotalMemory, FATStart, FATEnd, PhotoStart,
         PhotoEnd, AlmStart, AlmEnd, DataStart, DataEnd) = (0,) * 9

        ImageHeader = b""
        ImageHeader += struct.pack('20s', b'Z-12')
        ImageHeader += struct.pack('20s', RIDstring)
        ImageHeader += struct.pack('bb', 1, 0)
        ImageHeader += struct.pack('l', TotalMemory)
        ImageHeader += struct.pack('l', FATStart)
        ImageHeader += struct.pack('l', FATEnd)
        ImageHeader += struct.pack('l', PhotoStart)
        ImageHeader += struct.pack('l', PhotoEnd)
        ImageHeader += struct.pack('l', AlmStart)
        ImageHeader += struct.pack('l', AlmEnd)
        ImageHeader += struct.pack('l', DataStart)
        ImageHeader += struct.pack('l', DataEnd)
        ImageHeader += struct.pack('72s', b'SPARE')

        return ImageHeader

###############################################################################
# BuildFat -- build FAT for beginning of downloaded file
###############################################################################

    def BuildFat(self, FileHeader, SessNum, MaxFileNumbers,
                 FileInfoSize, FileHdrStruct):

        # Can't figure out how to do this with chars rather than string
        (SegBeg, Remainder) = struct.unpack('=l 76s', FileHeader)

        # Turn remainder back into bytearray so it's mutable
        Remainder = bytearray(Remainder)

        SessLetter = ord(chr(65 + SessNum))
        # This byte is id'd as "RangerMode", which doesn't make sense...
        Remainder[8] = SessLetter

        # Calculate new value of the start address
        SegBeg = 10 + MaxFileNumbers * FileInfoSize

        # FAT header
        FatInfo = struct.pack('19s b', b"", 1)

        # Our file always first
        FatInfo += struct.pack('=l 76s', SegBeg, Remainder)

        # Then 0 for the remainding files
        RemainderSize = FileInfoSize*2*(MaxFileNumbers-1)

        FormatString = "%ds" % RemainderSize
        FatInfo += struct.pack(FormatString, b"")

        return FatInfo

###############################################################################
# DownloadZ12File -- download file image from Z12
###############################################################################
    def DownloadZ12File(self, RFileName, SegBeg, WordCount, CombinedFileHeader):
        filelen = WordCount * 2
        headerlen = len(CombinedFileHeader)
        totallen = headerlen + filelen
        filebuf = open(RFileName, 'wb')
        filebuf.write(bytearray(CombinedFileHeader))

        modem = XMODEM1k(self.Serial.getc, self.Serial.putc)
        self.Serial.serial.read(1000)
        QueryString = str.encode("$PASHQ,BLK,%X,%X\n\r" % (SegBeg, filelen))
        self.Serial.serial.timeout = 2

        print("Requesting download of %s (%s)" %
              (RFileName, Human_Bytes(filelen)))
        self.Serial.serial.write(QueryString)
        time.sleep(1)

        download_bytes = 0
        t1_start = time.perf_counter()
        download_bytes = modem.recv(filebuf, crc_mode=1)
        t1_stop = time.perf_counter()
        elapsed = t1_stop - t1_start
        bytes_per_sec = download_bytes / elapsed
        print("Received %s in %f.0 seconds: (%f.0 bytes/sec)" %
              (Human_Bytes(download_bytes),
               elapsed, bytes_per_sec))

        filebuf.close()
        #self.serial.timeout = self.TIMEOUT

        return download_bytes


###############################################################################
# GetZ12Files -- download files from Z12 memory
###############################################################################


    def GetZ12Files(self):
        # Assumes all files are the same 4-character sitename and
        # each represents a session number starting with 0

        MaxFileNumbers = 10 # For some versions of Z-12 it's 10

        FatInfoFile = "fatinfo.dat"
        MemInfoSize = 10
        FileInfoSize = 40
        FatInfoSize = MemInfoSize + FileInfoSize * MaxFileNumbers

        modem = XMODEM1k(self.Serial.getc, self.Serial.putc)
        self.Serial.serial.timeout = 2
        # Download FAT to buffer
        Query = b"BLK,%X,%X" % (0, FatInfoSize*2)
        self.Commands.QueryCommand(Query, verbose=True)
        time.sleep(2)

        print("Requesting FAT Download...")
        mybuf = open('data', 'wb')
        print("Bytes received: ", modem.recv(mybuf, crc_mode=1, retry=2))
        mybuf.close()

        # Now read and process FAT
        mybuf = open('data', "rb")
        buf = mybuf.read(20)

        MemHeader = struct.unpack(">10H", buf)
        FilesFound = MemHeader[9]  # decrement by one for current file
        print("Files Found (less current): ", FilesFound)

        # Perl: N = unsigned 32 bit long big endian Python: l
        # Perl: A = Ascii string, space padded Python: s (string)
        # Perl: C = unsigned 8 bit char Python: B
        # Perl: n = unsigned 16 bit short big endian Python: H
        # FAT struct from remote33.pl:
        # FileHdrStruct = "N N A4 C C n N C A3 A1 A33 n N n n C C C C C C n n n"
        # FAT struct translated to Python:
        FileHdrStruct = ">l l 4s B B H l B 3s 1s 33s H l H H B B B B B B H H H"

        # Now loop through the files downloading each, creating header,
        # and saving combination to disk
        for i in range(0, FilesFound):
            FileHeader = mybuf.read(FileInfoSize*2)  # FileHeader is 80 bytes
            FileHdr = struct.unpack(FileHdrStruct, FileHeader)
            (SegBeg, WordCount, SegName, RangerMode, Tmp,
             FileStartWn, FileStartTime, RcvrType, Tmp2,
             SessName, Project, SegWn, SegTime,
             d13, d14, d15, d16, d17, d18, d19,
             d20, d21, d22, d23) = FileHdr

            SegName = SegName.decode('ascii')
            Tmp2 = Tmp2.decode('ascii')
            SessName = SessName.decode('ascii')
            Project = Project.decode('ascii')

            if (WordCount > 0):   # don't download zero sized file
                # Generate filename
                RFileName = self.ComposeRFileName(SegName, i, SegWn, SegTime)
                print("RFileName: ", RFileName)

                # Build image header
                ImageHeader = self.BuildImageHeader()

                # Build file FAT
                FatInfo = self.BuildFat(FileHeader, i, MaxFileNumbers,
                                        FileInfoSize, FileHdrStruct)

                CombinedFileHeader = ImageHeader + FatInfo

                self.DownloadZ12File(RFileName, SegBeg, WordCount,
                                     CombinedFileHeader)

        mybuf.close()
        return()

###############################################################################
# uZ download routines
###############################################################################
############################################################################
# From REMOTE33:
#
# Subroutine:  GetFilesListuZ
#
# Description: This subroutine obtains the list of the recorded files using
#              the query $PASHQ,FIF,<n> where n is the index of the first
#              file.
#              Each $PASHR,FIF can contain information for up to 10 files.
#              Format of the $PASHR,FIF is the following
#              $PASHR,FIF,<SpaceLeft>,<TotalFiles>,<FilesInThisMessage>,\
#              [<FileIdx>,<FileName>,<FileDate>,<FileSize>] - this group
#              is repeated <FilesInThisMessage> times
#
# Parameters:  None
#
############################################################################

    def GetFilesListuZ(self):

        # FLS command takes lowest index number to return
        # but if you specify higher than actual, bombs out
        # so, start with 0 and learn the actual total in the
        # first response
        total_files = "0"
        self.Commands.QueryCommand("FLS," + total_files)
        time.sleep(0.1)
        response = self.Serial.read_line()
        fields = response.split(b',')

        # get and strip off the preamble fields
        (null,kb_left,total_sessions,sessions_follow) = fields[:4]
        kb_left = int(kb_left)
        total_sessions = int(total_sessions)
        sessions_follow = int(sessions_follow)
        print("{} left, {} total sessions, {} sessions follow:".format(
            Human_Bytes(kb_left * 1024), total_sessions, sessions_follow))
        fields = fields[4:]

        # each session has 3 fields: site, time, size
        # time field needs to be split: first 4 digits are
        # GPS week, which needs fixing due to rollover;
        # next field is day of week; last field is HH:MM
        n = 0
        session_list = []
        while n < sessions_follow:
            site = fields[0].decode('ascii')
            week = int(fields[1][:4])
            week = str(fix_rollover(week))
            remainder = fields[1][4:].decode('ascii')
            date = week + remainder
            size = fields[2]
            # remove checksum from last entry
            if b'*' in size:
                (size,_) = size.split(b'*')

            size = int(size)
            print("site: {} date: {} size: {}".format(site, date,
                Human_Bytes(size * 1024)))
            fields = fields[3:]
            session_list.append(fields)
            n += 1
        return session_list

############################################################################
# From REMOTE33:
#
# Subroutine:  DownloadFilesuZ
#
# Description: This subroutines uses the utility rz to download receiver U
#              files via ZMODEM.
#              The recieiver initiates the transfer upon receiving command:
#              $PASHS,FIL,DOWNLOAD,<file name>,ZMODEM   
#
# Parameters:  None
#
############################################################################

    def DownloadFileuZ(self, session_id):
        modem = XMODEM(self.Serial.getc, self.Serial.putc)
        print( self.Commands.QueryRespond("DOWNLOAD," + str(session_id)
            + "XMODEM"))

        download_bytes = 0
        t1_start = time.perf_counter()
        download_bytes = modem.recv(filebuf, crc_mode=1)
        t1_stop = time.perf_counter()
        elapsed = t1_stop - t1_start
        bytes_per_sec = downloadbytes / elapsed
        print("Received %s in %f.0 seconds: (%f.0 bytes/sec)" %
              (self.Human_Bytes(download_bytes),
               elapsed, bytes_per_sec))

        filebuf.close
        self.serial.timeout = self.TIMEOUT

        return download_bytes

###############################################################################
# MAIN PROGRAM
###############################################################################

# NOTE: temporarily hardwired for file processing only; most command-
# line params are ignored

def main():
    g = AshtechGlobals()
    option = AshtechOpts(g)

    option.getargs()
    verbose = g.opts['verbose']
    if verbose:
        print("Verbose mode")

    # store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    error = AshtechError(original_sigint, g)
    signal.signal(signal.SIGINT, error.exit_handler)

    Serial = AshtechSerial(g.opts['serport'],
                           g.opts['baud'], g.opts['hwport'], verbose)
    Commands = AshtechCommands(Serial, g, verbose)
    ZFile = AshtechFile(Serial, Commands, g, verbose)

    print()
    Serial.Open()

    Commands.SetCommand("OUT,A", verbose=0)     # turn off output
    Serial.reset_input()                        # clean the sluices
    Serial.reset_output()
    time.sleep(1)

    ZFile.rid = Commands.QueryRID(verbose=True)
    print()
    g.start_time = datetime.datetime.utcnow()

    time.sleep(1)
    ZFile.GetZ12Files()

    Serial.Close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
