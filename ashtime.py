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
import datetime
import calendar

class GPS_Time:

	def __init__(self,week,tow):
		self.week = week
		self.tow = tow
		self.time_list = self.MakeTime(week,tow)
		(self.sec,self.minute,self.hour,self.mday,self.mon,self.year,
			self.weeknum,self.yday) = self.time_list

###############################################################################
# MakeTime -- take GPSWeek and TOW and return GPS time
# (NOT UTC; no leapseconds) in list format.
###############################################################################
	def MakeTime(self,week,tow):
		datetime_input_format = "%Y-%m-%d %H:%M:%S"
		datetimeformat = "%S,%M,%H,%d,%m,%Y,%w,%j"
		epoch = datetime.datetime.strptime("1980-01-06 00:00:00",
			datetime_input_format)
		elapsed = datetime.timedelta(days = (week*7),
			seconds = tow) # Use GPS time; no leapseconds

		# sticks object in self.gpstime for other formatting
		self.gpstime = datetime.datetime.strftime(
			epoch + elapsed,datetimeformat)
		gpstimelist = list(self.gpstime.split(','))

		# also make a pretty string version
		self.gpstimestring = datetime.datetime.strftime(
			epoch + elapsed,datetime_input_format).strip()

		# Returns: (sec,min,hour,mday,mon,year,weeknum,yday)
		return gpstimelist

###############################################################################
# RINEX_fmt_obs -- return string in RINEX format for epoch header
###############################################################################
	def RINEX_fmt_obs(self):
		timestring = " {:2d}".format(int(self.year) - 2000)
		timestring += " {:2d}".format(int(self.mon))
		timestring += " {:2d}".format(int(self.mday))
		timestring += " {:2d}".format(int(self.hour))
		timestring += " {:2d}".format(int(self.minute))
		timestring += "{:11.7f}".format(float(self.sec))
	
		return timestring

###############################################################################
# timelist -- return list of values:
# (sec,minute,hour,mday,mon,year,weeknum,yday)
###############################################################################
	def timelist(self):
		return self.time_list

###############################################################################
# timestring -- return string in pretty date/time format
###############################################################################
	def timestring(self):
		return self.gpstimestring
		
		
###############################################################################
# time_from_seq -- number of seconds this week to last 30 minute mark
# this is to determine epoch time from mben_dict['seq'] value
###############################################################################
	def time_from_seq(self,week,tow,seq):

		# convert seq (50ms modulo 30 minutes) to seconds
		seq_seconds = int(seq * 0.05)

		# divide tow by 1800 seconds (30 minutes) to
		# get number of 30 minute chunks so far this week
		(quotient,remainder) = divmod(tow,1800)

		# multiply 30 minutes of seconds by number of chunks
		# to give us tow to prior 30 minute point
		trunc_seconds = quotient * 1800
		# add seq_seconds to get epoch time
		seq_seconds = trunc_seconds + seq_seconds

		return seq_seconds

###############################################################################
# NOT IN GPS_Time class
###############################################################################
# current_gps_time -- get current time from system clock
# and subtract leapseconds
###############################################################################
def current_gps_time():
	from ashglobal import AshtechGlobals
	leapseconds = AshtechGlobals.LEAPSECONDS
	gps_time = datetime.datetime.utcnow() + \
		datetime.timedelta(seconds=leapseconds)
	return gps_time

# end of ashtime.py
