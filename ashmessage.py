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

from ashserial import *
from ashcommand import *
from ashutil import *
from ashposition import *
from ashtime import *
from ashrinex import *
from ashglobal import *

class AshtechMessages:

###############################################################################
###############################################################################
	def __init__(self,serport,commands,structs,rinex,verbose):
		self.SerPort = serport
		self.Commands = commands
		self.Globals = structs
		self.RINEX = rinex
		self.verbose = verbose

###############################################################################
###############################################################################
# MsgSwitch -- sit on serial port and hand messages off to appropriate handler
# relies on another command to start message stream
###############################################################################
	def MsgSwitch(self,verbose=False):

		self.SerPort.inter_byte_timeout = 5  # tenths of second?
		delimiter = b'$PASHR'

		self.SerPort.reset_input()		# clear out garbage
		while True:
			message = self.SerPort.read_anything(delimiter,0)
			if len(message) > 9: # ignore leftover b'$PASHR' in buffer
				
				# strip crlf and beyond from end
				if (message[-8:] == b'\r\n$PASHR'):
					message = message[:-8]
				#sometimes we don't get the $PASHR part
				elif (message[-2:] == b'\r\n'):
					message = message[:-2]
				else:
					print("Bad message trailer: \"",message[-8:],"\"")
					continue

				# extract message type, strip whitespace
				msg_type = message[1:4].decode('ascii')
				msg_type = msg_type.strip()
				# trim off msg type including comma, leave checksum byte(s)
				payload = message[5:]

				if verbose:
					print ("msg_type:",msg_type,"length:",len(payload))
				if   msg_type == 'MPC': self.parse_mben(payload,verbose)
				elif msg_type == 'PBN': self.parse_pben(payload,verbose)
				elif msg_type == 'SNV': pass #self.parse_snav(payload,verbose)
				elif msg_type == 'SAL': pass #self.parse_salm(payload,verbose)
				elif msg_type == 'EPB': pass #self.parse_epb(payload,verbose)
				elif msg_type == 'RPC': pass #self.parse_dben(payload,verbose)
				elif msg_type == 'DAL':	pass # not processed here
				else: print("Message type",msg_type,"is unknown!")

				# send an epoch stanza to the RINEX output only if
				# we've received both MBN and PBN messages.  also
				# test to make sure we have week and tow
			if self.Globals.got_first_mben and \
				self.Globals.got_first_pben and \
				self.Globals.gps_week and \
				self.Globals.gps_tow:

				# and only if we've gotten a full stanza
				if self.Globals.mben_list_full:
					if verbose:
						print("Off to RINEX...")
					self.RINEX.write_rinex_obs()
					# clear the mben list
					self.Globals.mben_list = [None] * 33 # 1 - 32
					self.Globals.mben_list_full = False
					# clear tow since it's now in the past
					self.Globals.gps_tow = 0

		return 

