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

from .linacAttr import LinacAttr
from .LinacFeatures import _LinacFeature
from PyTango import DevString

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class MeaningAttr(_LinacFeature, LinacAttr):
    _meanings = {}

    def __init__(self, owner, *args, **kwargs):
        super(MeaningAttr, self).__init__(owner=owner,
                                          name="%s:Meaning" % (owner.name),
                                          valueType=DevString, *args, **kwargs)

    def __str__(self):
        return "%s (%s)" % (self.alias, self.__class__.__name__)

    @property
    def rvalue(self):
        return self._meaning(self._owner.value)

    def _meaning(self, value):
        if value not in self._meanings:
            if value:
                return "%s:unknown" % (value)
            return "Not established"
        return "%s:%s" % (value, self._meanings[value])

    @property
    def timestamp(self):
        return self._owner.timestamp

    @property
    def quality(self):
        return self._owner.quality

    @property
    def meanings(self):
        return self._meanings

    @meanings.setter
    def meanings(self, value):
        if not isinstance(value, dict):
            raise TypeError("meanings shall be a dictionary")
        if value != self._meanings:
            self._meanings = value

    @property
    def events(self):
        return self._owner._events
