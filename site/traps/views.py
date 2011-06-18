
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

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout

from django.http import HttpResponse, HttpResponseRedirect
from traps.models import *
from traps.signals import *
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext
from django import forms
from django.core.context_processors import csrf
from django.conf import settings
from django.core.validators import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.defaultfilters import stringfilter

# Custom classes
from traps.validation import *
from traps.error_handling import *
from traps.forms import *
from traps.import_mib import *
from traps.write_snmptt_conf import *
from traps.custom_settings import *
from traps.custom_permissions import *
from traps.custom_search import *
from traps.pagination import * 
from traps.helpers import *

# Non django modules
from string import replace
import os
import sys
import subprocess
import shlex
import datetime
import time

# Login
def snaketrap_authentication(request):
	username = request.POST.get('username', None)
	password = request.POST.get('password', None)
	user = authenticate(username=str(username), password=str(password))
	if user is not None:
		if user.is_active:
			login(request, user)
			trap_listing(request)
		else:
			print "Your account has been disabled!"
	else:
		print "Your username and password were incorrect."

# Logout
def logout_view(request):
	logout(request)
	return HttpResponseRedirect(str(settings.LOGIN_URL))

# URL Arguments
class Arguments:
	def __init__(self):
		self.search_column = ''
		self.search_type = ''
		self.query = ''
		self.order = ''
		self.pagesize = 0

# Views
@login_required
def about(request):
	snaketrap_version = SnakeTrapInfo.objects.get(pk='version')
	return render_to_response('traps/about.html', {'snaketrap_version': snaketrap_version}, context_instance=RequestContext(request))

@login_required
def upload_file(request):
	SSettings = SnakeTrapSettings()
	if request.method == 'POST':
		form = UploadFileForm(request.POST, request.FILES)
		if form.is_valid():
			fh = open(str(SSettings.snmp_mib_dir) + '/' + str(request.FILES['file'].name), "w")
			fh.write(request.FILES['file'].read())
			fh.close()
			IMib = ImportMib(SSettings, 'add', str(request.FILES['file'].name))
			CErr = IMib.initial_checks()
			if CErr != None:
				return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
			IMib.convert_mib()
			IMib.parse_snmptt_file()
			summary = []
			for out in IMib.MImOut.output:
				if out.startswith("Total translations"):
					summary.append(out)
				elif out.startswith("Successful translations"):
					summary.append(out)
				elif out.startswith("Failed translations"):
					summary.append(out)
			return render_to_response('traps/mib_upload.html',{"file": request.FILES['file'].name, "succeeded": IMib.MImOut.succeeded, "failed": IMib.MImOut.failed,"errors": IMib.MImOut.errors,"output": IMib.MImOut.output,"summary": summary},context_instance=RequestContext(request))
		else:
			form = UploadFileForm()
			return(form)
	else:
		form = UploadFileForm()
		return(form)

@login_required
def trap_listing(request):
	# Get all arguments
	args = Arguments()

	# Get permissions
	perms = SnakeTrapPermissions(request)
	Search = CustomSearch()

	args.search_column = str(request.GET.get('search_column', ''))
	args.search_type = str(request.GET.get('search_type', ''))
	args.query = request.GET.getlist('query')
	if len(args.query) == len(args.search_type.split(",")):
		args.query = ",".join(args.query)
	else:
		if len(args.query) > 0:
			fquery = ''
			for query in args.query:
				if fquery != '':
					fquery = fquery + "|||" + str(query)
				else:
					fquery = str(query)
			args.query = fquery
		else:
			args.query = ''

	args.order = str(request.GET.get('order', '-traptime'))

	# These require try statements since they are integer (would otherwise crash if string was inserted)
	try:
		args.pagesize = int(request.GET.get('pagesize', 20))
	except:
		args.pagesize = 20
	try:
		args.page = int(request.GET.get('page', 1))
	except:
		args.page = 1

	if args.pagesize > 3000:
		CErr = CustomError()
		CErr.object, CErr.custom_error_type = 'Screwing Around Error', 'Stop messing with my system or suffer my wrath!!!'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all objects and order by args.order
	trap_list = Trap.objects.all().order_by(str(args.order))

	# Apply permissions
	trap_list = perms.filterResult(trap_list)

	# Apply search
	trap_list = Search.f_search(trap_list, args)

	# Get time of first and last result
	try:
		first_trap = Trap.objects.all().order_by('traptime')[0]
		last_trap = Trap.objects.all().order_by('-traptime')[0]
		first_trap_year, first_trap_month, first_trap_day = first_trap.traptime.year, first_trap.traptime.month, first_trap.traptime.day
		last_trap_year, last_trap_month, last_trap_day = last_trap.traptime.year, last_trap.traptime.month, last_trap.traptime.day
	except:
		first_trap_year, first_trap_month, first_trap_day = datetime.datetime.now().year - 1, datetime.datetime.now().month, datetime.datetime.now().day
		last_trap_year, last_trap_month, last_trap_day = datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day

	# Get dates for date slider
	date_list = list_dates(first_trap_year, first_trap_month, first_trap_day, last_trap_year, last_trap_month, last_trap_day)

	# Apply pagination
	traps = f_paginator(request, trap_list, args)

	# Send result to template
	return render_to_response('traps/trap.html', {"traps": traps, "args": args, "permissions": perms, "dates": date_list, "jquery": "True", "jquery_slider": "True" }, context_instance=RequestContext(request))

