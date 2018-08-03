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

    _reads = None
    _writes = None
    _subtotal = None
    _total = None

    def setUp(self):
        self._simulators = getPLCSimulators()
        self._devices = getLinacDevices()
        self._relocator = getRelocator()
        self._parseFiles()

    def _parseFiles(self):
        self._attrs = {}
        for number in [1, 2, 3]:
            obj = ParseFile()
            obj.parse_file('../plc%d.py' % number)
            self._attrs[number] = obj.attrs
        obj = ParseFile()
        obj.parse_file('../plck.py')
        self._attrs[5] = self._attrs[4] = obj.attrs

    def _deviceStaticAttrs(self):
        return {'EventsTime': {'type': 'float', 'dim': 1},
                'EventsTimeMin': {'type': 'float'},
                'EventsTimeMax': {'type': 'float'},
                'EventsTimeMean': {'type': 'float'},
                'EventsTimeStd': {'type': 'float'},
                'EventsNumber': {'type': 'int', 'dim': 1},
                'EventsNumberMin': {'type': 'int'},
                'EventsNumberMax': {'type': 'int'},
                'EventsNumberMean': {'type': 'float'},
                'EventsNumberStd': {'type': 'float'},
                'IsTooFarEnable': {'type': 'bool'},
                'forceWriteDB': {'type': 'str'},
                'lastUpdateStatus': None,
                'lastUpdate': None,
                'State': None,
                'Status': None,
                }


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
        self._total = 0
        for number in self._attrs:
            self._reads = 0
            device = self._devices[number]
            devAttrs = list(device.get_attribute_list())
            otherAttrs = []
            for attrName, attrStruct in self._attrs[number].iteritems():
                if isinstance(attrStruct, dict) and 'active' in attrStruct:
                    for k in attrStruct:
                        self.__checkAttrsLists("%s_%s" % (attrName, k),
                                               devAttrs, otherAttrs)
                else:
                    self.__checkAttrsLists(attrName, devAttrs, otherAttrs)
                    self.assertAttibute(attrName, attrStruct, device)
            for attrName, attrStruct in self._deviceStaticAttrs().iteritems():
                self.__checkAttrsLists(attrName, devAttrs, otherAttrs)
                self.assertAttibute(attrName, attrStruct, device)
            self._subtotal = self._reads
            self._total += self._subtotal
            print("plc%d: %d attributes tested" % (number, self._subtotal))
            if len(devAttrs) > 0:
                print("Unchecked device attributes: %s" % (devAttrs))
            if len(otherAttrs) > 0:
                print("Described attributes not present: %s" % (otherAttrs))
        print("Total %d attributes tested" % (self._total))

    def __checkAttrsLists(self, attrName, devAttrs, otherAttrs):
        if attrName in devAttrs:
            devAttrs.pop(devAttrs.index(attrName))
        else:
            otherAttrs.append(attrName)

    def assertAttibute(self, attrName, attrStruct, device):
        if isinstance(attrStruct, dict):
            if 'type' in attrStruct:
                attrType = attrStruct['type']
            else:
                attrType = None
            if 'dim' in attrStruct:
                dim = attrStruct['dim']
            else:
                dim = 0
            if 'assert' in attrStruct:
                if attrStruct['assert'] == 'noException':
                    try:
                        device[attrName].value
                        self._reads += 1
                    except:
                        self.fail(attrName)
            else:
                value = device[attrName].value
                if self.assertReadValue(value, attrType, dim=dim, msg=attrName):
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
