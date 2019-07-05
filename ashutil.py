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

###############################################################################
# verify_chksum -- generate checksum from payload and compare to one or two
# checksum_bytes, returning true if they match.  Expects that payload has 
# already been stripped of checksum bytes (they are passed as "checksum_rcvd")
###############################################################################
def verify_chksum(payload,chksum_rcvd):
	# single byte checksum is simple XOR
	if len(chksum_rcvd) == 1:
		chksum_rcvd = chksum_rcvd[0]
		chksum = 0
		for c in payload:
			chksum = chksum ^ c

	# two-byte checksum is sum of payload unpacked as unsigned shorts
	# remember to change from big-endian
	else:
		chksum_rcvd, = struct.unpack('> H',chksum_rcvd)
		size = len(payload)
		words = int(size / 2)
		odd = None
		if size % 2 == 0:                       # length is even  
			fmt = '> ' + str(words) + 'H'
			shorts = struct.unpack(fmt,payload)
		else:                                   # length is odd
			fmt = '>' + str(words) + 'H B'      # get odd byte too
			(shorts,odd) = struct.unpack(fmt,payload)
		chksum = 0
		for i in range(0,words):
			chksum = chksum + shorts[i]
		if odd:
			chksum = chksum + odd

		while chksum > 65535:
			chksum = chksum - 65536

	if chksum == chksum_rcvd:
		return True
	else:
		return False

###############################################################################
# fix_gps_week_rollover -- correct Wn by adding appropriate number of weeks
###############################################################################
def fix_rollover(Wn):
	from ashglobal import AshtechGlobals
	week = int(Wn)
	while week < AshtechGlobals.ROLLOVER:
		week = week + 1024
	return week

###############################################################################
# make_lli -- function to create lli byte from warn and good/bad flags
###############################################################################
def make_lli(warn,goodbad):
	# Z12 output:
	# warning flag bits:
	# 0		-- same as 22 in good/bad
	# 1		-- same as 24 in good/bad
	# 2		-- same as 23 in good/bad
	# 4		-- carrier phase questionable
	# 8		-- code phase (range) questionable
	# 16	-- range not precise (code phase loop not settled)
	# 32	-- Z tracking mode
	# 64	-- possible cycle slip
	# 128	-- loss of lock since last epoch
	#
	# good/bad flag (integer values):
	# 0		-- measurement not available, no further data sent
	# 22	-- code and/or carrier phase measured
	# 23	-- code and/or carrier phase measure, and nav message
	#			obtained but measurement not used to compute position
	# 24	-- code and/or carrier phase measured, nav message
	#			 obtained, and measurement used to compute position
	#
	# lli fields:
	# all zeroes -- OK or not known
	# 1		-- lost lock since previous obs; cycle slip possible
	# 2		-- opposite wavelength factor to defined (or default)
	# 4		-- observation under anti-spoofing
	# bits 0 and 1 for phase only

	x = 0
	LOCK_LOSS =		bool(x & 0b10000000)
	CYCLE_SLIP =	bool(x & 0b01000000)
	Z_TRACK =		bool(x & 0b00100000)
	FUZZY_RANGE =	bool(x & 0b00010000)
	FUNKY_CODE =	bool(x & 0b00001000)
	FUNKY_PHASE =	bool(x & 0b00000100)
	GROOVY_24 =		bool(x & 0b00000010)
	GROOVY_23 =		bool(x & 0b00000001)
	GROOVY_22 =		bool(x & 0b00000000)




	lli = 0
	if goodbad == 0:					# no data
		lli = 1
		return lli

	if warn >= 64:					# lost lock or possible cycle slip
		lli = 1
		return lli
	if warn > 32 and warn < 64:		# Z-tracking and questionable data
		lli = 5				
		return lli
	if warn == 32:					# Z-tracking mode; turn on A/S flag
		lli = 4
		return lli
	if warn >= 4 and warn < 32:		# questionable data
		lli = 1				
		return lli

	return lli						# all is well; return 0

###############################################################################
# make_srbyte -- function to create snr byte from snr value
###############################################################################
def make_sbyte(snrfloat):
	# we need to map analog value
	# (from 75 to 200?) into range:
	# 1 = minimum possible value
	# 5 = threshold for good S/N ratio
	# 9 = maximum possible value
	# 0 = unknown or don't care
				
	# lots of SWAG here...
	snrbyte = 1				# below 100 -- don't know how low it goes	
	if snrfloat >= 100:
		snrbyte = 2
	if snrfloat >= 115:
		snrbyte = 3
	if snrfloat >= 130:
		snrbyte = 4
	if snrfloat >= 145:
		snrbyte = 5
	if snrfloat >= 160:
		snrbyte = 6
	if snrfloat >= 175:
		snrbyte = 7
	if snrfloat >= 190:
		snrbyte = 8
	if snrfloat >= 205:
		snrbyte = 9

	return snrbyte

##############################################################################

##############################################################################
# fixphase -- used in parse_mben to validate the phase value and update lli
# shamelessly stolen from Mark Sims' Lady Heather
##############################################################################
def fixphase(phase_in,lli):
	phase = phase_in
	count = 0
	while phase >= 1.0E10:
		phase -= 1.0E10
		count += 1
		lli | (1<<0)		# set loss-of-lock bit
		if count >= 10:
			phase = 0.0
			break

	count = 0
	while phase <= -1.0E10:
		phase += 1.0E10
		count += 1
		lli | (1<<0)		# set loss-of-lock bit
		if count >= 10:
			phase = 0.0
			break
	return phase,lli

# end of ashutil.py
