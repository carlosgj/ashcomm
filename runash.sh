#!/bin/bash

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

#############################   runash.sh    ###################################
#
# An example shell script to run ashcomm showing all the available 
# command line options.  NOTE: in-line comments MUST be surrounded 
# by back-ticks (`)!

./ashcomm.py \
--serport=/dev/ttyS4 \
--baud=115200 \
--msg_rate=30 \
--site=N8UR \
--operator='John Ackermann' \
--marker=DECK \
--marker_number=21A34 \
--comment="Test Comment"	`# prints in obs file header; max 60 characters` \
--observer='' 		`# if empty, use login name` \
--agency="Three Letter Acronym" \
--rx_num='' `# if empty, use uZ SN if available, otherwise "NONE` \
--antenna_number="1" \
--antenna_type="TRM41249.00" \
--antenna_height=1.5 \
--antenna_east=0 \
--antenna_north=0 \
--rinex_file=''	`# if empty, build filename from site name or "NONE"` \
--verbose=False
