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

from .internalAttr import InternalAttr
from .LinacFeatures import _LinacFeature, Memorised
from PyTango import DevBoolean, AttrQuality

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class GroupMember(_LinacFeature):

    _attr = None
    _idx = None
    _rvalue = None

    def __init__(self, attr, idx, *args, **kwargs):
        super(GroupMember, self).__init__(*args, **kwargs)
        self._attr = attr
        self._idx = idx
        if self._attr is not None:
            self._rvalue = self._attr.rvalue
        self.debug("Build with index %d" % (self._idx))

    @property
    def name(self):
        if self._attr:
            return "%s:%s" % (self.representant, self._name)
        return ":%s" % (self._name)

    @property
    def representant(self):
        return self._attr.name

    def valueChange(self):
        newValue = self._attr.rvalue
        if newValue != self._rvalue:
            self.debug("value change to %s (was %s)"
                       % (self._attr.rvalue, self._rvalue))
            self._rvalue = self._attr.rvalue
            self.owner._rvalues[self._idx] = self._rvalue
            self.owner.valueChange()


class GroupAttr(InternalAttr):

    _members = None
    _rvalues = None

    def __init__(self, group, valueType=DevBoolean, *args, **kwargs):
        if valueType is not DevBoolean:
            raise TypeError("Group attributes only supported for booleans")
        super(GroupAttr, self).__init__(valueType=DevBoolean, *args, **kwargs)
        self._members = {}
        self._rvalues = []
        self.debug("Building group: %s" % (group))
        for i, element in enumerate(group):
            obj = self._getOtherAttrObj(element)
            if obj is not None:
                member = GroupMember(owner=self, attr=obj, idx=i)
                self._rvalues.append(member._rvalue)
                self._members[element] = member
                obj.addReportTo(member, member.valueChange)
            else:
                self.error("Unable to find %s member of the group" % (element))
                # FIXME: this may happen if the construction of this object
                #        happen before the member declaration.

    @property
    def members(self):
        if self._members is not None:
            return self._members.keys()

    def valueChange(self):
        newValue = all(self._rvalues)
        self.debug("value change to %s (was %s) = all(%s)"
                   % (newValue, self._readValue, self._rvalues))
        self._readValue = newValue
        self.launchEvents()

    def doWriteValue(self, value):
        self.debug("received a group write of %s" % (value))
        for element, member in self._members.iteritems():
            self.debug("working with %s (%s)" % (element, value))
            member._attr.write_value = value
        self._writeValue = value
        self.valueChange()

