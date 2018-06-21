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

from .linacAttrBase import LinacAttrBase
from .LinacFeatures import _LinacFeature
from PyTango import DevString

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


BASESET = 'baseSet'


class HistoryAttr(_LinacFeature, LinacAttrBase):

    _cleanerSet = None

    def __init__(self, owner, *args, **kwargs):
        super(HistoryAttr, self).__init__(owner=owner,
                                          name="%s:History" % (owner.name),
                                          valueType=DevString, *args, **kwargs)

    def __str__(self):
        return "%s (%s)" % (self.alias, self.__class__.__name__)

    @property
    def rvalue(self):
        return self.read_value

    @property
    def read_value(self):
        valuesLst = self.owner.read_value.array.tolist()
        if len(valuesLst) == 0:
            self._readValue = ['']
        else:
            if hasattr(self.owner, '_meaningsObj'):
                converter = self.owner._meaningsObj._meaning
            else:
                converter = str
            for i, element in enumerate(valuesLst):
                newValue = converter(element)
                valuesLst[i] = newValue
            self._readValue = valuesLst
        return self._readValue

    @property
    def timestamp(self):
        return self._owner.timestamp

    @property
    def quality(self):
        return self._owner.quality

    @property
    def events(self):
        return self._owner._events

    @property
    def cleanerSet(self):
        return self._cleanerSet

    @cleanerSet.setter
    def cleanerSet(self, value):
        self._cleanerSet = value
