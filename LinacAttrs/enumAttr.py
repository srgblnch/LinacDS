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

from ast import literal_eval
from .linacAttr import LinacAttr
from .LinacFeatures import Memorised
from PyTango import AttrQuality
from time import time

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class EnumerationAttr(LinacAttr):
    def __init__(self, name, optionsLst=None, *args, **kwargs):
        """Precursor for the future CalibrationAttr class. Based on a list,
           provided by the user, that can be modified (and that's why it is
           memorised) provides a numeric access as well as a string meaning
           that combines both: the number and the string associated.
        """
        super(EnumerationAttr, self).__init__(name, *args, **kwargs)
        if optionsLst is None:
            self._options = []
            self._quality = AttrQuality.ATTR_INVALID
        elif type(optionsLst) == list:
            self._options = optionsLst
        else:
            raise TypeError("options shall be a list (not %s)"
                            % type(optionsLst))
        self._active = None
        self.setMemorised('options')
        self.setMemorised('active')
        self.debug("Build the EnumerationAttr %s" % self.name)

    @property
    def options(self):
        """List of the options in the enumeration
        """
        return self._options[:]

    @options.setter
    def options(self, lst):
        options = []
        # preprocess ---
        if type(lst) == list and not any([len(each)-1 for each in lst]):
            # candidate a wrong string made list
            rebuild = "".join("%s" % i for i in lst)
            self.warning("Received a wrong string list %s and rebuild to %s"
                         % (lst, rebuild))
            try:
                lst = eval(rebuild)
            except:
                lst = [rebuild]
        if type(lst) == str:
            # FIXME: check the input to avoid issues
            bar = list(literal_eval(lst))
            self.info("Received a string %r and understand a list: %s"
                      % (lst, bar))
            lst = bar
        # process ---
        if type(lst) == list:
            filteredLst = []
            for element in lst:
                if type(element) is str and len(element) > 0:
                    filteredLst.append(element.lower().strip())
            if self._options != filteredLst:
                self._options = filteredLst
                self._quality = AttrQuality.ATTR_VALID
                self.fireEvent(self.name+'_options', str(self.options))
                self.storeDynMemozized(self.name, 'options', self.options)
                if self._active is not None:
                    try:
                        # The active may have changed once the list change
                        self.active = self._active
                    except Exception as e:
                        self.warning("After options change, the active is not "
                                     "valid anymore")
                        self._active = None
        else:
            raise TypeError("options shall be a list (received a %s)"
                            % type(lst))

    @property
    def active(self):
        """Indicates which of the options is activated by the user selection.
        """
        if self._active is None:
            return 'None'
        return self._active

    @active.setter
    def active(self, value):
        if value == 'None':
            value = None
        if value is None and self._active is not None:
            quality = AttrQuality.ATTR_INVALID
            self.fireEvent(self.name+'_active', '', quality)
            self.fireEvent(self.name+'_numeric', 0, quality)
            self.fireEvent(self.name+'_meaning', '', quality)
            toBeActive = None
        else:
            if type(value) == int and value <= len(self._options):
                toBeActive = self._options[value-1]
            elif value.lower() in self._options:
                toBeActive = value.lower()
            else:
                self.options = self._options + [value]
                self.warning("%s wasn't in the list of available options "
                             "but added: %s" % (value, self.options))
                toBeActive = value.lower()
            self._active = toBeActive
            self._timestamp = time()
            self.fireEvent(self.name+'_active', self.active)
            self.fireEvent(self.name+'_numeric', self.numeric)
            self.fireEvent(self.name+'_meaning', self.meaning)

    @property
    def numeric(self):
        """Machine-friendly output with the element active.
        """
        if self._active is None:
            return 0
        return self._options.index(self.active)+1

    @numeric.setter
    def numeric(self, value):
        if type(value) == int:
            self.active = value

    @property
    def meaning(self):
        """Humane-friendly output with the element active.
        """
        if self._active is None:
            return 'None'
        return "%d:%s" % (self.numeric, self.active)
