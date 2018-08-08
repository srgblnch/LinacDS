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

from .attrdescr import Descriptor
from .linacds import LinacDS
from PyTango import AttributeProxy, AttrWriteType
from time import sleep

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class AttrsWrite(LinacDS):

    _writes = None
    _subtotal = None
    _total = None

    def test_Attributes(self):
        self._total = 0
        for number in self._attrs:
            self._writes = 0
            device = self._devices[number]
            devAttrs = []
            for attrName in list(device.get_attribute_list()):
                attr = AttributeProxy("%s/%s" % (device.name(), attrName))
                if attr.get_config().writable == AttrWriteType.READ_WRITE:
                    devAttrs.append(attrName)
            otherAttrs = []
            for attrName, attrDesc in self._attrs[number].iteritems():
                if isinstance(attrDesc, Descriptor):
                    if attrDesc.hasSubAttrs():
                        for subAttrDesc in attrDesc.subAttrs():
                            if subAttrDesc.writable:
                                subAttrName = "%s_%s" % (attrName,
                                                         subAttrDesc.name)
                                self._checkAttrsLists(subAttrName, devAttrs,
                                                      otherAttrs)
                                # TODO: ignore, they will have their own test
                    elif attrDesc.writable:
                        self._checkAttrsLists(attrName, devAttrs, otherAttrs)
                        self.assertAttibute(attrName, attrDesc, device)
            for attrName, attrDesc in self._deviceStaticAttrs().iteritems():
                if isinstance(attrDesc, Descriptor) and attrDesc.writable:
                    self._checkAttrsLists(attrName, devAttrs, otherAttrs)
                    self.assertAttibute(attrName, attrDesc, device)
            self._subtotal = self._writes
            self._total += self._subtotal
            print("plc%d: %d attributes write tested" % (number, self._subtotal))
            if len(devAttrs) > 0:
                print("Unchecked device write attributes: %s" % (devAttrs))
            if len(otherAttrs) > 0:
                print("Described write attributes not present: %s" % (
                    otherAttrs))
        print("Total %d write attributes tested" % (self._total))

    def assertAttibute(self, attrName, attrDesc, device):
        if isinstance(attrDesc, Descriptor):
            func = {'bool': self._booleanWrites,
                    'int': self._integerWrites,
                    'float': self._floatWrites}.get(attrDesc.type, None)
            if func is not None:
                func(device, attrName)
                self._writes += 1
            else:
                self.fail("%s has an unmanaged type %s"
                          % (attrName, attrDesc.type))

    def __writeWait(self):
        sleep(1.5)  # FIXME: it is necessary an active wait.
        # Do not wait always the maximum, but do some readings if the write
        # has applied before the limit.

    def _booleanWrites(self, device, attrName):
        self._checkNoExceptionOnWrite(device, attrName)
        self._booleanFlip(device, attrName)

    def _integerWrites(self, device, attrName):
        self._checkNoExceptionOnWrite(device, attrName)

    def _floatWrites(self, device, attrName):
        self._checkNoExceptionOnWrite(device, attrName)

    def _checkNoExceptionOnWrite(self, device, attrName):
        try:
            value = device[attrName].value
            device[attrName] = value
        except:
            self.fail(attrName)

    def _booleanFlip(self, device, attrName):
        value = device[attrName].value
        try:
            device[attrName] = not value
        except:
            self.fail(attrName)
        self.__writeWait()
        self.assertEqual(device[attrName].value, not value)
        try:
            device[attrName] = value
        except:
            self.fail(attrName)
        self.__writeWait()
        self.assertEqual(device[attrName].value, value)