###############################################################################
# parse_mben -- parse measurement binary response ($PASHQ,MBN)
# returns a dict with a header as the first item, followed by 1 to 3 items
# depending on which observations were made.  Raw values are converted to
# properly scaled ones.
###############################################################################
	def parse_mben(self,message,verbose=False):
		LIGHTSPEED = self.Globals.LIGHTSPEED		# speed of light, km/s
		Z12_SNR_SCALE = self.Globals.Z12_SNR_SCALE	# scale to sensible range

		# first, strip off checksum byte and test
		chksum = message[-1:]
		message = message[:-1]
		if not verify_chksum(message,chksum):
			print("Checksum error!")
			return

		# message structure and keys defined in ashglobal.py
		mben_list = struct.unpack(self.Globals.mben_struct,message) 
		mben_dict = dict(zip(self.Globals.mben_keys, mben_list))
		mben_flag_list = [None] * 33
		mben_flag_dict = dict(zip(self.Globals.mben_flag_keys,mben_flag_list))

		prn = mben_dict['prn']

		if not prn in range(1,32):
			return

		# convert "seq" (unit: 50ms modulo 30 minutes) to real time
		seq = int(mben_dict['seq'])
		seq_tmp = GPS_Time(self.Globals.gps_week,self.Globals.gps_tow)
		seq_seconds = seq_tmp.time_from_seq(self.Globals.gps_week,
			self.Globals.gps_tow,seq)
		epoch = GPS_Time(self.Globals.gps_week,seq_seconds)

		# convert values (formulas from Lady Heather -- thanks, Mark!)
		mben_dict['az'] = mben_dict['az'] * 2
		mben_dict['ca_snr'] /= Z12_SNR_SCALE
		mben_dict['l1_snr'] /= Z12_SNR_SCALE
		mben_dict['l2_snr'] /= Z12_SNR_SCALE

		# see below for phase processing

		mben_dict['ca_range'] *= (LIGHTSPEED * 1000.0)
		mben_dict['l1_range'] *= (LIGHTSPEED * 1000.0)
		mben_dict['l2_range'] *= (LIGHTSPEED * 1000.0)

		mben_dict['ca_dopp'] /= 10000.0
		mben_dict['l1_dopp'] /= 10000.0
		mben_dict['l2_dopp'] /= 10000.0

		# add the lli values to mben_flag_dict; one flag for
		# each of ca, l1, l2 so calc once copy thrice
		flag_tmp= make_lli(mben_dict['ca_warn'],mben_dict['ca_goodbad'])
		mben_flag_dict['ca_phase_lli'] = \
		mben_flag_dict['ca_range_lli'] = \
		mben_flag_dict['ca_dopp_lli'] = \
		flag_tmp

		flag_tmp= make_lli(mben_dict['l1_warn'],mben_dict['l1_goodbad'])
		mben_flag_dict['l1_phase_lli'] = \
		mben_flag_dict['l1_range_lli'] = \
		mben_flag_dict['l1_dopp_lli'] = \
		flag_tmp

		flag_tmp= make_lli(mben_dict['l2_warn'],mben_dict['l2_goodbad'])
		mben_flag_dict['l2_phase_lli'] = \
		mben_flag_dict['l2_range_lli'] = \
		mben_flag_dict['l2_dopp_lli'] = \
		flag_tmp

		# fix phase overflows and update lli if necessary
		mben_dict['ca_phase'],mben_flag_dict['ca_phase_lli'] = \
			fixphase(mben_dict['ca_phase'],mben_flag_dict['ca_phase_lli'])
		mben_dict['l1_phase'],mben_flag_dict['l1_phase_lli'] = \
			fixphase(mben_dict['l1_phase'],mben_flag_dict['l1_phase_lli'])
		mben_dict['l2_phase'],mben_flag_dict['l2_phase_lli'] = \
			fixphase(mben_dict['l2_phase'],mben_flag_dict['l2_phase_lli'])

		# add the sbyte values to mben_flag_dict; one flag for 
		# each of ca, l1, l2 so calc once copy thrice
		sbyte_tmp = make_sbyte(mben_dict['ca_snr'])
		mben_flag_dict['ca_phase_sbyte'] = \
		mben_flag_dict['ca_range_sbyte'] = \
		mben_flag_dict['ca_dopp_sbyte'] = \
		sbyte_tmp

		sbyte_tmp = make_sbyte(mben_dict['l1_snr'])
		mben_flag_dict['l1_phase_sbyte'] = \
		mben_flag_dict['l1_range_sbyte'] = \
		mben_flag_dict['l1_dopp_sbyte'] = \
		sbyte_tmp

		sbyte_tmp = make_sbyte(mben_dict['l2_snr'])
		mben_flag_dict['l2_phase_sbyte'] = \
		mben_flag_dict['l2_range_sbyte'] = \
		mben_flag_dict['l2_dopp_sbyte'] = \
		sbyte_tmp

		self.Globals.mben_list[prn] = mben_dict
		self.Globals.mben_flag_list[prn] = mben_flag_dict

		if 1 == 0:
			print()
			print("Epoch:",epoch)
			mbn = "MBN" + str(mben_dict['struct_left'])
			print(mbn,"seq:",mben_dict['seq'],"prn:",mben_dict['prn'],
				"el:",mben_dict['el'], "az:",mben_dict['az'],
				"ch_id:",mben_dict['ch_id'])
			print("CA:",mben_dict['ca_qual'],mben_dict['ca_snr'],
				mben_dict['ca_phase'],mben_dict['ca_prange'],
				mben_dict['ca_dop'])
			print("L1:",mben_dict['l1_qual'],mben_dict['l1_snr'],
				mben_dict['l1_phase'],mben_dict['l1_prange'],
				mben_dict['l1_dop'])
			print("L2:",mben_dict['l2_qual'],mben_dict['l2_snr'],
				mben_dict['l2_phase'],mben_dict['l2_prange'],
				mben_dict['l2_dop'])
			if mben_dict['struct_left'] == 0:
				print("PRNs in this epoch:",end = ' ',flush = True)
				for i in self.Globals.mben_list:
					if i != None:
						print(i['prn'], end = ' ',flush = True)
				print()

		if mben_dict['struct_left'] == 0:	# last message for this epoch
			self.Globals.got_first_mben = True
			self.Globals.mben_list_full = True

		return	

