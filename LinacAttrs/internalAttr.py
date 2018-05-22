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

from .linacAttr import LinacAttr
from .LinacFeatures import Logic

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class InternalAttr(LinacAttr):

    _readSet = None
    _writeSet = None

    _meanings = None
    _meaningsObj = None

    _logicObj = None

    def __init__(self, isWritable=False, defaultValue=None, meanings=None,
                 logic=None, operator=None, inverted=None, *args, **kwargs):
        """
            Class to describe an attribute that references information from
            any of the Linac's PLCs.
        """
        super(InternalAttr, self).__init__(*args, **kwargs)
        if defaultValue:
            if self._memorised:
                if not self._memorised.getRecoverValue():
                    self.info("Using default value %s" % (defaultValue))
                    self._readValue = defaultValue
                # don't apply the default value if another has been recovered
                # from database as memorised.
            else:
                self._readValue = defaultValue
        self.meanings = meanings
        if logic is not None:
            self._logicObj = Logic(owner=self, logic=logic, operator=operator,
                                   inverted=inverted)

    #######################################################
    # Dictionary properties for backwards compatibility ---
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

    # FIXME: this may be a reference to a MeaningAttr
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

    @property
    def logicObj(self):
        return self._logicObj

    # FIXME: this may be a reference to a Memorized feature
    #######################
    # Memorised feature ---
    def storeDynMemozized(self, mainName, suffix, value):
        if self._memorised:
            self._memorised.store(suffix)

    def recoverDynMemorized(self, mainName, suffix):
        if self._memorised:
            self._memorised.recover(suffix)

    #############################################################
    # Dependencies between attributes and changes propagation ---
    def evaluateAttrValue(self):
        if self._logicObj is not None:
            self._logicObj._evalLogical()
