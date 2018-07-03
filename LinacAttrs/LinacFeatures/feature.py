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

from .abstract import _AbstractFeatureLog

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class _LinacFeature(_AbstractFeatureLog):

    _name = None
    _owner = None
    _components = None

    def __init__(self, owner, *args, **kwargs):
        super(_LinacFeature, self).__init__(*args, **kwargs)
        self._name = self.__class__.__name__
        self._owner = owner

    def __str__(self):
        return "%s" % (self.name)

    def __repr__(self):
        repr = "%s:\n" % (self.name)
        self._buildComponents()
        for each in self._components:
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
            return "%s: \"%s\"" % (component, attrgetter)

    @property
    def name(self):
        if self.owner:
            return "%s:%s" % (self.owner.name, self._name)
        return ":%s" % (self._name)

    @property
    def owner(self):
        return self._owner
