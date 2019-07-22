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

#############################   ashglobal.py    ################################

from ashglobal import *
from ashserial import *
from ashcommand import *
from ashutil import *
from ashposition import *
import ashtime
#from ashtime import *
from ashrinex import *


class AshtechGlobals:

    ###############################################################################
    ###############################################################################
    def __init__(self):
        pass

###############################################################################
# Constants
###############################################################################

    # program name
    PROG_NAME = "N8UR_AshComms"

    # version number
    VER_NUM = "2019.07.08A"

    # gps_week is greater than:
    ROLLOVER = 2048

    # GPS time is UTC -18 seconds
    LEAPSECONDS = 18

    # C
    LIGHTSPEED = 299792.458    # speed of light, km/s

    # divide reported snr by this to get something that looks like dBc
    # this is from Lady Heather.  For now, let's use reported value
#	Z12_SNR_SCALE = 5.0
    Z12_SNR_SCALE = 1.0

###############################################################################
# data structures used globally
###############################################################################

###############################################################################
# command line options (set by argparse)
###############################################################################

    # need to keep this current with actual options!
    opt_keys = ['verbose', 'serport', 'baud', 'hwport', 'rinex_file',
                'elmask', 'dopmask', 'site_name', 'project_name', 'msg_rate',
                'operator', 'comment', 'marker', 'marker_number', 'observer',
                'agency', 'rx_number', 'antenna_number', 'antenna_type',
                'antenna_height', 'antenna_east', 'antenna_north']

    opts = dict.fromkeys(opt_keys, None)  # make empty dict

    rx_type = None					# set by QueryRID()
    rx_ser_num = None				# set by QueryRID() if rx_type = "UZ"

###############################################################################
# mben measurement has the key observation data.  There is one data dictionary
# per satellite being measured in this.  A list of 33 elements (PRNS 1-32,
# but remember list starts with element 0) provides # a slot for each of
# the GPS satellites; the appropriate position is filled in for the
# satellites received in each epoch.  The entire list is cleared before
# writing a new epoch.
#
# Z12 manual says 97 bytes including checksum but counting fields yields
# 95.  There's a set of common values followed by three identical sets of
# observations for CA, L1, and L2.
###############################################################################
    mben_struct = """> H B B B B B B B c B B d d l l B B c B 
		B d d l l B B c B B d d l l"""

    # any data munging is done in the parse_mben function and presented
    # here (ie, this is not raw Z12 data).
    mben_keys = [
        'seq', 'struct_left', 'prn', 'el', 'az', 'ch_id',

        'ca_warn', 'ca_goodbad', 'ca_spare', 'ca_snr', 'ca_qual',
        'ca_phase', 'ca_range', 'ca_dopp', 'ca_correction',

        'l1_warn', 'l1_goodbad', 'l1_spare', 'l1_snr', 'l1_qual',
        'l1_phase', 'l1_range', 'l1_dopp', 'l1_correction',

        'l2_warn', 'l2_goodbad', 'l2_spare', 'l2_snr', 'l2_qual',
        'l2_phase', 'l2_range', 'l2_dopp', 'l1_correction']

    mben_flag_keys = [
        'ca_phase_lli', 'ca_phase_sbyte',
        'ca_range_lli', 'ca_range_sbyte',
        'ca_dopp_lli', 'ca_dopp_sbyte',

        'l1_phase_lli', 'l1_phase_sbyte',
        'l1_range_lli', 'l1_range_sbyte',
        'l1_dopp_lli', 'l1_dopp_sbyte',

        'l2_phase_lli', 'l2_phase_sbyte',
        'l2_range_lli', 'l2_range_sbyte',
        'l2_dopp_lli', 'l2_dopp_sbyte']

    # make empty structs
    mben_dict = dict.fromkeys(mben_keys, None)
    mben_flag_dict = dict.fromkeys(mben_flag_keys, None)

    mben_list = [None] * 33         # current observables; index = PRN (1-32)
    mben_flag_list = [None] * 33    # current observables; index = PRN
    mben_list_full = False          # keep track of messages per epoch
    current_mben_epoch = GPS_Time(0, 0)  # set in parse_mben()
    current_mben_epoch_string = ""

###############################################################################
# pben is "navigation" message which includes time of week, llh, vlvlvh,
# dop. Z12 manual says 54 bytes excluding checksum
###############################################################################
    pben_struct = ("> l 4s d d d f f f f f H")

    pben_keys = ['tow', 'site', 'navx', 'navy', 'navz', 'offset',
                 'velx', 'vely', 'velz', 'drift', 'pdop']

    current_pben = dict.fromkeys(pben_keys, None)  # make empty dict
    new_pben = False        # toggles in MsgSwitch
    current_pben_epoch = GPS_Time(0, 0)  # set in parse_pben()
    current_pben_epoch_string = ""  # set in parse_pben()
    current_fix = [None]

    # this contains all the data for one epoch
    epoch_data = [mben_list, current_pben]

###############################################################################
# time stuff
    first_observation = GPS_Time(0, 0)     # set in parse_pben()
    first_observation_string = ""  # set in parse_pben()

    # these have to be available in the exit hanlder. how???
    start_time = None			# set in main()
    obs_epoch_count = 0	        	# set in write_obs_epoch()

    # for convenience, week and current tow are kept in separate variables
    gps_week = 0		# set in get_gps_week()
    gps_tow = 0			# set by parse_pben()
    last_tow = 0                # set by parse_pben()

###############################################################################
# stuff for building RINEX files
###############################################################################
    obs_filename = ""						# from create_obs_file()
    wrote_rinex_obs_file_header = False		# set by write_rinex_obs_epoch()

###############################################################################
# GENERAL COMMENTS FOR THE BENEFIT OF FUTURE GENERATIONS
###############################################################################

# For each epoch, the Z12 outputs one mben message per satellite
# followed by one pben message.  The mben message doesn't directly
# contain a timestamp, but the "seq" value can be converted to time
# assuming you know the correct time within 30 minutes.  Below is an
# example of the message timing for one epoch (all times are in
# GPS, not UTC time, so -18 seconds from clock time):
#
# mben msg time: 2019-06-28 14:36:40.241705 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:40.352999 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:40.464362 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:40.575608 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:40.686875 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:40.798160 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:40.909513 epoch:  19  6 28 14 36 40.0000000
# mben msg time: 2019-06-28 14:36:41.020809 epoch:  19  6 28 14 36 40.0000000
# pben msg time: 2019-06-28 14:36:44.130924 epoch:  19  6 28 14 36 40.0000000
#
# The mben messages are output first and take a second or so.  The pben
# messge comes about 3 seconds later.  This might change depending on
# what other messages the receiver is outputting.

# end of ashglobals.py
