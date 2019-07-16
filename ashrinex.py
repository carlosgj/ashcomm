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

#############################   ashrinex.py    #################################

import sys
import os
import serial
import getpass

from ashserial import *
from ashcommand import *
from ashutil import *
from ashmessage import *
from ashposition import *


class Rinex:

    ###############################################################################
    def __init__(self, commands, globs, verbose):
        self.Commands = commands
        self.g = globs
        self.verbose = verbose

###############################################################################
    # help us keep columns lined up
    ruler = "xxxx5xxxx0xxxx5xxxx0xxxx5xxxx0xxxx5xxxx0xxxx5xxxx0xxxx5xxxx6xxxx5xxxx0xxxx5xxxx0"
###############################################################################

###############################################################################
# write_rinex_obs -- write header if haven't already, the write one epoch
# of data (header and obs)
###############################################################################
    def write_rinex_obs(self, verbose=False):

        if not self.g.wrote_rinex_obs_file_header:
            print("First Observation: " +
                     self.g.first_observation_string +
                ", measurements every " +
                     str(self.g.opts['msg_rate']) + " seconds")

            print("Approximate Position: " +
                self.g.current_fix.ddmmxxx_string() +
                ", Grid:", self.g.current_fix.grid_square())

            self.obs_file_header()
            self.g.wrote_rinex_obs_file_header = True

            print(
                "Starting to write observation epochs... press Ctrl-C to exit")
        print(".", end="")
        sys.stdout.flush()  # flush so the dots appear right away

        self.obs_epoch_header(verbose)
        self.obs_epoch(verbose)
        self.g.obs_epoch_count += 1

###############################################################################
# create_rinex_obs_file -- use name if provided, otherwise build it up
###############################################################################
    def create_rinex_obs_file(self):
        clean_name = ''
        if self.g.opts['rinex_file']:
            filename = self.g.opts['rinex_file']
            for c in filename:
                if c.isalnum() or c in [' ', '.', '/']:
                    clean_name = clean_name + c
            while clean_name.count("../"):
                # don't let us go upstairs
                clean_name = clean_name.replace("../", "./")
                # get rid of leading "./" combinations...
                clean_name = clean_name.lstrip("./")
            if filename != clean_name:
                print("changed requested file name",
                      filename, "to:", clean_name)
            filename = clean_name
        else:
            if self.g.opts['site_name']:
                sitename = self.g.opts['site_name']
                for c in sitename:
                    if c.isalnum() or c in [' ', '.', '/']:
                        clean_name = clean_name + c
                sitename = clean_name
            else:
                sitename = "NONE"
            yday = str(datetime.datetime.utcnow().timetuple().tm_yday)
            hour = int(datetime.datetime.utcnow().timetuple().tm_hour)
            hour_letter = chr(ord('a') + hour)
            year = \
                str(int(datetime.datetime.utcnow().timetuple().tm_year) - 2000)
            obs_filename = sitename + yday + hour_letter + "." + year + "o"
            self.g.obs_filename = obs_filename

            print("Attempting to create RINEX observations file:", obs_filename)

            if os.path.isfile(obs_filename):
                print(obs_filename,
                      "already exists!  Do you want to overwrite? (y/n):", end='')
                if input().lower().startswith('y'):
                    os.remove(obs_filename)
                else:
                    print("Exiting so you can try again...")
                    sys.exit(1)
            try:
                # Here we just create the file; we'll write to it elsewhere
                open(obs_filename, 'x').close()
            except:
                print("Couldn't create", obs_filename,
                      "!  Exiting so you can try again...")
                sys.exit(1)

