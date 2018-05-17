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
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from .internalAttr import InternalAttr

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

class LogicAttr(InternalAttr):
    def __init__(self, logic=None, operator=None, inverted=None,
                 *args, **kwargs):
        super(LogicAttr, self).__init__(*args, **kwargs)
        self._logic = logic
        self._operator = operator
        self._inverted = inverted

    @property
    def logic(self):
        return self._logic

    @property
    def operator(self):
        return self._operator

    @property
    def inverted(self):
        return self._inverted
