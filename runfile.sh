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

./ashfile.py \
--serport=/dev/ttyS4 \
--baud=115200 \
--verbose=False