###############################################################################
# obs_file_header -- assemble and return the file header at
# the start of the obs file
###############################################################################
    def obs_file_header(self):

        print()
        print("Writing RINEX observation file header...")

        # column count starts with 1.  header ID is columns 61-80
        # print(self.ruler)
        header = []
        string = "{:9.2f}{:11}{:<20}{:<20}{:<20}".format(2.11,
                                                         " ", "OBSERVATION", "GPS ", "RINEX VERSION / TYPE")
        header.append(string)
        date = datetime.date.today().strftime("%d %B %Y")

        string = "{:<20}{:<20}{:<20}{:<20}".format(self.g.PROG_NAME,
                                                   self.g.opts['operator'], date, "PGM / RUN BY / DATE")
        header.append(string)

        if self.g.opts['comment']:
            string = "{:<60}{:<20}".format("Comment", "COMMENT")
            header.append(string)
        string = "{:<60}{:<20}".format(self.g.opts['marker'],
                                       "MARKER NAME")
        header.append(string)
        string = "{:<60}{:<20}".format(self.g.opts['marker_number'],
                                       "MARKER NUMBER")
        header.append(string)
        # if not otherwise specified, get login name
        if self.g.opts['observer']:
            observer = self.g.opts['observer']
        else:
            observer = getpass.getuser()
        string = "{:<20}{:<40}{:<20}".format(observer,
                                             self.g.opts['agency'], "OBSERVER / AGENCY")
        header.append(string)

        # Receiver Info
        (rx_type, ch_opt, nav_ver, opts, ch_ver, ser_num) = self.Commands.QueryRID()

        # for receiver number, use in this priority: (1) opts[rx_number],
        # (2) if uZ, receiver serial number; (3) "NONE"
        if self.g.opts['rx_number']:
            rx_number = self.g.opts['rx_number']
        elif ser_num:
            rx_number = ser_num
        else:
            rx_number = "NONE"

        rxtype = "{} {}/{}".format(rx_type, ch_opt, opts)
        version = "{}/{}".format(nav_ver, ch_ver)
        string = "{:<20}{:<20}{:<20}{:<20}".format(
            rx_number, rxtype, version, "REC # / TYPE / VERS")
        header.append(string)

        if self.g.rx_ser_num:
            string = "{:<40}{:<20}{:<20}".format(
                "SN: " + ser_num, "", "COMMENT")
            header.append(string)

        # Antenna info
        string = "{:<20}{:<20}{:<20}{:<20}".format(
            self.g.opts['antenna_number'],
            self.g.opts['antenna_type'],
            "",	"ANT # / TYPE")
        header.append(string)

        # Position info

        [lat, lon, height] = self.g.current_fix.ddmmxxx_string_list()
        string = "{:<20}{:<20}{:<20}{:<20}".format(lat, lon, height, "COMMENT")
        header.append(string)

        [x, y, z] = self.g.current_fix.xyz_float_list()
        string = "{:14.4f}{:14.4f}{:14.4f}{:<18}{:<20}".format(x, y, z,
                                                               "", "APPROX POSITION XYZ")
        header.append(string)

        string = "{:14.4f}{:14.4f}{:14.4f}{:<18}{:<20}".format(
            self.g.opts['antenna_height'],
            self.g.opts['antenna_east'],
            self.g.opts['antenna_north'], "",
            "ANTENNA: DELTA H/E/N")
        header.append(string)

        string = "{:6d}{:6d}{:6s}{:<42}{:<20}".format(
            1, 1, "", "", "WAVELENGTH FACT L1/2")
        header.append(string)

        string = "{:6d}{:<54}{:<20}".format(
            9, "    C1    P1    P2    L1    L2    D1    D2    S1    S2",
            "# / TYPES OF OBSERV")
        header.append(string)

        string = "{:10.3f}{:<50}{:<20}".format(
            self.g.opts['msg_rate'], "", "INTERVAL")
        header.append(string)

        # First observation time

        header.append(self.first_obs_time())

        string = "{:<60}{:<20}".format("", "END OF HEADER")
        header.append(string)

        with open(self.g.obs_filename, 'a') as writer:
            for i in header:
                writer.write(i + "\n")

        return

