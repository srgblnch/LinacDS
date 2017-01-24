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
from LinacFeatures import Memorised


class InternalAttr(LinacAttr):

    _memorised = None

    _logic = None
    _operator = None
    _inverted = None

    _mean = None
    _std = None

    _triggered = None

    _readSet = None
    _writeSet = None

    def __init__(self, memorized=False, isWritable=False,
                 defaultValue=None, *args, **kwargs):
        """
            Class to describe an attribute that references information from
            any of the Linac's PLCs.
        """
        super(InternalAttr, self).__init__(*args, **kwargs)
        if memorized:
            self._memorised = Memorised(owner=self)
            if not self._memorised.recover():
                self.info("Using default value %s" % (defaultValue))
                self._readValue = defaultValue
        elif defaultValue:
            self._readValue = defaultValue
        # FIXME: can those float('NaN') be to mean "non initialised"?

    #######################################################
    # Dictionary properties for backwards compatibility ---
    @property
    def logic(self):
        return self._logic

    @logic.setter
    def logic(self, value):
        self._logic = value

    @property
    def operator(self):
        return self._operator

    @operator.setter
    def operator(self, value):
        self._operator = value

    @property
    def inverted(self):
        return self._inverted

    @inverted.setter
    def inverted(self, value):
        self._inverted = value

    @property
    def Mean(self):
        return self._mean

    @Mean.setter
    def Mean(self, value):
        self._mean = value

    @property
    def Std(self):
        return self._std

    @Std.setter
    def Std(self, value):
        self._std = value

    @property
    def Triggered(self):
        return self._triggered

    @Triggered.setter
    def Triggered(self, value):
        self._triggered = value

    @property
    def read_set(self):
        return self._readSet

    @read_set.setter
    def read_set(self, value):
        self._readSet = value

    @property
    def write_set(self):
        return self._writeSet

    @write_set.setter
    def write_set(self, value):
        self._writeSet = value

    #######################
    # Memorised feature ---
    def storeDynMemozized(self, mainName, suffix, value):
        if self._memorised:
            self._memorised.store(suffix)

    def recoverDynMemorized(self, mainName, suffix):
        if self._memorised:
            self._memorised.recover(suffix)