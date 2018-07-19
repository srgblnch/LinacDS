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

from ..constants import (CHANGING, WARNING, ALARM,
                         ABSOLUTE, RELATIVE, ABOVE, BELOW)
from .feature import _LinacFeature

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

    def __init__(self, name, *args, **kwargs):
        super(_QualitiesObject, self).__init__(*args, **kwargs)
        self._name = name

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


class _Threshold(_QualitiesObject):

    _above = None
    _below = None

    def __init__(self, description, *args, **kwargs):
        super(_Threshold, self).__init__(*args, **kwargs)
        self._str_ = "{"
        for key, item in description.iteritems():
            if key is ABOVE:
                self._above = item
                self._str_ = "".join("%sabove: %s" % (self._str_, item))
            elif key is BELOW:
                self._below = item
                self._str_ = "".join("%sbelow: %s" % (self._str_, item))
            else:
                raise TypeError("Unknown threshold definition %s" % (key))
            self._str_ = "".join("%s, " % (self._str_))
        self._str_ = self._str_[:-2] + "}"
        # TODO: check that below < above

    @property
    def above(self):
        return self._above

    @property
    def below(self):
        return self._below


class _Absolute(_Threshold):
    def __init__(self, *args, **kwargs):
        super(_Absolute, self).__init__(*args, **kwargs)


class _Relative(_Threshold):
    def __init__(self, *args, **kwargs):
        super(_Relative, self).__init__(*args, **kwargs)
        # TODO: check that those values (above and below) are positive


class _QualityDescription(_QualitiesObject):
    def __init__(self, *args, **kwargs):
        super(_QualityDescription, self).__init__(*args, **kwargs)


class _Quality4Floats(_QualityDescription):

    _absolute = None
    _relative = None

    def __init__(self, description, *args, **kwargs):
        super(_Quality4Floats, self).__init__(*args, **kwargs)
        self._str_ = "{"
        for key, item in description.iteritems():
            if key is ABSOLUTE:
                self._absolute = _Absolute(name="%s.absolute" % (self.name),
                                           description=item)
                self._str_ = "".join("%sabsolute: %s"
                                     % (self._str_, self._absolute))
            elif key is RELATIVE:
                self._relative = _Relative(name="%s.relative" % (self.name),
                                           description=item)
                self._str_ = "".join("%srelative: %s"
                                     % (self._str_, self._relative))
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


class _Quality4States(_QualityDescription):

    _enumeration = None

    def __init__(self, enumeration, *args, **kwargs):
        super(_Quality4States, self).__init__(*args, **kwargs)
        self._enumeration = enumeration

    @property
    def enumeration(self):
        return self._enumeration



class QualityInterpreter(_LinacFeature):

    _changing = None
    _warning = None
    _alarm = None
    _str_ = None

    def __init__(self, descriptor, *args, **kwargs):
        super(QualityInterpreter, self).__init__(*args, **kwargs)
        self._str_ = "{"
        self.log("Building a quality interpreter with %s definition"
                 % (descriptor))
        for key, item in descriptor.iteritems():
            self.log("check for key '%s', item: %s" % (key, item))
            if isinstance(item, list):
                self.log("item %s is a list" % (item))
                self.__assignQuality(key, _Quality4States, item)
            elif isinstance(item, dict):
                self.log("item %s is a dictionary" % (item))
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
        if key is CHANGING:
            self._changing = Constructor(name="%s.changing" % (self.name),
                                            description=item)
            self._str_ = "".join("%schanging: %s"
                                 % (self._str_, self._changing))
        elif key is WARNING:
            self._warning = Constructor(name="%s.warning" % (self.name),
                                            description=item)
            self._str_ = "".join("%swarning: %s"
                                 % (self._str_, self._warning))
        elif key is ALARM:
            self._alarm = Constructor(name="%s.alarm" % (self.name),
                                            description=item)
            self._str_ = "".join("%salarm: %s"
                                 % (self._str_, self._alarm))
        else:
            raise KeyError("Unknown descriptor key %s" % (key))
