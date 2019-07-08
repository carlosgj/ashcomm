
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
libraries or modules that are not part of a standard Python distribution,
other than xmodem (install with "pip3 install xmodem") which is only
needed for working with the receiver's internal file storage.  I haven't 
tried it, but there's no reason ashtech.py shouldn't run on a Windows
system that has Python3 installed.

So far, I've tested the program on a standard Z12 receiver and on a
Z12-REF reference station.  I have a micro-Z reference station and
will try to test that soon.

At present, the program is limited to streaming data from the receiver
and converting it to RINEX output files.  I want to add the ability to
download and manage files stored in the receiver.  That will take a bit
more work because the Z12 and micro-Z have very different file systems
(and my Z12 died last night -- but a replacement is on its way).

ashcomm.py has a number of command line options, most of which are used to
populate the RINEX report header.  The "runash.sh" shell script
includes them all and can be used as a template.  At present, the
RINEX file information (site name, project, etc.) are written to
the RINEX file header, but not uploaded into the receiver.  e.g.,
if you set the sitename via ashcomm.py command line, that name
will be used by the program, but the receiver won't know about it.
This may change.

To run the program, type "ashcomm.py" followed by the desired options, or
use the runash.sh shell script after customizing it for your needs.
