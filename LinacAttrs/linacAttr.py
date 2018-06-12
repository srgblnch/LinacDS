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

from .abstract import _AbstractAttrDict, _AbstractAttrTango
from .LinacFeatures import Events, ChangeReporter
from .LinacFeatures import CircularBuffer, HistoryBuffer
from PyTango import AttrQuality
from PyTango import DevBoolean, DevString
from PyTango import DevUChar, DevShort, DevUShort, DevInt
from PyTango import DevLong, DevLong64, DevULong, DevULong64
from PyTango import DevFloat, DevDouble

from time import time, ctime
import traceback

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


TYPE_MAP = {DevUChar: ('B', 1),
            DevShort: ('h', 2),
            DevFloat: ('f', 4),
            DevDouble: ('f', 4),
            # the PLCs only use floats of 4 bytes
            }


class LinacAttr(_AbstractAttrDict, _AbstractAttrTango):

    _readValue = None
    _writeValue = None
    _minValue = None
    _maxValue = None

    _qualities = None

    _events = None
    _eventsObj = None
    _event_t = None
    _lastEventQuality = AttrQuality.ATTR_INVALID

    _baseSet = None

    _AutoStop = None
    _switchDescriptor = None

    _changeReporter = None

    def __init__(self, name, valueType, events=None, minValue=None,
                 maxValue=None, *args, **kwargs):
        # meanings must be is a subclass of LinacAttr or
        # generates a circular import because MeaningAttr
        # inherits from LinacAttr.
        """ Main superclass for linac attributes.
        """
        super(LinacAttr, self).__init__(*args, **kwargs)
        self._name = name
        if valueType is None:
            self._type = None
        elif valueType in [DevString, DevBoolean]:
            self._type = valueType
        else:
            self._type = TYPE_MAP[valueType]
        if events is not None:
            self.events = events
        self._tangodb = None
        self._timestamp = time()
        self._quality = AttrQuality.ATTR_VALID
        if self._type == ('f', 4):
            self._noneValue = float('NaN')
        elif self._type in [('h', 2), ('B', 1)]:
            self._noneValue = 0
        elif self._type == DevBoolean:
            self._noneValue = None
        else:
            self._noneValue = '0'
        if minValue:
            self._minValue = minValue
        if maxValue:
            self._maxValue = maxValue

    def __str__(self):
        return "%s (%s)" % (self.name, self.__class__.__name__)

    def __repr__(self):
        repr = "%s:\n" % self
        compoments = self.keys()
        compoments.sort()
        for each in compoments:
            if self[each] is None:
                pass  # ignore
            elif type(self[each]) is list and len(self[each]) == 0:
                pass  # ignore
            else:
                repr += "\t%s: %s\n" % (each, self[each])
        return repr

    ################
    # properties ---
    @property
    def name(self):
        return self._name

    @property
    def alias(self):
        if hasattr(self, '_alias'):
            return self._alias

    @alias.setter
    def alias(self, value):
        if isinstance(value, str):
            self._alias = value

    @property
    def value(self):
        return self.rvalue

    @property
    def rvalue(self):
        if isinstance(self._readValue, CircularBuffer):
            if self.type == ('f', 4):
                return float(self.read_value)
            else:
                return int(self.read_value)
        return self.read_value

    @property
    def wvalue(self):
        if hasattr(self, 'write_value'):
            return self.write_value

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def quality(self):
        return self._quality

    @property
    def vtq(self):
        return self.rvalue, self.timestamp, self.quality

    @property
    def type(self):
        return self._type

    @property
    def minValue(self):
        return self._minValue

    @property
    def maxValue(self):
        return self._maxValue

    @property
    def noneValue(self):
        if self._type == ('f', 4):
            return float('NaN')
        elif self._type in [('h', 2), ('B', 1)]:
            return 0
        else:
            return '0'

    ##########################
    # Tango attribute area ---


    #######################################################
    # Dictionary properties for backwards compatibility ---
    @property
    def read_value(self):
        return self._readValue

    @read_value.setter
    def read_value(self, value):
        if isinstance(value, CircularBuffer):
            if self._readValue is not None:
                self.warning("Assigned a readValue %s class when was %s"
                             % (type(value), type(self._readValue)))
            self._readValue = value
            self.launchEvents()
        elif isinstance(self._readValue, CircularBuffer):
            self._readValue.append(value)
            self.launchEvents()
        elif self._readValue != value:
            self.debug("value change from %s to %s" % (self._readValue, value))
            self._readValue = value
            self.launchEvents()

    @property
    def write_value(self):
        return self._writeValue

    @write_value.setter
    def write_value(self, value):
        if self._writeValue != value:
            self.debug("value change from %s to %s"
                       % (self._writeValue, value))
            self._writeValue = value
            if hasattr(self, 'hardwareWrite'):
                self.hardwareWrite(self.device.write_db)

    @property
    def read_t(self):
        return self._timestamp

    @read_t.setter
    def read_t(self, value):
        self._timestamp = value

    @property
    def read_t_str(self):
        if self._timestamp:
            return ctime(self._timestamp)
        return ""

    @property
    def qualities(self):
        return self._qualities

    @qualities.setter
    def qualities(self, value):
        self._qualities = value

    @property
    def events(self):
        return self._events

    @events.setter
    def events(self, value):
        if value is not None:
            self._eventsObj = Events(owner=self)
        else:
            self._eventsObj = None
        self._events = value

    @property
    def event_t(self):
        return self._event_t

    @event_t.setter
    def event_t(self, value):
        self._event_t = value

    @property
    def event_t_str(self):
        if self._event_t:
            return ctime(self._event_t)
        return None

    def launchEvents(self):
        if self._eventsObj:
            # TODO: thresholds for events emissions
            self.event_t = self._eventsObj.fireEvent()
        if hasattr(self, '_meaningsObj') and self._meaningsObj:
            name = self._meaningsObj.alias
            value, timestamp, quality = self._meaningsObj.vtq
            self._meaningsObj.event_t = \
                self._eventsObj.fireEvent(name, value, timestamp,
                                          quality)
        # FIXME: migrate the meaning feature to the callback system will
        #        simplify this method (because the meaning attribute will be
        #        reported and will be itself the one that emits the event).
        if self._changeReporter is not None:
            self._changeReporter.report()

    @property
    def lastEventQuality(self):
        return self._lastEventQuality

    @lastEventQuality.setter
    def lastEventQuality(self, value):
        self._lastEventQuality = value

    @property
    def AutoStop(self):
        return self._AutoStop

    @AutoStop.setter
    def AutoStop(self, value):
        self._AutoStop = value

    @property
    def switchDescriptor(self):
        return self._switchDescriptor

    @switchDescriptor.setter
    def switchDescriptor(self, value):
        self._switchDescriptor = value

    @property
    def baseSet(self):
        return self._baseSet

    @baseSet.setter
    def baseSet(self, value):
        self._baseSet = value

    #############################################################
    # Dependencies between attributes and changes propagation ---
    def addReportTo(self, obj):
        if self._changeReporter is None:
            self._changeReporter = ChangeReporter(self)
        self._changeReporter.addDestination(obj)

    @property
    def reporter(self):
        return self._changeReporter
