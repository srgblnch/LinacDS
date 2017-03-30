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

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

from linacAttr import LinacAttr
from LinacFeatures import _LinacFeature
from PyTango import DevString

class MeaningAttr(_LinacFeature, LinacAttr):
    _meanings = {}

    def __init__(self, owner, *args, **kwargs):
        super(MeaningAttr, self).__init__(owner=owner,
                                          name="%s:Meaning" % (owner.name),
                                          valueType=DevString, *args, **kwargs)
        #_LinacFeature.__init__(self, owner, *args, **kwargs)
        #LinacAttr.__init__(self, "%s:Meaning" % (owner.name), DevString)

    def __str__(self):
        return "%s (%s)" % (self.alias, self.__class__.__name__)

    @property
    def rvalue(self):
        if self._owner.value not in self._meanings:
            if self._owner.value:
                return "%d:unknown" % (self._owner.value)
            return "Not established"
        return "%d:%s" % (self._owner.value, self._meanings[self._owner.value])

    @property
    def timestamp(self):
        return self._owner.timestamp

    @property
    def quality(self):
        return self._owner.quality

    @property
    def meanings(self):
        return

    @meanings.setter
    def meanings(self, value):
        if not isinstance(value, dict):
            raise TypeError("meanings shall be a dictionary")
        if value != self._meanings:
            self._meanings = value

    @property
    def events(self):
        return self._owner._events