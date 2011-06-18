#!/usr/bin/env python
#
# You need to create and configure /etc/snaketrap2nagios.conf before you use this script. You should have received an example configuration with snaketrap in the actions dir.
# You need to run this on the same machine as Nagios.
#
# -*- coding: utf-8 -*-

"""sendTrapToNagios.py"""

__author__ = "Dag Stockstad"
__copyright__ = "GNU General Public License"
__version__ = "0.2"
__date__ = "$Date: 2011-05-05"

# System requirements
# Python (tested with 2.4)

import os
import sys
import re
import syslog
import ConfigParser
import time

if len(sys.argv) < 5:
	print "usage: " + sys.argv[0] + " <fqdn/ip> <trap description> <return code> <output>"
	sys.exit(2)

# Check arguments
if isinstance(sys.argv[1], str) != True:
	syslog.syslog(sys.argv[1] + " should be a string")
	sys.exit(0)
if isinstance(sys.argv[2], str) != True:
	syslog.syslog(sys.argv[1] + " should be a string")
	sys.exit(0)

try:
	return_code = int(sys.argv[3])
except:
	syslog.syslog(str(sys.argv[3]) + " should be an integer")
	sys.exit(0)

if isinstance(sys.argv[4], str) != True:
	syslog.syslog(sys.argv[1] + " should be a string")
	sys.exit(0)



fqdn = str(sys.argv[1])
trap_description = str(sys.argv[2])
output = str(sys.argv[4])

config = ConfigParser.RawConfigParser()
config.read('/etc/snaketrap2nagios.conf')

try:
	nagios_pipe = config.get('general', 'nagios_pipe')
except:
	syslog.syslog('No pipe configured, exiting.')
	sys.exit(0)

try:
	host_mapping = config.get('mappings', str(fqdn))
except:
	host_mapping = None

if host_mapping != None:
	fqdn = str(host_mapping)

fh_pipe = open(str(nagios_pipe), "a")
fh_pipe.write('[' + str(time.time()) + '] PROCESS_SERVICE_CHECK_RESULT;' + str(fqdn) + ';' + str(trap_description) + ';' + str(return_code) + ';' + str(output))
fh_pipe.close
