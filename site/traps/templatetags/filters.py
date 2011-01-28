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

from django.template.defaultfilters import stringfilter
from django import template
from django.conf import settings
import syslog 

# Template filters
register = template.Library()

@register.filter
@stringfilter
def truncate_string(value, arg):
	if len(value) > arg:
		return value[0:arg]
	else:
		return value

@register.filter
@stringfilter
def get_rest_of_string(value, arg):
	if len(value) - 1 > arg:
		return value[arg:]
	else:
		return ''

@register.filter
@stringfilter
def get_prefix(value):
	return ""