@login_required
def trap_remove(request):
	CErr = CustomError()

	if request.user.is_staff == False:
		CErr.object, CErr.custom_error_type = 'Permission Error', 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	objects = request.POST.getlist('selected_objects')
	Trap.objects.filter(pk__in=objects).delete()

	return HttpResponseRedirect(settings.URL_PREFIX + "/traps")

@login_required
def unknown_trap_listing(request):
	CErr = CustomError()
	Search = CustomSearch()

	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all arguments
	args = Arguments()

	# Get permissions
	# perms = SnakeTrapPermissions(request)
	Search = CustomSearch()

	args.search_column = str(request.GET.get('search_column', ''))
	args.search_type = str(request.GET.get('search_type', ''))
	args.query = request.GET.getlist('query')
	if len(args.query) == len(args.search_type.split(",")):
		args.query = ",".join(args.query)
	else:
		if len(args.query) > 0:
			fquery = ''
			for query in args.query:
				if fquery != '':
					fquery = fquery + "|||" + str(query)
				else:
					fquery = str(query)
			args.query = fquery
		else:
			args.query = ''

	args.order = str(request.GET.get('order', '-traptime'))

	# These require try statements since they are integer (would otherwise crash if string was inserted)
	try:
		args.pagesize = int(request.GET.get('pagesize', 20))
	except:
		args.pagesize = 20
	try:
		args.page = int(request.GET.get('page', 1))
	except:
		args.page = 1

	if args.pagesize > 3000:
		CErr = CustomError()
		CErr.object, CErr.custom_error_type = 'Screwing Around Error', 'Stop messing with my system or suffer my wrath!!!'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all objects and order by args.order
	unknown_trap_list = Unknown_trap.objects.all().order_by(str(args.order))

	# Apply search
	unknown_trap_list = Search.f_search(unknown_trap_list, args)

	# Get time of first and last result
	try:
		first_trap = Unknown_trap.objects.all().order_by('traptime')[0]
		last_trap = Unknown_trap.objects.all().order_by('-traptime')[0]
		first_trap_year, first_trap_month, first_trap_day = first_trap.traptime.year, first_trap.traptime.month, first_trap.traptime.day
		last_trap_year, last_trap_month, last_trap_day = last_trap.traptime.year, last_trap.traptime.month, last_trap.traptime.day
	except:
		first_trap_year, first_trap_month, first_trap_day = datetime.datetime.now().year - 1, datetime.datetime.now().month, datetime.datetime.now().day
		last_trap_year, last_trap_month, last_trap_day = datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day

	# Get dates for date slider
	date_list = list_dates(first_trap_year, first_trap_month, first_trap_day, last_trap_year, last_trap_month, last_trap_day)


	# Apply pagination
	unknown_traps = f_paginator(request, unknown_trap_list, args)

	# Send result to template
	return render_to_response('traps/unknown_trap.html', {"unknown_traps": unknown_traps, "args": args, "dates": date_list, "jquery": "True", "jquery_slider": "True" }, context_instance=RequestContext(request))

@login_required
def unknown_trap_remove(request):
	CErr = CustomError()

	if request.user.is_staff == False:
		CErr.object, CErr.custom_error_type = 'Permission Error', 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	objects = request.POST.getlist('selected_objects')

	Unknown_trap.objects.filter(pk__in=objects).delete()

	return HttpResponseRedirect(settings.URL_PREFIX + "/unknown_traps")

