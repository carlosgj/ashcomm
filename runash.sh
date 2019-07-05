#!/bin/bash

#################################  ashcomm.py  #################################
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

./ashcomm.py \
--serport=/dev/ttyS4 \
--baud=115200 \
--msg_rate=30 \
--site=N8UR \
--operator='John Ackermann' \
--marker=DECK \
--marker_number=21A34 \
--observer=jra \
--agency="Three Letter Acronym" \
--rx_num=143A221 \
--antenna_number="1" \
--antenna_type="TRM41249.00" \
--antenna_height=1.5 \
--antenna_east=0 \
--antenna_north=0 \
--verbose=False
