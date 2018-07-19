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

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class InternalAttr(LinacAttr):

    _meanings = None
    _meaningsObj = None

    def __init__(self, defaultValue=None, meanings=None, *args, **kwargs):
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

    #######################################################
    # Dictionary properties for backwards compatibility ---
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


    # FIXME: this may be a reference to a Memorized feature
    #######################
    # Memorised feature ---
    def storeDynMemozized(self, mainName, suffix, value):
        if self._memorised:
            self._memorised.store(suffix)

    def recoverDynMemorized(self, mainName, suffix):
        if self._memorised:
            self._memorised.recover(suffix)
