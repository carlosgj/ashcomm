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

#############################   ashopt.py    ###################################

import argparse

from ashglobal import *

###############################################################################


class AshtechOpts:

    ###############################################################################
    def __init__(self, g):
        self.g = g

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
        args.add_argument('-v', '--verbose', default='False', type=str2bool,
                          nargs='?', const=True, help='be verbose')

        args.add_argument('-s', '--serport', default='/dev/ttyS0', type=str,
                          help='host computer serial port')
        args.add_argument('-b', '--baud', default=115200, type=int,
                          help='baud rate')
        args.add_argument('-p', '--hwport', default='A', type=str,
                          help='receiver hardware port')
        args.add_argument('-f', '--rinex_file', default='', type=str,
                          help='file name -- blank to auto-generate; \"NONE\" to skip')

        # receiver configuration options
        args.add_argument('--elmask', default=10, type=int,
                          help='elevation mask')
        args.add_argument('--dopmask', default=10, type=int,
                          help='dop mask')
        args.add_argument('--site_name', default='TEST', type=str,
                          help='site name \(max 4 char\)')
        args.add_argument('--project_name', default='', type=str,
                          help='project name \(max 20 char\)')
        args.add_argument('--msg_rate', default=20, type=int,
                          help='message output rate (default 20 seconds)')

        # RINEX field options
        args.add_argument('--operator', default='', type=str,
                          help='operator name')
        args.add_argument('--comment', default='', type=str,
                          help='optional comment, max 60 characters')
        args.add_argument('--marker', default='', type=str,
                          help='marker name')
        args.add_argument('--marker_number', default='', type=str,
                          help='marker number')
        args.add_argument('--observer', default='', type=str,
                          help='observer')
        args.add_argument('--agency', default='', type=str,
                          help='agency')

        args.add_argument('--rx_number', default='', type=str,
                          help='receiver number')
        args.add_argument('--antenna_number', default='', type=str,
                          help='antenna number \(from WGS database\)')
        args.add_argument('--antenna_type', default='', type=str,
                          help='antenna type \(from WGS database\)')

        args.add_argument('--antenna_height', default='', type=float,
                          help='antenna elevation')
        args.add_argument('--antenna_east', default='', type=float,
                          help='antenna easting')
        args.add_argument('--antenna_north', default='', type=float,
                          help='antenna northing')

        self.g.opts = vars(args.parse_args())

        return
