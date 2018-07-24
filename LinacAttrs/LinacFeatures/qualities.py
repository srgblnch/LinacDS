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

from .buffers import CircularBuffer
from ..constants import (CHANGING, WARNING, ALARM,
                         ABSOLUTE, RELATIVE, ABOVE, BELOW, UNDER)
from .feature import _LinacFeature
from PyTango import AttrQuality

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class _QualitiesObject(object):
    # FIXME: this copies some methods from _LinacFeature. It must not inherit
    #        from a feature, but they may share a superclass
    # TODO: this class tree would need also some logging methods

    _name = None
    _str_ = None
    _components = None
    _owner = None

    def __init__(self, name, owner, *args, **kwargs):
        super(_QualitiesObject, self).__init__(*args, **kwargs)
        self._name = name
        self._owner = owner

    def __str__(self):
        if self._str_ is not None:
            return self._str_
        return self.name

    def __repr__(self):
        repr = "%s:\n" % (self.name)
        self._buildComponents()
        for each in self._components:
            if each not in ['name']:
                value = self._getComponentValue(each)
                if value is not None:
                    repr += "\t%s\n" % (value)
        return repr

    def _buildComponents(self):
        if self._components is None:
            # only the first time requested, and once all the inits have end
            components = []
            for kls in self.__class__.__mro__:
                for key, value in kls.__dict__.iteritems():
                    if isinstance(value, property) and key not in components:
                        components += [key]
            components.sort()
            self._components = components

    def _getComponentValue(self, component):
        attrgetter = getattr(self, component)
        if attrgetter is None:
            pass  # ignore
        elif type(attrgetter) is list and len(attrgetter) == 0:
            pass  # ignore
        else:
            return "%s: %s" % (component, attrgetter)

    @property
    def name(self):
        return self._name

    def log(self, *args, **kwargs):
        self._owner.log(*args, **kwargs)

    def error(self, *args, **kwargs):
        self._owner.error(*args, **kwargs)

    def warning(self, *args, **kwargs):
        self._owner.warning(*args, **kwargs)

    def info(self, *args, **kwargs):
        self._owner.info(*args, **kwargs)

    def debug(self, *args, **kwargs):
        self._owner.debug(*args, **kwargs)


class _AbsoluteThreshold(_QualitiesObject):

    _above = None
    _below = None
    _under = None

    def __init__(self, description, *args, **kwargs):
        super(_AbsoluteThreshold, self).__init__(*args, **kwargs)
        # self.debug("Building absolute threshold with %s description"
        #            % (description))
        self._str_ = "{"
        for key, item in description.iteritems():
            if key is ABOVE:
                above = self._above = float(item)
                self._str_ = "".join("%sabove: %g" % (self._str_, item))
            else:
                above = float("Inf")
            if key is BELOW:
                below = self._below = float(item)
                self._str_ = "".join("%sbelow: %g" % (self._str_, item))
            else:
                below = float("-Inf")
            if key is UNDER:
                self._under = bool(item)
                self._str_ = "".join("%sunder: %s" % (self._str_, item))
            if key not in [ABOVE, BELOW, UNDER]:
                raise TypeError("Unknown threshold definition %s" % (key))
            self._str_ = "".join("%s, " % (self._str_))
        if above < below:
            raise AssertionError("Check bounds, "
                                 "below must be smaller than above")

        self._str_ = self._str_[:-2] + "}"

    @property
    def above(self):
        return self._above

    @property
    def below(self):
        return self._below

    @property
    def under(self):
        return self._under

    def eval(self, value):
        if self._above is not None:
            above = float(self._above)
        else:
            above = float('inf')
        if self._below is not None:
            below = float(self._below)
        else:
            below = float('-inf')
        if self._under is not None:
            answer = above < value < below
            # self.debug("%g < %g < %g: %s" % (above, value, below, answer))
        else:
            answer = not below <= value <= above
            # self.debug("not %g <= %g <= %g: %s" % (below, value, above, answer))
        return answer


class _RelativeThreshold(_QualitiesObject):

    _value = None

    def __init__(self, description, *args, **kwargs):
        super(_RelativeThreshold, self).__init__(*args, **kwargs)
        description = float(description)
        if description <= 0:
            raise AssertionError("Relative changes must be strictly positive")
        self._value = description
        self._str_ = "%g" % (self._value)

    def _getBuffer(self):
        return self._owner._owner.owner.read_value

    def eval(self):
        # self.debug("eval by relative threshold")
        deviation = self._getBuffer().std
        answer = deviation >= self._value
        # self.debug("%g >= %g: %s" % (deviation, self._value, answer))
        return answer


class _QualityDescription(_QualitiesObject):

    _role = None

    def __init__(self, *args, **kwargs):
        super(_QualityDescription, self).__init__(*args, **kwargs)
        self._role = self._name.rsplit('.')[-1]

