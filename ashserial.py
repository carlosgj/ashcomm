#!/usr/bin/env python3

#################################  ashcomm.py  #################################
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

from ashcommand import *
from ashutil import *
from ashmessage import *
from ashposition import *


class AshtechSerial:
	TIMEOUT = 3				# default timeout

	# Ashtech speed param = BAUDRATES[index]: 0 = 300 .. 9 = 115200
	BAUDRATES = [
			"300",
			"600",
			"1200",
			"2400",
			"4800",
			"9600",
			"19200",
			"38400",
			"57600",
			"115200",
		]

###############################################################################
###############################################################################
	def __init__(self,ser_port,ser_baud,hw_port,verbose,timeout = TIMEOUT):
		self.ser_port = ser_port
		self.ser_baud = ser_baud
		self.hw_port = hw_port
		self.verbose = verbose
		self.timeout = timeout

##############################################################################
# SpeedToIndex -- convert numeric baud rate to index number for Z12
##############################################################################
	def SpeedToIndex(self,speed):
		try:
			index = self.BAUDRATES.index(str(speed))
			return index
		except ValueError:
			print("Invalid Baud Rate: ",speed)

###############################################################################
# Open -- open Z12 serial port
###############################################################################
	def Open(self):
		index = self.SpeedToIndex(self.ser_baud)

		try:
			print("Attempting to open",self.ser_port,"at",
				self.ser_baud,"baud...")
			self.serial = serial.Serial(self.ser_port,self.ser_baud)
			self.serial.rtscts = False
			self.serial.dsrdtr = False
			self.serial.xonxoff = False
		except:
			print("Oops... error",sys.exc_info()[0],"occured.")
			sys.exit(1)

#		print("Trying to find hardware speed...",end=' ')
#		rate = self.FindHardwareSpeed()
#		print("detected baudrate: %s" % rate)

#		if int(rate) != int(self.ser_baud):
#			print("Attempting to change speed to",self.ser_baud,"baud...")
#			self.SetHardwareSpeed(self.ser_baud)
#			rate = self.FindHardwareSpeed()
#			if int(rate) == int(self.ser_baud):
#				print("Set and confirmed requested speed: %s" % rate)
#			else:
#				print("Couldn't set new speed; staying at",rate)

		time.sleep(0.1)
		self.reset_input()
		self.reset_output()

		return serial

###############################################################################
# Close -- close Z12 serial port
###############################################################################
	def Close(self):
		self.serial.close()

###############################################################################
# SetPortSpeed -- set computer port to desired speed
###############################################################################
	def SetPortSpeed(self,speed):
		self.reset_input()
		self.reset_output()
		self.serial.baudrate = speed
		self.serial.flush()
		return

###############################################################################
# FindHardwareSpeed -- probe the Z12 for its current serial port speed
###############################################################################
	def FindHardwareSpeed(self):
		starting_index = len(self.BAUDRATES) - 1
		index = starting_index

		TEST_TIMEOUT = 1
		self.serial.timeout = TEST_TIMEOUT

		# clear out the sluices
		self.reset_input()
		self.reset_output()

		# Ashtech responses start with "$PASHR,"
		look_for = b"$PASH"
		while (index > 0):
			rate = self.BAUDRATES[index]
			# send port query
			time.sleep(0.5)
			self.write("$PASHQ,PRT,A\r\n")
			time.sleep(0.5)
			response = self.read_anything('',16)
			if look_for in response:
				break
			index -= 1
			# loop until it works
			if (index == 0):
				index = starting_index

		self.serial.timeout = self.TIMEOUT
		return rate

###############################################################################
# SetHardwareSpeed -- set Z12 hardware serial speed to requested baud rate
###############################################################################
	def SetHardwareSpeed(self,speed):
		do_checksum = False
		index = self.SpeedToIndex(speed)
		command = "SPD," + self.hw_port + "," + str(index)
		result = self.Command.SetCommand(command,do_checksum) 

###############################################################################

###############################################################################
# read, write, etc. commands
###############################################################################

###############################################################################
# reset_input -- reset input buffer
###############################################################################
	def reset_input(self):
		self.serial.reset_input_buffer()

###############################################################################
# reset_output -- reset output buffer
###############################################################################
	def reset_output(self):
		self.serial.reset_output_buffer()

###############################################################################
# flush -- flush write buffer
###############################################################################
	def flush(self):
		self.serial.flush()
###############################################################################

###############################################################################
# read_line -- grab a line terminated with a crlf and return results as 
# byte object with crlf and "$PASHR," header stripped off
###############################################################################
	def read_line(self,timeout=TIMEOUT):
		orig_timeout = self.serial.timeout
		self.serial.timeout = timeout
		while True:		
			time.sleep(0.1)
			if self.serial.in_waiting:
				message = self.serial.readline()
				break

		# remove $PASHR and trailing crlf
		message = message[7:].rstrip()

		self.serial.timeout = orig_timeout
		return message
		
###############################################################################
# read_anything -- a more general read function.  It waits for anything on
# input and depending on the params reads length bytes or reads until the
# delimiter.  Delimiter must be a byte object.  Returns raw byte object 
# without stripping anything
###############################################################################
	def read_anything(self,delimiter=b'',length=0,timeout=TIMEOUT):
		orig_timeout = self.serial.timeout
		self.serial.timeout = timeout
		self.serial.inter_byte_timeout = 5  # tenths of second?
		while True:
			time.sleep(0.1)
			if self.serial.in_waiting:
				if delimiter:
					message = self.serial.read_until(delimiter)
				if length:
					message = self.serial.read(length)	
				break
		self.serial.inter_byte_timeout = None  # default
		return message

###############################################################################
# write -- serial write function. Takes a byte object or an ASCII  string 
# (which it converts to bytes before writing).  Returns the number of
# bytes written or -1 if write fails.
###############################################################################
	def write(self,message):

		if type(message) is str:
			message = message.encode('ascii')
		try:
			numbytes = self.serial.write(message)
		except:
			print("Couldn't write to",self.ser_port,"!")
			return -1
			self.flush()
		return numbytes

# end of ashserial.py
