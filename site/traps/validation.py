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

from traps.error_handling import *
# Validation
class CustomValidation:
	def __init__(self):
		import re
		self.valid_re = re.compile(r'^[-\w\.]+$')

	def isValid(self, field_data, all_data):
		if not self.valid_re.search(field_data):
			raise ValidationError, "This value must contain only letters, numbers, underscores, dots or hyphens."

	def validateArg(self, arguments):
		CErr = CustomError()
		for argument in arguments:
			try:
				self.isValid(argument, [])
			except ValidationError:
				CErr.object = str(argument)
				CErr.custom_error_type = 'ValidationError'
				return(CErr)
		return(None)
