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

from django.core.validators import RegexValidator
from django.db import models
from django.contrib.auth.models import User

PERMISSION_COLUMN_CHOICES = (
    ('severity', 'Severity'),
    ('hostname', 'Hostname'),
)


# Create your models here.
class Trap(models.Model):
	eventid = models.CharField(max_length=128, null=True, blank=True)
	eventname = models.CharField(max_length=50, null=True, blank=True, db_index=True)
	trapoid = models.CharField(max_length=128, editable=False, db_index=True)
	enterprise = models.CharField(max_length=100, null=True, blank=True)
	community = models.CharField(max_length=30, null=True)
	hostname = models.CharField(max_length=100, null=True, blank=True)
	agentip = models.CharField(max_length=16, null=True, blank=True)
	category = models.CharField(max_length=20, null=True, blank=True)
	severity = models.CharField(max_length=20, null=True, blank=True, db_index=True)
	uptime = models.CharField(max_length=20, null=True, blank=True)
	traptime = models.DateTimeField('TrapTime')
	formatline = models.TextField(null=True, db_index=True)

	def __unicode__(self):
		return(str(self.id))

	class Meta:
		db_table = 'snmptt'

class Unknown_trap(models.Model):
	trapoid = models.CharField(max_length=100, null=True, db_index=True)
	enterprise = models.CharField(max_length=100, null=True)
	community = models.CharField(max_length=30, null=True)
	hostname = models.CharField(max_length=100, null=True)
	agentip = models.CharField(max_length=16, null=True)
	uptime = models.CharField(max_length=20, null=True)
	traptime = models.DateTimeField('TrapTime', null=True)
	formatline = models.TextField(null=True, db_index=True)

	def __unicode__(self):
		return(str(self.id))
	class Meta:
		db_table = 'snmptt_unknown'

class Action(models.Model):
	action_name = models.CharField(max_length=512, primary_key=True)
	commandline = models.CharField(max_length=512, validators=[RegexValidator(r'^[-\w\$\.\ ]+$', message='This field can only contain upper/lowercase characters, spaces, numbers, dots, hyphens and dollar signs')])
	help = models.CharField(max_length=512, null=True, blank=True)

	def __unicode__(self):
		return(str(self.action_name))
	class Meta:
		db_table = 'actions'

class Snmptt_def(models.Model):
	oid = models.CharField(max_length=128, primary_key=True)
	oid_name = models.CharField(max_length=512)
	event_type = models.CharField(max_length=256)
	severity = models.CharField(max_length=128)
	format = models.CharField(max_length=512)
	description = models.TextField()
	action_name = models.ForeignKey('Action', db_column='action_name', blank=True, null=True)
	date_added = models.DateTimeField('Added', auto_now=True)

	def __unicode__(self):
		return(str(self.oid))
	class Meta:
		db_table = 'snmptt_def'
		verbose_name = 'SNMPTT Definition'

class Argument(models.Model):
	oid = models.ForeignKey('Snmptt_def', db_column='oid')
	argument_nr = models.SmallIntegerField()
	argument = models.CharField(max_length=512, validators=[RegexValidator(r'^[-\w\$\.\ \*\@\"]+$', message='This field can only contain upper/lowercase characters, @, ", spaces, numbers, dots, hyphens and dollar signs')])

	def __unicode__(self):
		return(str(self.id))
	def snmptt_def_oid(self):
		return(str(Snmptt_def.oid))
	class Meta:
		db_table = 'snmptt_def_action_args'
		unique_together = ('oid','argument_nr')
		ordering = ('argument_nr','oid')

class RegexPermission(models.Model):
	user = models.ForeignKey(User)
	column = models.CharField(max_length=128, choices=PERMISSION_COLUMN_CHOICES)
	regex = models.CharField(max_length=512)

	def __unicode__(self):
		return self.regex
	class Meta:
		db_table = 'regex_permissions'
