# -*- coding: utf-8 -*-

import sys

################################  N8UR ASHCOMM  ################################
#
#   Copyright 2019 by John Ackermann, N8UR jra@febo.com https://febo.com
#   Version number can be found in the ashglobal.py file
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#   Software to communicate with Ashtech GPS receivers via serial port.
################################################################################

#############################   ashgrid.py    ##################################
#
# From Walter Underwood K6WRU in a Stack Overflow posting:
# https://tinyurl.com/yylktpvq
# Convert latitude and longitude to Maidenhead grid locators.
#
# Arguments are in signed decimal latitude and longitude. For example,
# the location of my QTH Palo Alto, CA is: 37.429167, -122.138056 or
# in degrees, minutes, and seconds: 37° 24' 49" N 122° 6' 26" W


def to_grid(dec_lat, dec_lon):
    upper = 'ABCDEFGHIJKLMNOPQRSTUVWX'
    lower = 'abcdefghijklmnopqrstuvwx'
    if not (-180 <= dec_lon < 180):
        sys.stderr.write(
            'longitude must be -180<=lon<180, given %f\n' % dec_lon)
        sys.exit(32)
    if not (-90 <= dec_lat < 90):
        sys.stderr.write('latitude must be -90<=lat<90, given %f\n' % dec_lat)
        sys.exit(33)  # can't handle north pole, sorry, [A-R]

    adj_lat = dec_lat + 90.0
    adj_lon = dec_lon + 180.0

    grid_lat_sq = upper[int(adj_lat/10)]
    grid_lon_sq = upper[int(adj_lon/20)]

    grid_lat_field = str(int(adj_lat % 10))
    grid_lon_field = str(int((adj_lon/2) % 10))
    grid = grid_lat_field + grid_lon_field

    adj_lat_remainder = (adj_lat - int(adj_lat)) * 60
    adj_lon_remainder = ((adj_lon) - int(adj_lon/2)*2) * 60
    remainder = adj_lat_remainder + adj_lon_remainder

    grid_lat_subsq = lower[int(adj_lat_remainder/2.5)]
    grid_lon_subsq = lower[int(adj_lon_remainder/5)]
    subsq = grid_lat_subsq + grid_lon_subsq

    fullgrid = grid + remainder + subsq

    return fullgrid
