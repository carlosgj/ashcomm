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
import signal
import serial
import io
import struct
import math
import argparse

from ashserial import *
from ashcommand import *
from ashutil import *
from ashmessage import *
from ashposition import *
from ashtime import *
from ashrinex import *
from ashglobal import *

###############################################################################
# exit_handler -- grab CTRL+C and exit gracefully
###############################################################################
def exit_handler(signum, frame):
    # restore the original signal handler
	signal.signal(signal.SIGINT, original_sigint)
	print()
	sys.exit(1)
#	try:
#		if input("\nReally quit? (y/n)> ").lower().startswith('y'):
#			sys.exit(1)
#	except KeyboardInterrupt:
#		print("Ok ok, quitting")
#		sys.exit(1)

	# restore the exit gracefully handler here    
	signal.signal(signal.SIGINT, exit_handler)

###############################################################################
class AshtechReceiver:

###############################################################################
###############################################################################
	def __init__(self):
		pass

###############################################################################
# getargs -- get command line arguments and supply defaults
###############################################################################
	def getargs(self):
		args = argparse.ArgumentParser()

		def str2bool(v):
			if isinstance(v, bool):
				return v
			if v.lower() in ('yes', 'true', 't', 'y', '1'):
				return True
			elif v.lower() in ('no', 'false', 'f', 'n', '0'):
				return False
			else:
				raise argparse.ArgumentTypeError('Boolean value expected.')

		# setup options with defaults
		args.add_argument('-v','--verbose', default='False',type=str2bool,
			nargs='?',const=True,help='be verbose')

		args.add_argument('-s','--serport', default='/dev/ttyS0',type=str,
			help='host computer serial port')
		args.add_argument('-b','--baud', default=115200,type=int,
			help='baud rate')
		args.add_argument('-p','--hwport', default='A',type=str,
			help='receiver hardware port')
		args.add_argument('-f','--rinex_file', default='',type=str,
			help='file name -- blank to auto-generate; \"NONE\" to skip')
		
		# receiver configuration options		
		args.add_argument('--elmask', default=10,type=int,
			help='elevation mask')
		args.add_argument('--dopmask', default=10,type=int,
			help='dop mask')
		args.add_argument('--site_name', default='TEST',type=str,
			help='site name \(max 4 char\)')
		args.add_argument('--project_name', default='',type=str,
			help='project name \(max 20 char\)')
		args.add_argument('--msg_rate', default=20,type=int,
			help='message output rate (default 20 seconds)')

		# RINEX field options
		args.add_argument('--operator', default = '',type=str,
			help='operator name')
		args.add_argument('--marker', default = '',type=str,
			help='marker name')
		args.add_argument('--marker_number', default = '',type=str,
			help='marker number')
		args.add_argument('--observer', default = '',type=str,
			help='observer')
		args.add_argument('--agency', default = '',type=str,
			help='agency')

		args.add_argument('--rx_number', default='',type=str,
			help='receiver number')
		args.add_argument('--antenna_number', default='',type=str,
			help='antenna number \(from WGS database\)')
		args.add_argument('--antenna_type', default='',type=str,
			help='antenna type \(from WGS database\)')

		args.add_argument('--antenna_height', default='',type=float,
			help='antenna elevation')
		args.add_argument('--antenna_east', default='',type=float,
			help='antenna easting')
		args.add_argument('--antenna_north', default='',type=float,
			help='antenna northing')

		self.Globals.opts = vars(args.parse_args())

		return

###############################################################################
# MAIN PROGRAM
###############################################################################
if __name__ == '__main__':
	original_sigint = signal.getsignal(signal.SIGINT)
	signal.signal(signal.SIGINT, exit_handler)
	
	import subprocess

	def main():
		RX = AshtechReceiver()
		RX.Globals = AshtechGlobals()
		RX.getargs()
		verbose = RX.Globals.opts['verbose']
		if verbose:
			print("Verbose mode")

		RX.Serial = AshtechSerial(RX.Globals.opts['serport'],
			RX.Globals.opts['baud'],RX.Globals.opts['hwport'],verbose)
		time.sleep(1)
		RX.Commands = AshtechCommands(RX.Serial,verbose)
		RX.RINEX = Rinex(RX.Commands,RX.Globals,verbose)
		RX.Messages = AshtechMessages(RX.Serial,RX.Commands,
			RX.Globals,RX.RINEX,verbose)

		RX.Serial.Open()
		RX.Globals.start_time = current_gps_time() # make GPS time

		RX.Commands.SetCommand("OUT,A",verbose=0)			# turn off output
		time.sleep(0.5)
		RX.Commands.SetCommand("NME,ALL,A,OFF",verbose=0)	# turn off NMEA
		time.sleep(0.5)

		RX.Commands.QueryRID(verbose=True)

#		RX.GetZ12Files()
		
		RX.RINEX.create_rinex_obs_file()

		RX.gps_week = RX.Messages.GetGPSWeek(verbose)
		time.sleep(1)

		# set message rate
		RX.Commands.SetCommand("RCI,"+ str(RX.Globals.opts['msg_rate']))
		time.sleep(1)
		RX.Commands.SetCommand("OUT,A,PBN,MBN,BIN",verbose)
		time.sleep(1)
		RX.Messages.MsgSwitch(verbose)
		time.sleep(1)
		RX.Serial.Close()

	main()

