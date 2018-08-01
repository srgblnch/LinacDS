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

from .devices import getPLCSimulators, getLinacDevices, getRelocator
from .parsefile import ParseFile
from PyTango import DeviceProxy
from unittest import TestCase

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class TestBench(TestCase):

    _attrs = None
    _simulators = None
    _devices = None
    _relocator = None

    def setUp(self):
        self._simulators = getPLCSimulators()
        self._devices = getLinacDevices()
        self._relocator = getRelocator()
        self._parseFiles()

    def _parseFiles(self):
        self._attrs = {}
        for number in [1,2,3]:
            obj = ParseFile()
            obj.parse_file('../plc%d.py' % number)
            self._attrs[number] = obj.attrs
        obj = ParseFile()
        obj.parse_file('../plck.py')
        self._attrs[5] = self._attrs[4] = obj.attrs


    def test_Constructor(self):
        devProxies = 0
        for i in range(1, 6):
            if isinstance(self._simulators[i], DeviceProxy):
                devProxies += 1
            if isinstance(self._devices[i], DeviceProxy):
                devProxies += 1
        if isinstance(self._relocator, DeviceProxy):
            devProxies += 1
        self.assertEqual(devProxies, 11,
                         "Not all the devices proxies are available")

    def test_Attributes(self):
        total = 0
        for number in self._attrs:
            reads = 0
            device = self._devices[number]
            for attrName in self._attrs[number]:
                if 'type' in self._attrs[number][attrName]:
                    attrType = self._attrs[number][attrName]['type']
                    print number, attrName
                    value = device[attrName].value
                    if self.__doTest(value, attrType, attrName):
                        reads += 1
            subtotal = reads
            total += subtotal
            print("plc%d: %d attributes tested" % (number, subtotal))
        print("Total %d attributes tested" % (total))

    def __doTest(self, value, dataType, msg=None):
        if dataType == 'float':
            self.assertIsInstance(value, float, msg)
        elif dataType == 'int':
            self.assertIsInstance(value, int, msg)
        elif dataType == 'str':
            self.assertIsInstance(value, str, msg)
        else:
            return False
        return True
