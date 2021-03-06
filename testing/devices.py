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

from PyTango import DeviceProxy

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

NAMEPATTERN = "li/ct/plc%d"


def getPLCSimulators():
    sim = {}
    for i in range(1, 6):
        sim[i] = DeviceProxy("%s-sim" % (NAMEPATTERN % i))
    return sim


def getLinacDevices():
    dev = {}
    for i in range(1, 6):
        dev[i] = DeviceProxy(NAMEPATTERN % i)
    return dev


def getRelocator():
    return DeviceProxy("li/ct/linacdatarelocator-01")
