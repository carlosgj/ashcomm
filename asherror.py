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

############################   asherror.py    ##################################

import sys
import signal

from ashserial import *
from ashcommand import *
from ashutil import *
from ashmessage import *
from ashposition import *
from ashtime import *
from ashrinex import *
from ashglobal import *
from ashopt import *


class AshtechError:

    def __init__(self, original_sigint, g):
        self.original_sigint = original_sigint
        self.g = g

###############################################################################
# exit_handler -- grab CTRL+C and exit gracefully
###############################################################################

    def exit_handler(self, signum, frame):

        def real_handler(signum, frame):
            # restore the original signal handler
            signal.signal(signal.SIGINT, self.original_sigint)
            self.stats()
            sys.exit(1)
            try:
                if input("\nReally quit? (y/n)> ").lower().startswith('y'):
                    sys.exit(1)
            except KeyboardInterrupt:
                stats()
                sys.exit(1)

            # restore the exit gracefully handler here
            signal.signal(signal.SIGINT, real_handler)

        real_handler(signum, frame)

###############################################################################
# stats -- prints session details for the exit handler
###############################################################################
    def stats(self):
        print()
        string = "Exiting program..."
        if self.g.start_time:
            duration = datetime.datetime.utcnow() - self.g.start_time
            string += " Run time: {}".format((str(duration))[:-5])
            if self.g.obs_epoch_count:
                string += "; wrote {} epochs to {}".format(
                    self.g.obs_epoch_count, self.g.obs_filename)
        print(string)
        print()
