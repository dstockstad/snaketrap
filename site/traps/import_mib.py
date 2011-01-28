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
import subprocess
import shlex
import syslog

# Import MIB
class ImportMib:
	def __init__(self, MSettings, mode, mibfile):
		self.CErr = CustomError()
		self.MImOut = MibImportOutput()
		self.MSettings = MSettings
		self.mode = str(mode)
		self.mibfile = str(mibfile)
		self.modes = ['add','readd','delete']
		self.in_mib = str(MSettings.snmp_mib_dir) + '/' + str(mibfile)
		self.out_mib = str(MSettings.temp_dir) + '/' + str(mibfile)

	# Run Commands
	def runCommand(self, command):
		proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		s_out, s_err = proc.communicate()
		list_out = s_out.split("\n")
		list_err = s_err.split("\n")
		return(list_out, list_err)

	def initial_checks(self):
		if self.mibfile == None or self.mode == None or len(self.mibfile) == 0 or len(self.mode) == 0:
			self.CErr.object = 'Mode and/or Mibfile'
			self.CErr.custom_error_type = 'Unspecified'
			return(self.CErr)

		if self.modes.count(self.mode) == 0:
			self.CErr.object = 'Mode'
			self.CErr.custom_error_type = 'Invalid'
			return(self.CErr)

		if os.path.isfile(self.MSettings.snmpttconvertmib) == False:
			self.CErr.object = 'snmpttconvertmib (' + str(self.MSettings.snmpttconvertmib) + ')'
			self.CErr.custom_error_type = 'DoesntExist'
			return(self.CErr)

		return(None)

	def convert_mib(self):
		if os.path.isfile(str(self.in_mib)):
			if os.path.exists(str(self.out_mib)):
				os.remove(str(self.out_mib))
		syslog.syslog("convert_mib was called with in_mib " + str(self.in_mib) + " and out_mib " + str(self.out_mib))
		self.MImOut.output, self.MImOut.errors = self.runCommand('export MIBDIRS=' + str(self.MSettings.snmp_mib_dir) + ';' + str(self.MSettings.snmpttconvertmib) + ' --in=' + str(self.in_mib) + ' --out=' + str(self.out_mib))


	def commit_snmptt_def_to_db(self):
		if len(self.name) > 0 and len(self.oid) > 0 and len(self.event_type) > 0 and len(self.severity) > 0 and len(self.description) > 0 and self.get_description == 0 and len(self.format) > 0:
			self.description = "\n".join(self.description).replace("'","\\'")
			self.format = str(self.format).replace("'","\\'")
			q = Snmptt_def(oid_name=str(self.name), oid=str(self.oid), event_type=str(self.event_type), severity=str(self.severity), format=str(self.format), description=str(self.description))
			q.save()
			q = Snmptt_def.objects.filter(oid=str(self.oid))
			if len(q) == 0:
				self.MImOut.failed.append("Failed importing " + str(self.oid))
			else:
				self.MImOut.succeeded.append("Succeeded importing " + str(self.oid))

	def delete_oid_from_db(self):
		Snmptt_def.objects.filter(oid=str(self.oid)).delete()
		q = Snmptt_def.objects.filter(oid=str(self.oid))
		if len(q) > 0:
			self.MImOut.failed.append("Failed to delete " + str(self.oid))
		else:
			self.MImOut.failed.append("Succeeded deleting " + str(self.oid))

	def parse_snmptt_file(self):
		fh_snmptt_file = open(str(self.out_mib), "r")
		self.data = fh_snmptt_file.read().split("\n")
		fh_snmptt_file.close()

		self.name, self.oid, self.event_type, self.severity, self.description, self.get_description, self.conf_script, self.script_db, self.conf_script_args, self.args_written = '','','','',[],0,'',None,None,[]
		for line in self.data:
			if line.startswith("EVENT ") and len(shlex.split(str(line))) == 5:
				list = shlex.split(str(line))
				self.name, self.oid, self.event_type, self.severity = (list[1], list[2], list[3], list[4])
			elif line.startswith("FORMAT"):
				self.format = " ".join(str(line).split(" ")[1:])
			elif line.startswith("EDESC"):
				self.get_description = 0
			elif self.get_description == 1:
				self.description.append(line)
			elif line.startswith("SDESC"):
				self.get_description = 1
			if line.startswith("EDESC"):
				if self.mode == 'delete':
					self.delete_oid_from_db()
				elif self.mode == 'add':
					self.commit_snmptt_def_to_db()
				elif self.mode == 'readd':
					self.delete_oid_from_db()
					self.commit_snmptt_def_to_db()
				self.name, oid, self.event_type, self.severity, self.description, self.get_description, self.conf_script, self.script_db, self.conf_script_args = '','','','',[],0,'',None,None

