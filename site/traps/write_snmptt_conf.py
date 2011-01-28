"""
This file is part of SnakeTrap.

SnakeTrap is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SnakeTrap is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SnakeTrap.  If not, see <http://www.gnu.org/licenses/>.
"""

from traps.models import *
from traps.error_handling import *
import os

# Write snmptt configuration file
class writeSnmpttConf:
	def __init__(self):
		self.CErr = CustomError()

	def writeConf(self, MSettings):
		self.output_snmptt_def = MSettings.output_snmptt_def
		snmptt_def_fh = open(self.output_snmptt_def, "w")
		snmptt_def_list	= Snmptt_def.objects.all()
		for snmptt_def in snmptt_def_list:
			snmptt_def_fh.write('EVENT ' + str(snmptt_def.oid_name) + ' ' + str(snmptt_def.oid) + ' "' + str(snmptt_def.event_type) + '" ' + str(snmptt_def.severity) + '\n')
			action = snmptt_def.action_name
			if str(action) != 'None':
				commandline = action.commandline
				arguments = snmptt_def.argument_set.all()
				for arg in arguments:
					arg_nr = arg.argument_nr
					commandline = str(commandline).replace("$ARG" + str(arg_nr) + "$", arg.argument)
				snmptt_def_fh.write('EXEC ' + str(MSettings.action_dir) + '/' + str(commandline) + '\n')
			snmptt_def_fh.write('FORMAT ' + str(snmptt_def.format) + '\n')
			snmptt_def_fh.write('SDESC\n' + str(snmptt_def.description) + '\nEDESC\n')
			
						
