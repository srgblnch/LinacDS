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

from .abstract import LinacException
from .linacAttr import LinacAttr
from .linacAttrBase import TYPE_MAP
from .LinacFeatures import TooFarCondition
from .meaningAttr import MeaningAttr
from PyTango import DevBoolean, DevUChar, AttrQuality

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class PLCAttr(LinacAttr):

    _format = None

    _readAddr = None
    _readBit = None
    _writeAddr = None
    _writeBit = None

    _meanings = None
    _meaningsObj = None

    _readbackAttrName = None
    _readbackAttrObj = None
    _setpointAttrName = None
    _setpointAttrObj = None
    _switchAttrName = None
    _switchAttrObj = None

    _isRst = None
    _rst_t = None

    _tooFarCondition = None

    def __init__(self, valueFormat=None,
                 readAddr=None, readBit=None, writeAddr=None, writeBit=None,
                 meanings=None, readback=None, setpoint=None, switch=None,
                 IamChecker=None, isRst=None, *args, **kwargs):
        """
            Class to describe an attribute that references information from
            any of the Linac's PLCs.
        """
        super(PLCAttr, self).__init__(*args, **kwargs)
        self._format = valueFormat
        self._readAddr = readAddr
        self._readBit = readBit
        self._writeAddr = writeAddr
        self._writeBit = writeBit or readBit

        self.meanings = meanings

        self._readbackAttrName = readback
        self._buildReadbackObj()
        self._setpointAttrName = setpoint
        self._buildSetpointObj()
        self._switchAttrName = switch
        self._buildSwitchObj()
        self._isRst = isRst
        # self.debug("%s PLCAttr build" % self.name)

    def hardwareRead(self, datablock):
        if datablock is None:
            self.warning("Not ready to read from hardware")
            return
        if self.type == DevBoolean:
            value = datablock.bit(self._readAddr, self._readBit)
        else:
            value = datablock.get(self._readAddr, *self.type)
        if value is not None:
            self.read_value = value
            self._timestamp = self._device.last_update_time
        return value

    def hardwareWrite(self, datablock):
        if datablock is None:
            self.warning("Not ready to write on hardware")
            return
        self.info("Hardware write (%s)" % self.wvalue)
        # TODO: check the Locking bit to know if the write control has gained
        if self.type == DevBoolean:
            rbyte = datablock.b(self._readAddr)
            if self._writeValue:
                # sets bit 'bitno' of b
                toWrite = rbyte | (int(1) << self._writeBit)
                # a byte of 0s with a unique 1 in the place to set this 1
            else:
                # clears bit 'bitno' of b
                toWrite = rbyte & ((0xFF) ^ (1 << self._writeBit))
                # a byte of 1s with a unique 0 in the place to set this 0
            datablock.write(self._writeAddr, toWrite, TYPE_MAP[DevUChar])
            reRead = datablock.b(self._readAddr)
            self.debug("Writing boolean (%d.%d) byte was %s; write %s; now %s"
                       % (self._writeAddr, self._writeBit, bin(rbyte),
                          bin(toWrite), bin(reRead)))
        else:
            self.debug("Write value (%d) to %s" % (self._writeAddr,
                                                   self._writeValue))
            datablock.write(self._writeAddr, self._writeValue, self.type)

#     # TODO: move this to a formula feature
#     def __solveFormula(self, attrName, VALUE, formula):
#         '''Some attributes can have a formula to interpret or modify the
#            value given from the PLC to the value reported by the device.
#         '''
#         result = eval(formula)
#         # self.debug_stream("%s formula eval(\"%s\") = %s" % (attrName,
#         #                                                     formula,
#         #                                                     result))
#         return result

    ###########################
    # Dictionary properties ---
    @property
    def format(self):
        return self._format

    @format.setter
    def format(self, value):
        self._format = value

    @property
    def read_addr(self):
        return self._readAddr

    @property
    def read_bit(self):
        return self._readBit

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

    def _buildReadbackObj(self):
        self._readbackAttrObj = self._getOtherAttrObj(self._readbackAttrName)
        if self._readbackAttrObj is not None:
            self.debug("Readback Object build with %s"
                       % (self._readbackAttrName))
        return self._readbackAttrObj

    @property
    def setpointAttr(self):
        return self._setpointAttrName

    def _buildSetpointObj(self):
        self._setpointAttrObj = self._getOtherAttrObj(self._setpointAttrName)
        if self._setpointAttrObj is not None:
            self.debug("Setpoint Object build with %s"
                       % (self._setpointAttrName))
        return self._setpointAttrObj

    @property
    def SwitchAttr(self):
        return self._switchAttrName

    def _buildSwitchObj(self):
        self._switchAttrObj = self._getOtherAttrObj(self._switchAttrName)
        if self._switchAttrObj is not None:
            self.debug("Switch Object build with %s"
                       % (self._switchAttrName))
        return self._switchAttrObj

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

    @property
    def meanings(self):
        return self._meanings

    @meanings.setter
    def meanings(self, value):
        if value is not None:
            self._meaningsObj = MeaningAttr(owner=self)
        else:
            self._meaningsObj = None
        self._meanings = value

    def _evalQuality(self):
        # self.info("PLCAttr._evalQuality()")
        if self.isTooFarEnable() and self._setpointAttrName is not None:
            # self.info("TooFar is enable and there is a Setpoint Attr %s"
            #           % (self._setpointAttrName))
            if self._setpointAttrObj is None and \
                    self._buildSetpointObj() is None:
                return  # Couldn't build the setpoint object
            if self._tooFarCondition is None:
                self._tooFarCondition = TooFarCondition(
                    owner=self, setpointAttr=self._setpointAttrObj)
            # Once here one have the object build for sure
            if self._tooFarCondition.checkCondition():
                # self.info("Readback is too far from setpoint!")
                self._quality = AttrQuality.ATTR_WARNING
                self.info("After check TooFar condition, quality is: %s"
                          % (self._quality))
                return  # break check this wins
            self.info("After check TooFar condition, quality is: %s"
                      % (self._quality))
        # once made the check, the superclass implementation is called just
        # to know if there is a QualityInterpreter to be evaluated above this
        super(PLCAttr, self)._evalQuality()