class _Quality4Floats(_QualityDescription):

    _absolute = None
    _relative = None

    def __init__(self, description, *args, **kwargs):
        super(_Quality4Floats, self).__init__(*args, **kwargs)
        self._str_ = "{"
        for key, item in description.iteritems():
            # self.debug("%s: %s" % (key, item))
            if key is ABSOLUTE:
                self._absolute = _AbsoluteThreshold(name="%s.absolute"
                                                         % (self.name),
                                                    owner=self,
                                                    description=item)
                self._str_ = "".join("%sabsolute: %s"
                                     % (self._str_, self._absolute))
            elif key is RELATIVE:
                if self._attributeHasBuffer():
                    self._relative = _RelativeThreshold(name="%s.relative"
                                                             % (self.name),
                                                        owner=self,
                                                        description=item)
                    self._str_ = "".join("%srelative: %s"
                                         % (self._str_, self._relative))
                else:
                    raise BufferError("Impossible to setup a relative quality"
                                      "without a buffer of values in the "
                                      "attribute")
            else:
                raise TypeError("Unknown threshold definition %s"
                                % (key))
            self._str_ = "".join("%s, " % (self._str_))
        self._str_ = self._str_[:-2] + "}"

    @property
    def absolute(self):
        return self._absolute

    @property
    def relative(self):
        return self._relative

    def _attributeHasBuffer(self):
        interpreter = self._owner
        attribute = interpreter.owner
        buffer = attribute.read_value
        return isinstance(buffer, CircularBuffer)

    def eval(self, value):
        # self.debug("eval quality for %s floats (%s)" % (self._role, value))
        if self._absolute and self._absolute.eval(value):
            return True
        if self._relative and self._relative.eval():
            return True
        return False


class _Quality4States(_QualityDescription):

    _enumeration = None

    def __init__(self, description, *args, **kwargs):
        super(_Quality4States, self).__init__(*args, **kwargs)
        self._enumeration = description

    @property
    def enumeration(self):
        return self._enumeration

    def eval(self, value):
        answer = value in self._enumeration
        self.info("eval quality for enumerations (%s in %s: %s)"
                  % (value, self._enumeration, answer))
        return answer


class QualityInterpreter(_LinacFeature):

    _changing = None
    _warning = None
    _alarm = None
    _str_ = None

    def __init__(self, descriptor, *args, **kwargs):
        super(QualityInterpreter, self).__init__(*args, **kwargs)
        self._str_ = "{"
        # self.debug("Building a quality interpreter with %s definition"
        #            % (descriptor))
        for key, item in descriptor.iteritems():
            # self.debug("check for key '%s', item: %s" % (key, item))
            if isinstance(item, list):
                # self.debug("item %s is a list" % (item))
                self.__assignQuality(key, _Quality4States, item)
            elif isinstance(item, dict):
                # self.debug("item %s is a dictionary" % (item))
                self.__assignQuality(key, _Quality4Floats, item)
            else:
                raise TypeError("Unknown descriptor key %s item %s"
                                % (key, item))
            self._str_ = "".join("%s, " % (self._str_))
        self._str_ = self._str_[:-2] + "}"

    def __str__(self):
        return self._str_

    @property
    def changing(self):
        return self._changing

    @property
    def warning(self):
        return self._warning

    @property
    def alarm(self):
        return self._alarm

    def __assignQuality(self, key, Constructor, item):
        # self.debug("key %s, constructor %s, item %s"
        #          % (key, Constructor.__name__, item))
        if key is CHANGING:
            self._changing = Constructor(name="%s.changing" % (self.name),
                                         owner=self, description=item)
            self._str_ = "".join("%schanging: %s"
                                 % (self._str_, self._changing))
        elif key is WARNING:
            self._warning = Constructor(name="%s.warning" % (self.name),
                                        owner=self, description=item)
            self._str_ = "".join("%swarning: %s"
                                 % (self._str_, self._warning))
        elif key is ALARM:
            self._alarm = Constructor(name="%s.alarm" % (self.name),
                                      owner=self, description=item)
            self._str_ = "".join("%salarm: %s"
                                 % (self._str_, self._alarm))
        else:
            raise KeyError("Unknown descriptor key %s" % (key))

    def getQuality(self, value):
        # There is a precedence: if more than one quality matches, wins the
        # one more critical.
        if self._alarm and self._alarm.eval(value):
            answer = AttrQuality.ATTR_ALARM
        elif self._warning and self._warning.eval(value):
            answer = AttrQuality.ATTR_WARNING
        elif self._changing and self._changing.eval(value):
            answer = AttrQuality.ATTR_CHANGING
        else:
            answer = AttrQuality.ATTR_VALID
        return answer

