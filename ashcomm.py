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

#############################   ashcomm.py    ##################################

import time
import signal
import datetime

from ashserial import *
from ashcommand import *
from ashutil import *
from ashmessage import *
from ashposition import *
from ashtime import *
from ashrinex import *
from ashglobal import *
from ashopt import *
from asherror import *

###############################################################################
# MAIN PROGRAM
###############################################################################


def main():
    g = AshtechGlobals()
    option = AshtechOpts(g)
    option.getargs()
    verbose = g.opts['verbose']
    if verbose:
        print("Verbose mode")

    # store the original SIGINT handler
    original_sigint = signal.getsignal(signal.SIGINT)
    error = AshtechError(original_sigint, g)
    signal.signal(signal.SIGINT, error.exit_handler)

    Serial = AshtechSerial(g.opts['serport'],
                           g.opts['baud'], g.opts['hwport'], verbose)
    Commands = AshtechCommands(Serial, g, verbose)
    RINEX = Rinex(Commands, g, verbose)
    Messages = AshtechMessages(Serial, Commands,
                               g, RINEX, verbose)

    Serial.Open()

    Commands.SetCommand("OUT,A", verbose=0)  # turn off output
    Serial.reset_input()						# clean the sluices
    Serial.reset_output()
    time.sleep(1)

    Commands.QueryRID(verbose=True)

#	GetZ12Files()

    g.start_time = datetime.datetime.utcnow()
    RINEX.create_rinex_obs_file()

    print("Waiting for data; it may take a while...")

    gps_week = Messages.GetGPSWeek(verbose)
    time.sleep(1)

    # set message rate
    Commands.SetCommand("RCI," + str(g.opts['msg_rate']))
    time.sleep(1)
    Commands.SetCommand("OUT,A,PBN,MBN,BIN", verbose)
    time.sleep(1)
    Messages.MsgSwitch(verbose)
    time.sleep(1)
    Serial.Close()


if __name__ == '__main__':
    main()
