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

from attrdescr import Descriptor
from .linacds import LinacDS

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class Test2_AttrsRead(LinacDS):

    _reads = None
    _subtotal = None
    _total = None

    def test_Attributes(self):
        self._total = 0
        for number in self._attrs:
            self._reads = 0
            device = self._devices[number]
            devAttrs = list(device.get_attribute_list())
            otherAttrs = []
            for attrName, attrDesc in self._attrs[number].iteritems():
                if isinstance(attrDesc, Descriptor) and attrDesc.hasSubAttrs():
                    for subAttrDesc in attrDesc.subAttrs():
                        self._checkAttrsLists("%s_%s" % (attrName,
                                                         subAttrDesc.name),
                                              devAttrs, otherAttrs)
                else:
                    self._checkAttrsLists(attrName, devAttrs, otherAttrs)
                    self.assertAttibute(attrName, attrDesc, device)
            for attrName, attrDesc in self._deviceStaticAttrs().iteritems():
                self._checkAttrsLists(attrName, devAttrs, otherAttrs)
                self.assertAttibute(attrName, attrDesc, device)
            self._subtotal = self._reads
            self._total += self._subtotal
            self._logger.info("plc%d: %d attributes read tested"
                              % (number, self._subtotal))
            if len(devAttrs) > 0:
                self._logger.warning("Unchecked device read attributes: %s"
                                     % (devAttrs))
            if len(otherAttrs) > 0:
                self._logger.warning("Described read attributes not present: %s"
                                     % (otherAttrs))
        self._logger.info("Total %d read attributes tested"
                          % (self._total))
        self._logger.info("Attributes read test succeed")

    def assertAttibute(self, attrName, attrDesc, device):
        if isinstance(attrDesc, Descriptor):
            if attrDesc.specialCheck:
                if attrDesc.specialCheck == 'noException':
                    try:
                        device[attrName].value
                        self._reads += 1
                    except:
                        self.fail(attrName)
            else:
                value = device[attrName].value
                if self.assertReadValue(value, attrDesc.type,
                                        dim=attrDesc.dim, msg=attrName):
                    self._reads += 1

    def assertReadValue(self, value, dataType, dim=0, msg=None):
        if dim == 0:
            if dataType == 'float':
                self.assertIsInstance(value, float, msg)
            elif dataType == 'int' or dataType == 'bool':
                self.assertIsInstance(value, int, msg)
            elif dataType == 'str':
                self.assertIsInstance(value, str, msg)
            else:
                return False
            return True
        return False
