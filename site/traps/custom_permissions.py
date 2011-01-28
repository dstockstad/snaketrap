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

# Permissions
class SnakeTrapPermissions:
	def __init__(self, request):
		self.user = request.user
		self.user_id = self.user.id
		

	def getAllPermissions(self):
		self.perm_list = RegexPermission.objects.all().order_by('user')
		return(self.perm_list)

	def filterResult(self, list, table='traps'):
		# Don't filter anything if user is staff
		if self.user.is_staff:
			return list
		if table == 'traps':
			available_columns = ['severity','hostname']
		elif table == 'unknown_traps':
			available_columns = ['hostname']
		# Get all permission for the user
		perm_list = RegexPermission.objects.filter(user=self.user_id).order_by('column')
		i = 0
		perms = {}
		# Sort permission into dictionary by column as key
		for perm in perm_list:
			if str(perm.column) in perms:
				perms[str(perm.column)].append(perm.regex)
			else:
				perms[str(perm.column)] = [perm.regex]

		# Loop over dictionary and when multiple regular expressions exists for the same column, encase inside () and set OR condition as opposed to AND which would get empty result
		for perm in perms.keys():
			if available_columns.count(perm) != 0:
				string = ''
				params_list = []
				for regex in perms[str(perm)]:
					string = str(string) + " OR " + str(perm) + " ILIKE %s"
					params_list.append("%" + str(regex) + "%")
				where_string = "(" + str(string[4:]) + ")"

				list = list.extra(where=[where_string], params=params_list)
		return list
