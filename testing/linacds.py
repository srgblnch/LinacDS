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


# TODO: To complete the coverage:
# * read with checks on the qualities
# * write attributes
#   * plc attributes (3 types)
#   * internals (side effects with other attrs)
#   * enumerations (the funcionality itself)
# * Event generation (events are generated with the expected values)
# * Circular buffers (how different values affect those buffers)
# * Attr memorised (make sure the values are well stored, but also recovered)
# * Meaning attributes (construction of those strings from the ints)
# * History attributes (special case of buffer with certain resets)
# * AutoStop
#   * Well collection of data when on and no data collection if off
#   * reproduce the stop
# * change reporter (test relations propagation)
# * Formulas & masks / logic attrs
# * TooFar, switches and resets
# * group attributes

class LinacDS(TestCase):

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
