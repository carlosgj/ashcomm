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
#	Software to communicate with Ashtech GPS receivers via serial port.
################################################################################

import sys
import time
import serial
import io
import struct
import math

from ashserial import *
from ashglobal import *
from ashutil import *
from ashmessage import *
from ashposition import *
from ashtime import *

class AshtechCommands:

###############################################################################
###############################################################################
	def __init__(self,serport,g,verbose):
		self.SerPort = serport
		self.Globals = g			# globals with lower case j is reserved
		self.verbose = verbose

###############################################################################
# SetCommand -- send $PASHS set command to Z12; don't wait for response
##############################################################################
	def SetCommand(self,command,verbose=False):
		command_string_bytes = b"$PASHS," + bytes(command,'ascii') + b"\r\n"
		if verbose:
			print("SetCommand sent: ", command_string_bytes)
		self.SerPort.write(command_string_bytes)
		return

###############################################################################
# QueryCommand -- send $PASHQ query command to Z12; don't wait for response
###############################################################################
	def QueryCommand(self,command,verbose=False):
		command_string_bytes = b"$PASHQ," + bytes(command,'ascii') + b"\r\n"
		if verbose:
			print("QueryCommand sent: ",command_string_bytes)
		self.SerPort.write(command_string_bytes)
		return

###############################################################################
# SetRespond -- send $PASHS set command to Z12 and return raw response
###############################################################################
	def SetRespond(self,command,do_checksum=False,verbose=False):
		TIMEOUT = 3
		self.SerPort.timeout = TIMEOUT
		command = b"$PASHS," + command
		checksum = ""
		if do_checksum == True:
			checksum = 0
			for char in command:
				checksum = checksum ^ ord(char)	
			checksum = b",*" + hex(checksum)	
		command = command + checksum
		command = command + b"\r\n"
		if verbose:
			print("Set command sent:",command)
		self.SerPort.reset_input()		# clear out garbage
		self.SerPort.write(command)

		response = self.SerPort.readline().decode('ascii')
		return response

###############################################################################
# QueryRespond -- send a $PASHQ query command to Z12 and return response.  If
# length specified, read that many bytes and return all, else read to EOL.
# else return as list with $PASHR and command echo stripped
###############################################################################
	def QueryRespond(self,command,length=0,verbose=False):

		command_string_bytes = b"$PASHQ," + bytes(command,'ascii') + b"\r\n"
		self.SerPort.reset_input()		# clear out garbage
		self.SerPort.reset_output()		# clear out garbage
		self.SerPort.flush()			# clear out garbage

		self.SerPort.write(command_string_bytes)
		time.sleep(0.1)

		if verbose:
			print("Query sent:",command_string_bytes)
		
		response = b''
		if length:			# get raw data of length bytes
			while True:
				response=self.SerPort.read_anything('',length)
				break
			return response
		else:
			while True:
				response = self.SerPort.read_line().decode('ascii')
				response = response.rstrip("\r\n")
				break
		return response

###############################################################################
###############################################################################
# receiver queries and commands
###############################################################################

###############################################################################
# QueryRID -- return receiver ID info as list; if verbose pretty print
###############################################################################
	def QueryRID(self,verbose=False):
		response = self.QueryRespond("RID,A").split(',')
		response = response[1:]

		# sometimes there's a checksum, sometimes there isn't
		response[4] = response[4].split('*',1)[0]
		
		self.Globals.rx_type = response[0]

		# uZ has "SID" command to return serial number.  But it does it
		# with two lines (dummy date field, then SN) so simple query
		# won't work
		if response[0] == "UZ":
			self.QueryCommand("SID")
			date = self.SerPort.read_line()
			ser_num = self.SerPort.read_line()
			ser_num = ser_num.decode('ascii')
			response.append(ser_num)
			self.Globals.rx_ser_num = ser_num

		if verbose:
			# fields: 0 = rx type, 1 = channel option, 2 = nav version,
			# 3 = options, 4 = channel version
			string = "Rx type: {} ".format(str(response[0]))
			if ser_num:
				string += "SN: {} ".format(str(ser_num))
			string += "Options: {}/{} ".format(
				str(response[1]),str(response[3]))
			string += "Versions: {}/{}".format(
				str(response[2]),str(response[4]))
			print(string)
			
		return response


# end of ashserial.py
