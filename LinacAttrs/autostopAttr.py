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


from .linacAttr import LinacAttr
from .LinacFeatures import CircularBuffer
from .LinacFeatures import _LinacFeature
from PyTango import AttrQuality, DevBoolean, DevFloat
from time import ctime


class AutostopAttr(LinacAttr):
    # TODO: when internalAttr becomes more generic (logicAttr, grpAttr)
    #       make this class inherit from internalAttr.

    _plcAttr = None
    _enable = None
    _below = None
    _above = None
    _integr_t = None

    def __init__(self, plcAttr, below=None, above=None, *args, **kwargs):
        super(AutostopAttr, self).__init__(*args, **kwargs)
        self._plcAttr = plcAttr
        self._enable = AutoStopParameter(tag="Enable", dataType=DevBoolean,
                                         owner=self)
        self._below = AutoStopParameter(tag="Below_Threshold",
                                        dataType=DevFloat, owner=self)
        self._above = AutoStopParameter(tag="Above_Threshold",
                                        dataType=DevFloat, owner=self)
        self._integr_t = AutoStopParameter(tag="IntegrationTime",
                                           dataType=DevFloat, owner=self)
        self.info("Build %s between (%s,%s)" % (self.name, self._below.value,
                                                self._above.value))
        # also the mean, std and triggered
        self._mean = AutoStopParameter(tag="Mean", dataType=DevFloat, owner=self)
        self._std = AutoStopParameter(tag="Std", dataType=DevFloat, owner=self)
        self._triggered = AutoStopParameter(tag="Triggered", dataType=DevBoolean,
                                            owner=self)
        self._enable.value = False  # TODO: memorised attribute
        self._below.value = below or float('-Inf')
        self._above.value = above or float('Inf')
        # TODO: initialisation of the integr_t
        self._mean.value = float('nan')
        self._std.value = float('nan')
        self._triggered.value = False
        self._plcAttr.rvalue.append_cb(self.newvaluecb)

    @property
    def rvalue(self):
        return self._plcAttr.rvalue.array

    @property
    def timestamp(self):
        return self._plcAttr.timestamp

    @property
    def quality(self):
        return self._plcAttr.quality

    def newvaluecb(self):
        if self._enable.value:
            # self.info("New Value Callback for\n%s" % (self._plcAttr.rvalue))
            self._mean.value = self._plcAttr.rvalue.mean
            self._std.value = self._plcAttr.rvalue.std
            if self._above.value < self._mean.value < self._below.value:
                self._triggered.value = True

    @property
    def enable(self):
        return self._enable.value

    @property
    def below(self):
        return self._below.value

    @property
    def above(self):
        return self._above.value

    @property
    def integr_t(self):
        return self._integr_t.value

    @property
    def mean(self):
        if self._enable.value:
            return self._mean.value
        return float('nan')

    @property
    def std(self):
        if self._enable.value:
            return self._std.value
        return float('nan')

    @property
    def triggered(self):
        return self._triggered.value


class AutoStopParameter(_LinacFeature, LinacAttr):

    _tag = None
    _type = None
    _value = None
    _write_t = None

    def __init__(self, owner, tag, dataType, *args, **kwargs):
        super(AutoStopParameter, self).__init__(owner=owner,
                                                name="%s:Meaning"
                                                % (owner.name),
                                                valueType=dataType,
                                                *args, **kwargs)
        self._tag = tag
        if dataType == DevFloat:
            self._type = float
        elif dataType == DevBoolean:
            self._type = bool
        else:
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
