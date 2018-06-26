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

from ..constants import THRESHOLD
from .feature import _LinacFeature
from numpy import isnan
from PyTango import AttrQuality, DevFailed
from time import time, ctime
import traceback

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class Events(_LinacFeature):

    _conditions = None
    _lastEventValue = None
    _lastEventQuality = AttrQuality.ATTR_INVALID
    _event_t = None

    def __init__(self, conditions=None, *args, **kwargs):
        super(Events, self).__init__(*args, **kwargs)
        self.conditions = conditions
        self._ctr = EventCtr()

    def __str__(self):
        _str_ = "%s" % (self._conditions_str)
        if self._event_t:
            _str_ = "".join("%s '%s' %s" % (_str_, ctime(self._event_t),
                                            self._lastEventQuality))
        return _str_

    def __repr__(self):
        repr = "%s (Events):\n" % self.owner.name
        compoments = ['lastEventQuality', 'conditions', 'event_t',
                      'event_t_str']
        compoments.sort()
        for each in compoments:
            property = getattr(self, each)
            if property is None:
                pass  # ignore
            elif type(property) is list and len(property) == 0:
                pass  # ignore
            else:
                repr += "\t%s: %s\n" % (each, property)
        return repr

    @property
    def lastEventQuality(self):
        return self._lastEventQuality

    @lastEventQuality.setter
    def lastEventQuality(self, value):
        self._lastEventQuality = value

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

    @property
    def conditions(self):
        return self._conditions

    @conditions.setter
    def conditions(self, value):
        if value is None:
            self._conditions = None
            self._conditions_str = "No Events"
            return
        elif isinstance(value, dict):
            if len(value.keys()) == 0:
                self._conditions = {}
                self._conditions_str = "Always Emit"
                return
            elif THRESHOLD in value.keys():
                self._conditions = value
                value = self._conditions[THRESHOLD]
                self._conditions_str = \
                    "Emit when changes bigger than %s" % (value)
                return
        raise AssertionError("Cannot interpret event conditions with %r"
                             % (value))

    def fireEvent(self, name=None, value=None, timestamp=None, quality=None):
        if self._owner is None or self._owner.device is None:
            self.warning("Cannot emit events outside a tango device server")
            return False
        try:
            if name is None:
                name = name or self._owner.name
            if value is None:
                value = self._owner.rvalue
            if timestamp is None:
                timestamp = self._owner.timestamp
            if value is None:
                value = self._owner.noneValue
                self._owner.device.push_change_event(name, value, timestamp,
                                                     AttrQuality.ATTR_INVALID)
                self.lastEventQuality = AttrQuality.ATTR_INVALID
            if quality is None:
                quality = self._owner.quality
            if self._checkConditions(name, value, quality):
                self._owner.device.push_change_event(name, value, timestamp,
                                                     quality)
                self.lastEventQuality = quality
                self.info("%s.fireEvent(%s, %s, %s, %s)" % (self.name, name,
                                                            value, timestamp,
                                                            quality))
                self._ctr += 1
            if name != self._owner.name:
                return time()
            self._event_t = time()
            return self._event_t
        except DevFailed as e:
            self.warning("DevFailed in event %s emit: %s"
                         % (self.name, e[0].desc))
        except Exception as e:
            self.error("Event for %s (with name %s and value %s) not emitted "
                       "due to: %s" % (self.name, name, value, e))
            traceback.print_stack()
        return None

    def _checkConditions(self, name, value, quality):
        """
            Check if the conditions to emit an event match.
        """
        if name is not None and name.lower() != self.owner.name.lower():
            self.info("Delegated emission for %s" % (name))
            return True  # check doesn't apply
        if self._conditions is None or len(self._conditions.keys()) == 0:
            return True
        if THRESHOLD in self._conditions:
            threshold = self._conditions[THRESHOLD]
            if self._lastEventValue is None:
                self._lastEventValue = value
                self.info("No previous event to check threshold condition")
                return True
            diff = abs(self._lastEventValue - value)
            if isnan(diff) or diff > threshold:
                self._lastEventValue = value
                self.info("Value change bigger or equal to the threshold "
                          "(%g > %g)" % (diff, threshold))
                return True
            elif self.lastEventQuality == AttrQuality.ATTR_CHANGING and \
                    self.lastEventQuality != quality:
                # when last event emitted was changing, and there is a quality
                # change, then for sure emit an event with the new quality info
                return True
            else:
                return False
        return False


class EventCtr(object):

    __instance = None
    __ctr = 0

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
        return cls.__instance

    @property
    def ctr(self):
        return self.__ctr

    def __iadd__(self, value):
        self.__ctr += value
        # print("\nAdded %d, having %s\n" % (value, self.__ctr))
        return self

    def clear(self):
        # print("\nclear()\n")
        self.__ctr = 0
