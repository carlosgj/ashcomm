
#################################  ashcomm.py  #################################

Copyright 2019 by John Ackermann, N8UR jra@febo.com https://febo.com
Version number can be found in the ashglobal.py file

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
Software to communicate with Ashtech GPS receivers via serial port.

################################################################################

ashcomm.py is a program to collect data from Ashtech Z12 and micro-Z GPS
receivers and generate reports in RINEX 2.11 format that can be post-
processed to determine precise location and timing information.

It is written in Python3 on a Linux platform.  It does not use any
libraries or modules that are not part of a standard Python distribution.
There's no reason it shouldn't run on a Windows system that has Python3
installed.

ashcomm.py has a number of command line options, most of which are used to
populate the RINEX report header.  The "runash.sh" shell script
includes them all and can be used as a template.

To run the program, type "ashcomm.py" followed by the desired options, or
use the runash.sh shell script after customizing it for your needs.
