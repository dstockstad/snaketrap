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
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from traps.models import *
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext
from django import forms
from django.core.context_processors import csrf
from django.conf import settings
from django.core.validators import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from django.template.defaultfilters import stringfilter

# Memcache
# from django.views.decorators.cache import cache_page
# from django.core.cache import cache

# Custom classes
from traps.validation import *
from traps.error_handling import *
from traps.forms import *
from traps.import_mib import *
from traps.write_snmptt_conf import *
from traps.custom_settings import *
from traps.custom_permissions import *
from traps.custom_search import *

# Non django modules
from string import replace
import os
import sys
import subprocess
import shlex
import datetime
import syslog 
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

# Helper functions for views
def deleteFiles(filelist, directory):
	output = []
	for file in filelist:
		os.remove(str(directory) + '/' + str(file))

def check_dirs(dirs, request):
	CErr = CustomError()
	for dir in dirs:
		if os.path.isdir(dir) == False:
			CErr.object = 'Directory Error'
			CErr.custom_error_type = dir + " doesn't exist"
			return CErr
	return(None)

def f_paginator(request, list, pagesize, page):
	# Split up query into pages
	paginator = Paginator(list, int(pagesize))

	# If page request (9999) is out of range, deliver last page of results.
	try:
		traps = paginator.page(page)
	except (EmptyPage, InvalidPage):
		traps = paginator.page(paginator.num_pages)
	return(traps)


def list_dates(start_year=2011, start_month=1, start_day=1, last_year=2011, last_month=2, last_day=26):
	date_list = []

	begin_year = datetime.date(start_year, start_month, start_day)
	end_year = datetime.date(last_year, last_month, last_day)
	one_day = datetime.timedelta(days=1)

	next_day = begin_year
	if start_year == last_year:
		last_year = last_year + 1

	for year in range(start_year, last_year):
		for day in range(0, 366):  # includes potential leap year
			if next_day > end_year:
				break
			date_list.append("".join(next_day.isoformat().split("-")))
			next_day += one_day

	return(date_list)

# Views
@login_required
def about(request):
	return render_to_response('traps/about.html', {}, context_instance=RequestContext(request))

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
		page = int(request.GET.get('page', 1))
	except:
		page = 1

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
	traps = f_paginator(request, trap_list, args.pagesize, page)

	# Send result to template
	return render_to_response('traps/trap.html', {"traps": traps, "args": args, "permissions": perms, "dates": date_list, "jquery": "True", "jquery_slider": "True" }, context_instance=RequestContext(request))

@login_required
def trap_remove(request):
	CErr = CustomError()

	if request.user.is_staff == False:
		CErr.object, CErr.custom_error_type = 'Permission Error', 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	objects = request.POST.getlist('selected_objects')
	for object in objects:
		b = Trap.objects.get(pk=str(object))
		b.delete()

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
		page = int(request.GET.get('page', 1))
	except:
		page = 1

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
	unknown_traps = f_paginator(request, unknown_trap_list, args.pagesize, page)

	# Send result to template
	return render_to_response('traps/unknown_trap.html', {"unknown_traps": unknown_traps, "args": args, "dates": date_list, "jquery": "True", "jquery_slider": "True" }, context_instance=RequestContext(request))

@login_required
def unknown_trap_remove(request):
	CErr = CustomError()

	if request.user.is_staff == False:
		CErr.object, CErr.custom_error_type = 'Permission Error', 'You must be staff to view this page'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	objects = request.POST.getlist('selected_objects')
	for object in objects:
		b = Unknown_trap.objects.get(pk=str(object))
		b.delete()

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
		page = int(request.GET.get('page', 1))
	except:
		page = 1

	if args.pagesize > 3000:
		CErr = CustomError()
		CErr.object, CErr.custom_error_type = 'Screwing Around Error', 'Stop messing with my system or suffer my wrath!!!'
		return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

	# Get all objects and order by args.order
	snmptt_def_list = Snmptt_def.objects.select_related().all().order_by(str(args.order))
	snmptt_def_list = Search.f_search(snmptt_def_list, args)
	snmptt_defs = f_paginator(request, snmptt_def_list, args.pagesize, page)


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

	# Send result to template
	return render_to_response('traps/snmptt_def.html', {"snmptt_defs": snmptt_defs, "args": args, "dates": date_list, "jquery": "True", "jquery_slider": "True" }, context_instance=RequestContext(request))

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
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'change_argument', "title": 'Change Argument', "form": form, "selected_objects": request.POST.getlist('selected_oids'), "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	if action == 'delete_argument':
		form = DeleteArgumentForm(request.POST)
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'delete_argument', "title": 'Delete Argument', "form": form, "selected_objects": request.POST.getlist('selected_oids'), "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	if action == 'change_action':
		form = ChangeActionForm(request.POST)
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'change_action', "title": 'Change Action', "form": form, "selected_objects": request.POST.getlist('selected_oids'), "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
	if action == 'delete_action':
		form = ''
		return render_to_response('traps/snmptt_def_mass_change.html', {"action": 'delete_action', "title": 'Delete Action and Arguments', "form": form, "selected_objects": request.POST.getlist('selected_oids'), "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))

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
	modify_lines = request.POST.getlist('modify_line')
	action = request.POST.get('action','')
	if (action == 'delete' or action == 'delete_and_remove_oids') and len(modify_lines) > 0:
		# Run validation on action and modify_lines (allow chars, nums, dots and hyphens)
		CErr = CVal.validateArg([str(action)])
		if CErr != None:
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))
		CErr = CVal.validateArg(modify_lines)
		if CErr != None:
			return render_to_response('traps/error.html', {"custom_errors": CErr}, context_instance=RequestContext(request))

		# If you've gotten this far, validation has succeeded
		# Delete files in snmp_mib_dir
		deleteFiles(modify_lines, str(SSettings.snmp_mib_dir))
	if action == 'readd' and len(modify_lines) > 0:
		for line in modify_lines:
			IMib = ImportMib(SSettings, 'readd', str(line))
			IMib.convert_mib()
			IMib.parse_snmptt_file()
	if action == 'delete_and_remove_oids' and len(modify_lines) > 0:
		for line in modify_lines:
			IMib = ImportMib(SSettings, 'delete', str(line))
			IMib.parse_snmptt_file()
	form = upload_file(request)

	# List files in snmp_mib_dir
	mibs = os.listdir(SSettings.snmp_mib_dir)
	mibs.sort()
	return render_to_response('traps/mib.html', {"mibs": mibs, "args": args, "form": form.as_p(), "jquery": False, "jquery_slider": False }, context_instance=RequestContext(request))