###############################################################################
# parse_pben -- parse measurement binary response ($PASHQ,PBN) and
# return llh among other things
###############################################################################
	def parse_pben(self,message,verbose=False):

		# only get pben after we've received the first mben
		if not self.Globals.got_first_mben:
			return

		if verbose:
			print("raw pben length:",len(message))
		# first, strip off checksum bytes and test
		chksum = message[-2:]
		message = message[:-2]
		if not verify_chksum(message,chksum):
			print("Checksum error!")
			return

		# message structure and keys defined in ashglobal.py
		vallist = list(struct.unpack(self.Globals.pben_struct,message))
		pben_dict = dict(zip(self.Globals.pben_keys,vallist))

		pben_dict['tow'] =  pben_dict['tow'] / 1000.0
		pben_dict['site'] = pben_dict['site'].decode('ascii')
		pben_dict['pdop'] = pben_dict['pdop'] / 100.0	

		fix = Position(pben_dict['navx'],pben_dict['navy'],pben_dict['navz'])
		self.Globals.current_fix = fix

		self.Globals.current_pben = pben_dict
		self.Globals.gps_tow = pben_dict['tow']

		self.Globals.current_epoch = \
			GPS_Time(self.Globals.gps_week,self.Globals.gps_tow)

		self.Globals.current_epoch_string = \
			GPS_Time(self.Globals.gps_week,self.Globals.gps_tow).timestring()

		if not self.Globals.got_first_pben:
			self.Globals.first_observation = \
				self.Globals.current_epoch
			self.Globals.first_observation_string = \
				self.Globals.current_epoch_string

		self.Globals.got_first_pben = True

		if verbose:
#			print("navx,navy,navz:",navx,navy,navz)
			print(fix.ddxxx_float_list())
			print(fix.ddxxx_string_list())
			print(fix.ddmmxxx_float_list())
			print(fix.ddmmxxx_string_list())
			print(fix.ddmmssxxx_float_list())
			print(fix.ddmmssxxx_string_list())
			print()
			print("PBN:   %6.0f %4s %7.2f %7.2f %7.2f" %
				(pben_dict['tow'],pben_dict['site'],pben_dict['navx'],
					pben_dict['navy'],pben_dict['navz']))
			print("       %5.4f %.4E %.4E %.4E %3.5f, %1.2f" %
  				(pben_dict['offset'],pben_dict['velx'],pben_dict['vely'],
					pben_dict['velz'],pben_dict['drift'],pben_dict['pdop']))
			print()
			print("WGS84:",fix.ddmmxxx_string_list())
			print("current epoch seconds:",pben_dict['tow'])

		return fix,pben_dict['tow']

###############################################################################
# parse_salm -- parse almanac binary response ($PASHQ,SLM)
###############################################################################
	def parse_salm(self,message,verbose=False):
		print("In SALM parser")
		return