@login_required
def snmptt_def_listing(request):
	CErr = CustomError()
	Search = CustomSearch()

	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all arguments
	args = Arguments()
	args.search_column = str(request.GET.get('search_column', ''))
	args.search_type = str(request.GET.get('search_type', ''))
	args.query = request.GET.getlist('query')
	if len(args.query) == len(args.search_type.split("|||")):
		args.query = "|||".join(args.query)
	else:
		if len(args.query) > 0:
			fquery = ''
			for query in args.query:
				if fquery != '':
					fquery = fquery + "|||" + str(query)
				else:
					fquery = str(query)
			args.query = fquery
		else:
			args.query = ''

	args.order = str(request.GET.get('order', 'oid_name'))

	# These require try statements since they are integer (would otherwise crash if string was inserted)
	try:
		args.pagesize = int(request.GET.get('pagesize', 10))
	except:
		args.pagesize = 10
	try:
		args.page = int(request.GET.get('page', 1))
	except:
		args.page = 1

	if args.pagesize > 3000:
		CErr = CustomError()
		CErr.object, CErr.custom_error_type = 'Screwing Around Error', 'Stop messing with my system or suffer my wrath!!!'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all objects and order by args.order
	snmptt_def_list = Snmptt_def.objects.select_related().all().order_by(str(args.order))
	snmptt_def_list = Search.f_search(snmptt_def_list, args)
	snmptt_defs = f_paginator(request, snmptt_def_list, args)


	# Get time of first and last result
	try:
		first_trap = Snmptt_def.objects.all().order_by('date_added')[0]
		last_trap = Snmptt_def.objects.all().order_by('-date_added')[0]
		first_trap_year, first_trap_month, first_trap_day = first_trap.date_added.year, first_trap.date_added.month, first_trap.date_added.day
		last_trap_year, last_trap_month, last_trap_day = last_trap.date_added.year, last_trap.date_added.month, last_trap.date_added.day
	except:
		first_trap_year, first_trap_month, first_trap_day = datetime.datetime.now().year - 1, datetime.datetime.now().month, datetime.datetime.now().day
		last_trap_year, last_trap_month, last_trap_day = datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day

	# Get dates for date slider
	date_list = list_dates(first_trap_year, first_trap_month, first_trap_day, last_trap_year, last_trap_month, last_trap_day)

	# Check if there are any unsaved changes
	snaketrap_info = SnakeTrapInfo.objects.filter(key='unsaved_changes')
	if snaketrap_info.count() > 0:
		unsaved_changes = "True"
	else:
		unsaved_changes = "False"

	# Send result to template
	return render_to_response('traps/snmptt_def.html', {"unsaved_changes": unsaved_changes, "snmptt_defs": snmptt_defs, "args": args, "dates": date_list, "jquery": "True", "jquery_slider": "True"}, context_instance=RequestContext(request))

@login_required
def snmptt_def_commit(request):
	CErr = CustomError()
	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	wConf = writeSnmpttConf()
	SSettings = SnakeTrapSettings()

	wConf.writeConf(SSettings)
	return HttpResponseRedirect(settings.URL_PREFIX + "/snmptt_def")

