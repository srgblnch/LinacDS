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
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


from linacAttr import LinacAttr


class PLCAttr(LinacAttr):

    _rst_t = None

    def __init__(self, valueFormat=None,
                 readAddr=None, readBit=None,
                 writeAddr=None, writeBit=None,
                 formula=None,
                 events=None, meanings=None, qualities=None,
                 readback=None, setpoint=None, switch=None,
                 IamChecker=None, isRst=None,
                 *args, **kwargs):
        """
            Class to describe an attribute that references information from
            any of the Linac's PLCs.
        """
        super(PLCAttr, self).__init__(*args, **kwargs)
        self._format = valueFormat
        self._readAddr = readAddr
        self._readBit = readBit
        self._writeAddr = writeAddr
        self._writeBit = writeBit
        self._formula = formula

        self._events = events
        self._meanings = meanings
        self._qualities = qualities

        self._readbackAttrName = readback
        self._setpointAttrName = setpoint
        self._switchAttrName = switch
        self._isRst = isRst
        # self.debug("%s PLCAttr build" % self.name)

    #######################################################
    # Dictionary properties for backwards compatibility ---
    @property
    def read_addr(self):
        return self._readAddr

    @property
    def read_bit(self):
        return self._readBit

    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, value):
        self._format = value

    @property
    def meanings(self):
        return self._meanings

    @meanings.setter
    def meanings(self, value):
        self._meanings = value

    @property
    def formula(self):
        return self._formula

    @property
    def write_addr(self):
        return self._writeAddr

    @write_addr.setter
    def write_addr(self, value):
        self._writeAddr = value

    @property
    def write_bit(self):
        return self._writeBit

    @write_bit.setter
    def write_bit(self, value):
        self._writeBit = value

    @property
    def readbackAttr(self):
        return self._readbackAttrName

    @property
    def setpointAttr(self):
        return self._setpointAttrName

    @property
    def SwitchAttr(self):
        return self._switchAttrName

    @property
    def isRst(self):
        return self._isRst

    @isRst.setter
    def isRst(self, value):
        self._isRst = value

    @property
    def rst_t(self):
        return self._rst_t

    @rst_t.setter
    def rst_t(self, value):
        self._rst_t = value
