# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 3
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

from .feature import _LinacFeature

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

class Formula(_LinacFeature):
    _read = None
    _write = None
    _write_not_allowed = None

    def __init__(self, owner, read=None, write=None, write_not_allowed=None,
                 *args, **kwargs):
        super(Formula, self).__init__(owner=owner, *args, **kwargs)
        self.log("has formula: read: %s, write: %s" % (read, write))
        if read is not None:
            self._read = read
        else:
            self._read = 'VALUE'
        if write is not None:
            self._write = write
        else:
            self._write = 'VALUE'
        self._write_not_allowed = write_not_allowed

    @property
    def read(self):
        return self._read

    def readHook(self, value):
        return self._solve(value, self._read)

    @property
    def write(self):
        return self._write

    def writeHook(self, value):
        return self._solve(value, self._write)

    @property
    def write_not_allowed(self):
        return self._write_not_allowed

    def _solve(self, VALUE, formula):
        result = eval(formula)
        self.info("solve eval(\"%s\") = %s" % (formula, result))
        return result


