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

from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden

import sys
import re

from piston.handler import BaseHandler
from piston.utils import rc, throttle

from traps.models import * 
from traps.custom_permissions import *
from traps.custom_search import *
from traps.error_handling import CustomError

class SnaketrapHandler(BaseHandler):
	def read(self, request):
		methods_allowed = ('GET',)
		Search = CustomSearch()
		requested_info = str(request.GET.get('info', ''))
		format = str(request.GET.get('format', 'json'))

		search_column = str(request.GET.get('search_column',''))
		search_type = str(request.GET.get('search_type',''))
		query = str(request.GET.get('query',''))


		if len(requested_info) == 0:
			return HttpResponseForbidden("You didn't specify what info you want, add info=<traps|snmptt_def> to your url")
		elif requested_info == 'traps':
			# Get permissions
			perms = SnakeTrapPermissions(request)
			
			order = str(request.GET.get('order', '-traptime'))
			trap_list = Trap.objects.order_by(str(order))

			# Apply permissions
			trap_list = perms.filterResult(trap_list)

			# Apply search
			trap_list = Search.f_search(trap_list, search_column, search_type, query)

			return { 'trap': trap_list, 'data_length': len(trap_list) }
		elif requested_info == 'snmptt_def':
			if request.user.is_staff == False:
				return HttpResponseForbidden("You don't have the necessary privileges")
			order = str(request.GET.get('order', 'oid'))
			snmptt_def = Snmptt_def.objects.order_by(str(order))
			snmptt_def = Search.f_search(snmptt_def, search_column, search_type, query)

			return { 'snmptt_def': snmptt_def, 'data_length': len(snmptt_def) }