###############################################################################
# first_obs_time -- create header line for first observation time
###############################################################################
    def first_obs_time(self):

        (sec, minute, hour, mday, mon, year,
         weeknum, yday) = self.g.first_observation.time_list

        timestring = "{:2s}{:4d}".format(' ', int(year))
        timestring += "{:4s}{:02d}".format(' ', int(mon))
        timestring += "{:4s}{:02d}".format(' ', int(mday))
        timestring += "{:4s}{:02d}".format(' ', int(hour))
        timestring += "{:4s}{:02d}".format(' ', int(minute))
        timestring += "{:13.7f}".format(float(sec))
        timestring += "{:5s}".format(' ')
        timestring += "{:3s}".format("GPS")
        timestring += "{:9s}".format(' ')  # blanks to col 60; should be 2?
        timestring += "TIME OF FIRST OBS"   # takes us to col 77

        return timestring

###############################################################################
# obs_epoch_header -- assemble and return the observation header before
# each stanza of mben records
###############################################################################
    def obs_epoch_header(self, verbose=False):

        # get PRN list
        prn_list = ''
        count = 0
        for i in self.g.mben_list:
            if i:
                count += 1
                tmp = i['prn']
                prn_list += 'G{:02d}'.format(i['prn'])
        prn_list = '{:3d}'.format(count) + prn_list

        # now get pben records for position and epoch
        week = self.g.gps_week
        tow = self.g.gps_tow
        navx = self.g.current_pben['navx']
        navy = self.g.current_pben['navy']
        navz = self.g.current_pben['navz']

        (sec, minute, hour, mday, mon, year,
         weeknum, yday) = GPS_Time(week, tow).time_list
        timestring = \
            "{:1s}{:02d}{:1s}{:02d}{:1s}{:02d}{:1s}{:02d}{:1s}{:02d}{:11.7f}". \
            format(
                "", int(year) - 2000, "", int(mon), "", int(mday), "", int(hour),
                "", int(minute), float(sec))

        flagstring = \
            "{:2s}{:1d}".format(
                "", 0)  # need to figure out what to do with flag

        header = timestring + flagstring + prn_list

        with open(self.g.obs_filename, 'a') as writer:
            writer.write(header + "\n")

        if verbose:
            print(header)

        return header

###############################################################################
# obs_epoch -- create list of observables, one for each satellite
# 9 measurements: C1 P1 P2 L1 L2 D1 D2 S1 S2
# I get confused so C and P are (pseudo)range, L is phase. C/A phase not used
    def obs_epoch(self, verbose):
        for i in self.g.mben_list:
            if i:
                counter = self.g.mben_list.index(i)
                j = self.g.mben_flag_list[counter]

                # line 1
                l1p1 = "{:14.3f}{:1d}{:1d}".format(
                    i['ca_range'], j['ca_range_lli'], j['ca_range_sbyte'])

                l1p2 = "{:14.3f}{:1d}{:1d}".format(
                    i['l1_range'], j['l1_range_lli'], j['l1_range_sbyte'])

                l1p3 = "{:14.3f}{:1d}{:1d}".format(
                    i['l2_range'], j['l2_range_lli'], j['l2_range_sbyte'])

                l1p4 = "{:14.3f}{:1d}{:1d}".format(
                    i['l1_phase'], j['l1_phase_lli'], j['l1_phase_sbyte'])

                l1p5 = "{:14.3f}{:1d}{:1d}".format(
                    i['l2_phase'], j['l2_phase_lli'], j['l2_phase_sbyte'])

                # line 2
                l2p1 = "{:14.3f}{:1d}{:1d}".format(
                    i['l1_dopp'], j['l1_dopp_lli'], j['l1_dopp_sbyte'])

                l2p2 = "{:14.3f}{:1d}{:1d}".format(
                    i['l2_dopp'], j['l2_dopp_lli'], j['l2_dopp_sbyte'])

                l2p3 = "{:14.3f}".format(i['l1_snr'])
                l2p4 = "{:14.3f}".format(i['l2_snr'])

                line1 = l1p1 + l1p2 + l1p3 + l1p4 + l1p5
                line2 = l2p1 + l2p2 + l2p3 + l2p4

                with open(self.g.obs_filename, 'a') as writer:
                    writer.write(line1 + "\n")
                    writer.write(line2 + "\n")

        return

# end of rinex.py