###############################################################################
# parse_snav -- parse measurement binary response ($PASHQ,SNV)
###############################################################################
	def parse_snav(self,message,verbose=False):

		# first, strip off checksum bytes and test
		chksum = message[-2]
		message = message[:-2]
		if not verify_chksum(message,chksum):
			print("Checksum error!")
			return

		if verbose:
			print("In SNAV handler")
			print("svn message length",len(message))

		# Z12 manual says 130 bytes excluding checksum
		svn_struct = \
			("> s l f l l f f f f d d d l f f f f f f d d d f f h h c c ")
		print("svn_struct length",len(svn_struct))
		keylist = ['Wn','Sn','tgd_gp_del','iodc_clock_data_issue','toc',
					'af2','af1','af0','iode_orb_data_issue','imean_anom_corr',
					'ecc','a1div2','toe','cic_harm_corr_rad','crc_harm_corr_m',
					'cis_harm_corr_rad','crs_harm_corr_m','cuc_harm_corr_rad',
					'omega_0','arg_of_perigee','inc_angle','omegadot','idot',
					'acc','health','curve_fit','prn_minus_one','reserved']

		vallist = list(struct.unpack(svn_struct,message))
		if verbose:
			print("Raw week number:",vallist[0])

		snav_dict = dict(zip(keylist, vallist))
		if verbose:
			print("Original week number:",snav_dict['Wn'])
		snav_dict['Wn'] = fix_gps_week_number(snav_Dict['Wn'])
		if verbose:
			print("Adjusted week number:",snav_dict['Wn'])

		return snav_dict

##############################################################################
# GetGPSWeek -- use DAL NMEA message to get GPS week number and and
# return week number after fixing WNRO problems.  Z12 doesn't make it 
# easy to get the week number and DAL seems easiest to parse.  There's 
# one message per satellite, but we only need one record to grab the week, 
# so we ignore all past the first message record.
###############################################################################
	def GetGPSWeek(self,verbose=False):
		
		if verbose:
			print("Getting GPS week number...")

		# in theory, we should be able to do $PASHQ,DAL,A to get one 
		# sentence, but that doesn't work.  So instead we start streaming 
		# the sentence then stop after we get one

		# enable NMEA output
		self.Commands.SetCommand("OUT,A,NMEA")
		time.sleep(0.1)

		# set sentence rate to every 20 seconds, so we
		# have time to turn it off before getting flooded
		self.Commands.SetCommand("NME,PER,20")
		time.sleep(0.1)

		# start streaming DAL sentence
		self.Commands.SetCommand("NME,DAL,A,ON")
		time.sleep(0.1)

		gps_week = 0
		self.SerPort.reset_input()		# clear out garbage
		while not gps_week:
			# get one sentence
			message = self.SerPort.read_line()
			response = message.split(b',')

			# Wn is contained in field 14 before "*" and checksum
			gps_week,_ = response[13].split(b'*')

		# turn off NMEA sentences
		self.Commands.SetCommand("NME,ALL,A,OFF")

		if verbose:
			print("Raw GPS week:",gps_week)

		#correct for epoch
		gps_week = fix_rollover(gps_week)
		self.Globals.gps_week = gps_week
		if verbose:
			print("Corrected GPS week:",gps_week)

		return gps_week

###############################################################################
# get_initial_fix -- get one PBEN message and extract llh, and one SNAV
# message to extract Wn (week number) and Sn (tow -- seconds of week), then
# use that to get a UTC time structure
###############################################################################
	def GetInitialFix(self,verbose=False):
		
		fix = Position(navx,navy,navz)
		if verbose:
			print("navx,navy,navz:",navx,navy,navz)
			print(fix.ddxxx_float_list())
			print(fix.ddxxx_string_list())
			print(fix.ddmmxxx_float_list())
			print(fix.ddmmxxx_string_list())
			print(fix.ddmmssxxx_float_list())
			print(fix.ddmmssxxx_string_list())
			print("GPS week:",gps_week)
			print()
		return

# end of ashmessage.py

