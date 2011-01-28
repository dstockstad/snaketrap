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

from django.conf import settings

# Read Settings
class SnakeTrapSettings:
	def __init__(self):
		# Read settings
		self.action_dir, self.temp_dir, self.snmp_mib_dir, self.snmpttconvertmib, self.output_snmptt_def = self.read_settings(
		('action_dir',
		'temp_dir',
		'snmp_mib_dir',
		'snmpttconvertmib',
		'output_snmptt_def')
		)
		
	def read_settings(self, directives):
		mysettings = []
		for directive in directives:
			setting = str(settings.SNAKETRAP[str(directive)])
			mysettings.append(str(setting))
		return(mysettings)