@login_required
def snmptt_def_mass_change(request):
	CErr = CustomError()
	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	action = request.POST.get('action','')

	if len(request.POST.getlist('selected_oids')) == 0:
		CErr = CustomError()
		CErr.object = 'Selection Error'
		CErr.custom_error_type = 'No objects selected'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
	if action == '':
		CErr = CustomError()
		CErr.object = 'Selection Error'
		CErr.custom_error_type = 'You didn\'t specify what to do'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	if action == 'change_argument':
		form = ChangeArgumentForm(request.POST)
		object_list = Snmptt_def.objects.select_related().filter(oid__in=request.POST.getlist('selected_oids'))
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'change_argument', "title": 'Change Argument', "form": form, "selected_objects": object_list, "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	if action == 'delete_argument':
		form = DeleteArgumentForm(request.POST)
		object_list = Snmptt_def.objects.select_related().filter(oid__in=request.POST.getlist('selected_oids'))
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'delete_argument', "title": 'Delete Argument', "form": form, "selected_objects": object_list, "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	if action == 'change_action':
		form = ChangeActionForm(request.POST)
		object_list = Snmptt_def.objects.select_related().filter(oid__in=request.POST.getlist('selected_oids'))
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'change_action', "title": 'Change Action', "form": form, "selected_objects": object_list, "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	if action == 'delete_action':
		form = ''
		object_list = Snmptt_def.objects.select_related().filter(oid__in=request.POST.getlist('selected_oids'))
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'delete_action', "title": 'Delete Action and Arguments', "form": form, "selected_objects": object_list, "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
@login_required
def snmptt_def_mass_change_commit(request):
	CErr = CustomError()
	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	oids = request.POST.getlist('selected_oids')
	action = request.POST.get('action', '')

	if len(oids) == 0:
		CErr = CustomError()
		CErr.object = 'Selection Error'
		CErr.custom_error_type = 'No object selected'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	if action == '':
		CErr = CustomError()
		CErr.object = 'Selection Error'
		CErr.custom_error_type = 'You didn\'t specify what to do'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	if action == 'change_action':
		oid_action = request.POST.get('def_action', '')
		if len(oid_action) == 0:
			CErr = CustomError()
			CErr.object = 'Selection Error'
			CErr.custom_error_type = 'No action specified'
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
			
		for oid in oids:
			changed = Snmptt_def.objects.filter(oid=str(oid)).update(action_name=str(oid_action))
		output = 'You have successfully changed action to ' + str(oid_action) + ' on:'

	elif action == 'delete_action':
		for oid in oids:
			b = Snmptt_def.objects.get(oid=str(oid))
			b.action_name = None
			c = Argument.objects.filter(oid=b).delete()
			b.save()
		output = 'You have successfully deleted the action and arguments on:'
			
	elif action == 'change_argument':
		a = Argument()
		form = ChangeArgumentForm(request.POST, instance=a)
		if form.is_valid() == False:
			CErr = CustomError()
			CErr.object = 'Form Validation Error'
			CErr.custom_error_type = 'Invalid argument_nr or argument'
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

		data = request.POST.copy()

		for oid in oids:
			argument_nr = request.POST.get('argument_nr', '')
			argument = request.POST.get('argument', '')
			defset = Snmptt_def.objects.get(oid=str(oid))
			try:
				b = Argument.objects.get(oid=defset, argument_nr=argument_nr)
				b.argument = str(argument)
			except:
				b = Argument(oid=defset, argument_nr=argument_nr, argument=str(argument))
			b.save()
		output = 'You have successfully changed argument nr ' + str(argument_nr) + ' to ' + str(argument) + ' on:'

	elif action == 'delete_argument':
		try:
			argument_nr = int(request.POST.get('argument_nr',0))
		except ValueError:
			argument_nr = 0
		if argument_nr == 0:
			CErr = CustomError()
			CErr.object = 'Selection Error'
			CErr.custom_error_type = 'Invalid argument'
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
		for oid in oids:
			deleted = Argument.objects.filter(oid=str(oid), argument_nr=int(argument_nr)).delete()
		output = 'You have successfully deleted argument nr ' + str(argument_nr) + ' on:'

	return render_to_response('traps/snmptt_def_mass_change_commit.html', {"oids": oids, "output": output, "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	
@login_required
def snmptt_def_propagate(request):
	CErr = CustomError()
	Search = CustomSearch()
	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	oid_to_prop = request.GET.get('oid_to_prop','')

	if len(oid_to_prop) == 0:
		CErr.object = 'Selection Error'
		CErr.custom_error_type = 'No object selected'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all arguments
	args = Arguments()
	args.search_column = str(request.GET.get('search_column', ''))
	args.search_type = str(request.GET.get('search_type', ''))
	args.query = request.GET.getlist('query')
	if len(args.query) == len(args.search_type.split("|||")):
		args.query = "|||".join(args.query)
	else:
		if len(args.query) > 0:
			fquery = ''
			for query in args.query:
				if fquery != '':
					fquery = fquery + "|||" + str(query)
				else:
					fquery = str(query)
			args.query = fquery
		else:
			args.query = ''

	args.order = str(request.GET.get('order', 'oid_name'))

	# These require try statements since they are integer (would otherwise crash if string was inserted)
	try:
		args.pagesize = int(request.GET.get('pagesize', 10))
	except:
		args.pagesize = 10
	try:
		args.page = int(request.GET.get('page', 1))
	except:
		args.page = 1

	if args.pagesize > 3000:
		CErr = CustomError()
		CErr.object, CErr.custom_error_type = 'Screwing Around Error', 'Stop messing with my system or suffer my wrath!!!'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all objects and order by args.order
	object_list = Snmptt_def.objects.select_related().exclude(oid=oid_to_prop).order_by(str(args.order))
	objects = Search.f_search(object_list, args)
	
	prop_arguments = Argument.objects.filter(oid=oid_to_prop)
	try:
		prop_settings = Snmptt_def.objects.get(oid=oid_to_prop)
	except:
		CErr.object = 'OID Error'
		CErr.custom_error_type = 'The OID you selected to propagate from doesn\'t exist'		
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
		
	# Get time of first and last result
	try:
		first_trap = Snmptt_def.objects.all().order_by('date_added')[0]
		last_trap = Snmptt_def.objects.all().order_by('-date_added')[0]
		first_trap_year, first_trap_month, first_trap_day = first_trap.date_added.year, first_trap.date_added.month, first_trap.date_added.day
		last_trap_year, last_trap_month, last_trap_day = last_trap.date_added.year, last_trap.date_added.month, last_trap.date_added.day
	except:
		first_trap_year, first_trap_month, first_trap_day = datetime.datetime.now().year - 1, datetime.datetime.now().month, datetime.datetime.now().day
		last_trap_year, last_trap_month, last_trap_day = datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day

	# Get dates for date slider
	date_list = list_dates(first_trap_year, first_trap_month, first_trap_day, last_trap_year, last_trap_month, last_trap_day)

	return render_to_response('traps/snmptt_def_propagate.html', {"args": args, "dates": date_list, "prop_arguments": prop_arguments, "prop_settings": prop_settings, "title": 'Propagate', "available_objects": objects, "jquery": "True", "jquery_slider": "True" }, context_instance=RequestContext(request))

@login_required
def snmptt_def_propagate_commit(request):
	CErr = CustomError()
	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
		
	selected_oids = request.POST.getlist('selected_oids')
	if len(selected_oids) == 0:
		CErr.object = 'Selection Error'
		CErr.custom_error_type = 'You didn\'t select any objects to propagate to'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	arg_nrs_to_prop = request.POST.getlist('arg_nrs_to_prop')
	oid_to_prop = request.POST.get('oid_to_prop', '')
	arg_nrs_to_prop.sort()
	d = Snmptt_def.objects.get(pk=str(oid_to_prop))
	action_to_prop = d.action_name

	try:
		c = Action.objects.get(pk=action_to_prop)
	except:
		CErr.object = 'Validation Error'
		CErr.custom_error_type = 'Invalid action, please select another object to propagate from.'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	for oid in selected_oids:
		a = Snmptt_def.objects.get(oid=str(oid))
		for arg_nr in arg_nrs_to_prop:
			arg = Argument.objects.get(oid=d, argument_nr=arg_nr)
			try:
				b = Argument.objects.get(oid=a, argument_nr=arg_nr)
				b.argument = str(arg.argument)
			except:
				b = Argument(oid=a, argument_nr=arg_nr, argument=str(arg.argument))
			b.save()
		a.action_name = c
		a.save()

	return render_to_response('traps/snmptt_def_propagate_commit.html', {"title": 'Propagate', "oids": selected_oids, "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
			

@login_required
def mib_listing(request):
	CErr = CustomError()
	if request.user.is_staff == False:
		CErr.object = 'Permission Error'
		CErr.custom_error_type = 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Initiate classes
	args = Arguments()
	CVal = CustomValidation()
	SSettings = SnakeTrapSettings()

	# Check dirs
	CErr = check_dirs((SSettings.action_dir, SSettings.temp_dir, SSettings.snmp_mib_dir), request)
	if CErr != None:
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))


	# Check if POST is set and contains modify_line and action
	selected_objects = request.POST.getlist('selected_objects')
	action = request.POST.get('action','')
	if (action == 'delete' or action == 'delete_and_remove_oids') and len(selected_objects) > 0:
		# Run validation on action and selected_objects (allow chars, nums, dots and hyphens)
		CErr = CVal.validateArg([str(action)])
		if CErr != None:
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
		CErr = CVal.validateArg(selected_objects)
		if CErr != None:
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

		# If you've gotten this far, validation has succeeded
		# Delete files in snmp_mib_dir
		deleteFiles(selected_objects, str(SSettings.snmp_mib_dir))
	if action == 'readd' and len(selected_objects) > 0:
		for line in selected_objects:
			IMib = ImportMib(SSettings, 'readd', str(line))
			IMib.convert_mib()
			IMib.parse_snmptt_file()
	if action == 'delete_and_remove_oids' and len(selected_objects) > 0:
		for line in selected_objects:
			IMib = ImportMib(SSettings, 'delete', str(line))
			IMib.parse_snmptt_file()
	form = upload_file(request)

	# List files in snmp_mib_dir
	mibs = os.listdir(SSettings.snmp_mib_dir)
	mibs.sort()
	return render_to_response('traps/mib.html', {"mibs": mibs, "args": args, "form": form.as_p(), "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))

