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
class AshtechReceiver:


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
		args.add_argument('--comment', default = '',type=str,
			help='optional comment, max 60 characters')
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

	###################################################################
	# stats -- prints session details for the exit handler
	###################################################################
	def stats(self):
		print()
		print("Exiting program...")
		if self.Globals.start_time:
			duration = datetime.datetime.utcnow() - \
				self.Globals.start_time
			print("Run time: {}".format((str(duration))[:-5],end=''),end='')
			if self.Globals.obs_epoch_count:
				print("; wrote {} epochs to {}".format(
					self.Globals.obs_epoch_count,
					self.Globals.obs_filename))
			else:
				print()

###############################################################################
# MAIN PROGRAM
###############################################################################
if __name__ == '__main__':
	import subprocess

	def main():
		RX = AshtechReceiver()
		RX.Globals = AshtechGlobals()
		#######################################################################
		# exit_handler -- grab CTRL+C and exit gracefully
		#######################################################################
		def exit_handler(signum, frame):
			# restore the original signal handler
			signal.signal(signal.SIGINT, original_sigint)
			RX.stats()
			sys.exit(1)
			try:
				if input("\nReally quit? (y/n)> ").lower().startswith('y'):
					sys.exit(1)
			except KeyboardInterrupt:
				RX.stats()
				sys.exit(1)

		# restore the exit gracefully handler here    
		signal.signal(signal.SIGINT, exit_handler)
	#######################################################################

		# store the original SIGINT handler
		original_sigint = signal.getsignal(signal.SIGINT)
		signal.signal(signal.SIGINT, exit_handler)

		RX.getargs()
		verbose = RX.Globals.opts['verbose']
		if verbose:
			print("Verbose mode")

		RX.Serial = AshtechSerial(RX.Globals.opts['serport'],
			RX.Globals.opts['baud'],RX.Globals.opts['hwport'],verbose)
		time.sleep(1)
		RX.Commands = AshtechCommands(RX.Serial,RX.Globals,verbose)
		RX.RINEX = Rinex(RX.Commands,RX.Globals,verbose)
		RX.Messages = AshtechMessages(RX.Serial,RX.Commands,
			RX.Globals,RX.RINEX,verbose)

		RX.Serial.Open()

		RX.Commands.SetCommand("OUT,A",verbose=0)	# turn off output
		RX.Serial.reset_input()						# clean the sluices
		RX.Serial.reset_output()
		time.sleep(1)

		RX.Commands.QueryRID(verbose=True)

#		RX.GetZ12Files()

		RX.Globals.start_time = datetime.datetime.utcnow()
		RX.RINEX.create_rinex_obs_file()

		print("Waiting for data; it may take a bit...")

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
