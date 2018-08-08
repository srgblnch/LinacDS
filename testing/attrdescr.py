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

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class Descriptor(object):

    _name = None
    _type = None
    _dim = None
    _plc = None
    _specialCheck = None
    _subAttrs = None
    _writable = None

    def __init__(self, name, type=None, dim=0, plc=False,
                 specialCheck=False, enumeration=False, writable=False,
                 group=None):
        super(Descriptor, self).__init__()
        self._name = name
        self._type = type
        self._dim = dim
        self._plc = plc
        self._specialCheck = specialCheck
        if enumeration is True:
            if self._subAttrs is None:
                self._subAttrs = []
            self._subAttrs.append(Descriptor('active', type='bool',
                                  writable=True))
            self._subAttrs.append(Descriptor('numeric', type='int'))
            self._subAttrs.append(Descriptor('meaning', type='str'))
            self._subAttrs.append(Descriptor('options', type='str', dim=1,
                                  writable=True))
        self._writable = writable
        self.group = group

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def __repr__(self):
        repr = "%s(%s, " % (self.__class__.__name__, self.name)
        for key in ['type', 'dim', 'plc', 'specialCheck', 'writable']:
            value = getattr(self, key)
            if value is not None:
                repr += "%s=%s, " % (key, value)
        if self.hasSubAttrs():
            repr += "hasSubAttrs=True, "
        return repr[:-2] + ")"

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        self._type = value

    @property
    def dim(self):
        return self._dim

    @dim.setter
    def dim(self, value):
        self._dim = value

    @property
    def plc(self):
        return self._plc

    @plc.setter
    def plc(self, value):
        self._plc = value

    @property
    def specialCheck(self):
        return self._specialCheck

    @specialCheck.setter
    def specialCheck(self, value):
        self._specialCheck = value

    def hasSubAttrs(self):
        return self._subAttrs is not None

    def subAttrs(self):
        for descriptor in self._subAttrs:
            yield descriptor

    @property
    def writable(self):
        return self._writable

    @writable.setter
    def writable(self, value):
        self._writable = value

    @property
    def group(self):
        return self._group

    @group.setter
    def group(self, lst):
        if isinstance(lst, list):
            self._group = lst
