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
from django.contrib import admin
from django import forms
from piston.models import *

class ArgumentInline(admin.StackedInline):
	model = Argument
	extra = 0
class Snmptt_defAdmin(admin.ModelAdmin):
	list_display = ('__unicode__','oid','oid_name','severity')
	search_fields = ['oid','severity']
	inlines = [ArgumentInline]

class ActionAdmin(admin.ModelAdmin):
	list_display = ('__unicode__','commandline')
	search_fields = ['action_name','commandline']

class PermissionAdmin(admin.ModelAdmin):
	list_display = ('__unicode__','user','column','regex')

admin.site.register(Snmptt_def, Snmptt_defAdmin)
admin.site.register(Action, ActionAdmin)
admin.site.register(RegexPermission, PermissionAdmin)


admin.site.unregister(Consumer)
admin.site.unregister(Nonce)
admin.site.unregister(Token) 
admin.site.unregister(Resource) 
