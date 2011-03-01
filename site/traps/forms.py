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

# Forms
from django import forms
from django.forms import ModelForm
from traps.models import *

class UploadFileForm(forms.Form):
	file = forms.FileField()

class ChangeArgumentForm(ModelForm):
	class Meta:
		model = Argument
		exclude = ('oid',)

class DeleteArgumentForm(forms.Form):
	argument_nr = forms.IntegerField()

class ChangeActionForm(forms.Form):
	def_action = forms.ModelChoiceField(queryset=Action.objects.all())
