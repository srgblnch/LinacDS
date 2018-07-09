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
from .LinacFeatures import Events, ChangeReporter, Formula
from .LinacFeatures import CircularBuffer
from PyTango import AttrQuality
from PyTango import DevBoolean, DevString
from PyTango import DevUChar, DevShort, DevUShort, DevInt
from PyTango import DevLong, DevLong64, DevULong, DevULong64
from PyTango import DevFloat, DevDouble
from PyTango import DevFailed
from PyTango import Except as PyTangoExcept

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


class LinacAttrBase(_AbstractAttrDict, _AbstractAttrTango):

    _name = None
    _type = None
    _label = None
    _description = None

    _components = None

    _readValue = None
    _writeValue = None
    _minValue = None
    _maxValue = None

    _qualities = None

    _events = None
    _eventsObj = None

    _changeReporter = None

    # _formula = None
    _formulaObj = None

    def __init__(self, name, valueType, label=None, description=None,
                 events=None, minValue=None, maxValue=None, formula=None,
                 *args, **kwargs):
        # meanings must be is a subclass of LinacAttr or
        # generates a circular import because MeaningAttr
        # inherits from LinacAttr.
        """ Main superclass for linac attributes.
        """
        super(LinacAttrBase, self).__init__(*args, **kwargs)
        self._name = name
        if valueType is None:
            self._type = None
        elif valueType in [DevString, DevBoolean]:
            self._type = valueType
        else:
            self._type = TYPE_MAP[valueType]
        self._label = label
        self._description = description
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
        self.setFormula(formula)

    def __str__(self):
        return "%s (%s)" % (self.name, self.__class__.__name__)

    def __repr__(self):
        repr = "%s:\n" % self
        if self._components is None:
            # only the first time requested, and once all the inits have end
            components = list(self.keys())
            components.sort()
            if 'value' in components and 'rvalue' in components:
                components.pop(components.index('value'))
            if 'vtq' in components:
                components.pop(components.index('vtq'))
            self._components = components
        for each in self._components:
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
    def label(self):
        return self._label

    # @label.setter
    # def label(self, value):
    #     self._label = value

    @property
    def description(self):
        if self._description is not None:
            return "%r" % self._description

    # @description.setter
    # def description(self, value):
    #     self._description = value

    @property
    def value(self):
        return self.rvalue

    @property
    def rvalue(self):
        if isinstance(self._readValue, CircularBuffer):
            if self.type == ('f', 4):
                try:
                    rvalue = float(self.read_value)
                except:
                    rvalue = float('NaN')
            else:
                try:
                    rvalue = int(self.read_value)
                except:
                    rvalue = None
        else:
            rvalue = self.read_value
        try:
            if self._formulaObj is not None and \
                    self._formulaObj.read is not None:
                rvalue = self._formulaObj.readHook(rvalue)
        except Exception as e:
            self.error("Exception solving read formula: %s" % (e))
        return rvalue

    @property
    def wvalue(self):
        if hasattr(self, 'write_value'):
            wvalue = self.write_value
            try:
                if self._formulaObj is not None and \
                        self._formulaObj.write is not None:
                    wvalue = self._formulaObj.writeHook(wvalue)
            except DevFailed as e:
                self.error("Write not allowed: %s" % (e[0].desc))
                raise e
            except Exception as e:
                self.error("Exception solving write formula: %s" % (e))
            return wvalue

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
        elif self._type in [DevBoolean]:
            return None
        else:
            return '0'

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
            previousValue = self._readValue.value
            self._readValue.append(value)
            if hasattr(self, '_historyObj') and self._historyObj:
                self.read_value
            if previousValue != value:
                self.launchEvents()
        elif self._readValue != value:
            self._readValue = value
            self.launchEvents()

    @property
    def write_value(self):
        return self._writeValue

    @write_value.setter
    def write_value(self, value):
        self.doWriteValue(value)

    def doWriteValue(self, value):
        if self._writeValue != value:
            self.debug("value change from %s to %s"
                       % (self._writeValue, value))
            self._writeValue = value
            if hasattr(self, 'hardwareWrite'):
                self.hardwareWrite(self.device.write_db)
            if self._attr is None:
                self._buildAttrObj()
            if self._attr is not None:
                self._attr.set_write_value(value)

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
        if self._eventsObj is not None:
            return self._eventsObj
        return False

    @events.setter
    def events(self, value):
        if value is not None:
            self._eventsObj = Events(owner=self, conditions=value)
        else:
            self._eventsObj = None
        self._events = value

    def launchEvents(self):
        if self._eventsObj:
            self._eventsObj.fireEvent()
        # FIXME: those hasattr must be moved to the correct subclass
        #        launchEvents() method
        if hasattr(self, '_meaningsObj') and self._meaningsObj:
            name = self._meaningsObj.alias
            value, timestamp, quality = self._meaningsObj.vtq
            self._meaningsObj.event_t = \
                self._eventsObj.fireEvent(name, value, timestamp, quality)
        if hasattr(self, '_historyObj') and self._historyObj:
            name = self._historyObj.alias
            value, timestamp, quality = self._historyObj.vtq
            self._historyObj.event_t = \
                self._eventsObj.fireEvent(name, value, timestamp, quality)
        # FIXME: migrate the meaning feature to the callback system will
        #        simplify this method (because the meaning attribute will be
        #        reported and will be itself the one that emits the event).
        if hasattr(self, '_changeReporter') and self._changeReporter:
            self._changeReporter.report()

    #############################################################
    # Dependencies between attributes and changes propagation ---
    def addReportTo(self, obj, methodName=None):
        if self._changeReporter is None:
            self._changeReporter = ChangeReporter(self)
        self._changeReporter.addDestination(obj,
                                            methodName or 'evaluateAttrValue')

    @property
    def reporter(self):
        return self._changeReporter

    @property
    def formula(self):
        if self._formulaObj is not None:
            return "%s" % (self._formulaObj)

    def setFormula(self, value):
        if value is not None:
            kwargs = {'owner': self}
            kwargs.update(value)  # kwargs = {**kwargs, **value}
            self._formulaObj = Formula(**kwargs)
        else:
            self._formulaObj = None


