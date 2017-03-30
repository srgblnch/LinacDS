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


from .buffers import CircularBuffer
from .feature import _LinacFeature
from PyTango import AttrQuality
from time import ctime


class AutoStopParameter(_LinacFeature):

    _tag = None
    _type = None
    _value = None
    _write_t = None

    def __init__(self, tag, dataType, *args, **kwargs):
        super(AutoStopParameter, self).__init__(*args, **kwargs)
        self._tag = tag
        self._type = dataType

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if isinstance(value, self._type):
            if self._value != value:
                self._write_t = ctime()
                self._value = value
                #self.__event(self._tag, self._value, self._write_t)

    def __event(self, suffix, value, timestamp):
        if self._owner and self._owner._eventsObj:
            attrName = "%s_%s" % (self._owner.name, suffix)
            eventsObj = self._owner._eventsObj
            eventsObj.fireEvent(attrName, value, timestamp,
                                AttrQuality.ATTR_VALID)
