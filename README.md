
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

So far, I've tested the program on a standard Z12 receiver, a
Z12-REF reference station, and a micro-Z reference station.

At present, the program is limited to streaming data from the receiver
and converting it to RINEX observation files.  I want to add the ability 
to download and manage files stored in the receiver.  That will take a 
bit more work because the Z12 and micro-Z have very different file 
systems (and my Z12 died last night -- but a replacement is on its 
way).  I might also look at adding RINEX navigation file output, but
(a) I don't know anything about it; (b) it looks complicated; and
(c) I'm not sure what I would use it for.

ashcomm.py has a number of command line options, most of which are
used to populate the RINEX report header.  At a minimum, you will
need to specify the serial port (e.g., for Linux, "/dev/tytS0"),
and the baud rate.  To run the program, type "ashcomm.py" followed 
by the desired options

The provided "runash.sh" shell script runs the program, including all
the available options (with mainly made-up values); it can be used as 
a template for your needs.  Options setting RINEX data fields (site 
name, project, etc.) are written to the RINEX file header, but not 
uploaded into the receiver.  e.g., if you set the site name via 
ashcomm.py command line, that name will be used by the program, 
but the receiver won't know about it.  This may change.

There is a command-line option for the name of the output file.  If it
is set, that name will be used after deleting any illegal characters.
If the file name is not set, ashcomm will build one in the recommended 
format from the 4-character site name, the day of the year, and the 
hour.  If the site name is not provided, it is set to "NONE" and that 
is used in the file name.  If the program is about to overwrite an 
existing file, you will be warned and given an opportunity to bail out 
before doing any damage.

The program writes a few lines of information to STDOUT and provides an
ever-growing line of dots to show progress.  Setting the verbose option
causes a bunch of debugging information to be printed to STDOUT, most of
which is variable printouts that I used for debugging.

