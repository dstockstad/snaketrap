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
from traps.views import Arguments
from traps.pagination import piston_paginator
class SnaketrapApi(BaseHandler):
	def read(self, request, requested_info='', search_column='', search_type='', query=''):
		methods_allowed = ('GET',)
		Search = CustomSearch()
		args = Argument()

		# These require try statements since they are integer (would otherwise crash if string was inserted)
		try:
			args.pagesize = int(request.GET.get('pagesize', 100))
		except:
			args.pagesize = 100
		try:
			args.page = int(request.GET.get('page', 1))
		except:
			args.page = 1
	
		args.search_column, args.search_type, args.query = search_column, search_type, query

		if len(requested_info) == 0:
			return HttpResponse("You didn't specify what you want, showing some examples on what you can do:<br /> " + 
				"api/traps - show all traps<br />" + 
				"api/snmptt_def - show all snmptt definitions. only works if your user is staff<br />" + 
				"api/traps/?format=xml - show all traps but format it as xml instead of json. format can be used on all info<br />" +
				"api/traps/column/operator/query - search syntax, examples: <br />" +
				"api/traps/severity/eq/CRITICAL - show traps with where column severity is CRITICAL<br />" +
				"api/traps/severity|||hostname/eq|||eq/CRITICAL|||host1.example.org - show traps where column severity is CRITICAL and column hostname is host1.example.org<br /><br />" +
				"The following values are valid for column and when information shown is traps:<br />" +
				"eventname, trapoid, enterprise, community, hostname, agentip, category, severity, uptime, traptime, formatline<br /><br />" +
				"The following values are valid for column when information shown is snmptt_def:<br />" +
				"oid, oid_name, event_type, severity, format, description, action_name, date_added<br /><br />" +
				"The following are valid operators:<br />" +
				"eq, neq, like, nlike, gt, lt, gte, lte, null, nnull<br /><br />" +
				"Not all search types go with all search columns so just use trial and error and you'll see what works<br /><br />" +
				"Results will be limited to 100 by default, set pagesize=0 to show all results like so: api/traps/?pagesize=0"
			)

		elif requested_info == 'traps':
			# Get permissions
			perms = SnakeTrapPermissions(request)
			
			order = str(request.GET.get('order', 'id'))
			trap_list = Trap.objects.order_by(str(order))

			# Apply permissions
			trap_list = perms.filterResult(trap_list)

			# Apply search
			trap_list = Search.f_search(trap_list, args)

			# Apply pagination
			trap_list = piston_paginator(trap_list, args)

			return { 'trap': trap_list, 'data_length': trap_list.count() }
		elif requested_info == 'snmptt_def':
			if request.user.is_staff == False:
				return HttpResponseForbidden("You don't have the necessary privileges")

			order = str(request.GET.get('order', 'oid'))
			snmptt_def = Snmptt_def.objects.order_by(str(order))

			# Apply search
			snmptt_def = Search.f_search(snmptt_def, args)

			# Apply pagination
			snmptt_def = piston_paginator(snmptt_def, args)

			return { 'snmptt_def': snmptt_def, 'data_length': snmptt_def.count() }
