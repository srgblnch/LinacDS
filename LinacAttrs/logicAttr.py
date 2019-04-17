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

from .constants import LASTEVENTQUALITY, QUALITIES
from .internalAttr import InternalAttr
from time import time
import traceback

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class LogicAttr(InternalAttr):

    _logic = None
    _operator = None
    _inverted = None

    def __init__(self, logic=None, operator=None, inverted=None,
                 *args, **kwargs):
        super(LogicAttr, self).__init__(*args, **kwargs)
        self._logic = logic        # FIXME: check its structure
        self._operator = operator  # FIXME: check if it is a valid operator
        self._inverted = inverted  # FIXME: check it's boolean
        # TODO: include the logic evaluation
        #       - triggered by callbacks
        #       - with the necessary event emission

    @property
    def logic(self):
        return "(%s, %s, %s)" % (self._logic, self._operator,
                                    "inverted" if self._inverted else "normal")

    #def __repr__(self):
    #    return self.__str__()

    def evaluateAttrValue(self):
        self._evalLogical()

    def _evalLogical(self):
        was = self.read_value
        values = []
        for key in self._logic.keys():
            try:
                if type(self._logic[key]) == dict:
                    values.append(self.__evalDct(key, self._logic[key]))
                elif type(self._logic[key]) == list:
                    values.append(self.__evalLst(key, self._logic[key]))
                else:
                    self.warn(
                        "step less to evaluate for key %s unmanaged "
                        "content type" % (key))
            except Exception as e:
                self.error("cannot eval logic for key %s: %s" % (key, e))
                traceback.print_exc()
        if self._operator == 'or':
            result = any(values)
        elif self._operator == 'and':
            result = all(values)
        if self._inverted:
            result = not result
            self.info("values %s (%s) (inverted) answer %s"
                      % (values, self._operator, result))
        else:
            self.info("values %s (%s) answer %s"
                      % (values, self._operator, result))
        self.read_t = time()  # when has been re-evaluated
        if result != was:
            self.debug("value change to %s (was %s)" % (result, was))
            # FIXME: when change propagation done, this message can be removed
            self.read_value = result
            self.launchEvents()

    def __evalDct(self, name, dct):
        """
        """
        self.debug("%s dict2eval: %s" % (name, dct))
        for key, quality in dct.iteritems():
            if key == QUALITIES:
                return self.__evalQuality(name, quality)
            else:
                self.error("Not Implemented for key %s" % (key))

    def __evalLst(self, name, lst):
        """
        """
        attrStruct = self.device._getAttrStruct(name)
        if attrStruct is not None:
            value = attrStruct.rvalue
            self.debug("%s %s in %s = %s" % (name, value, lst, value in lst))
            return value in lst
        return False

    def __evalQuality(self, name, lst):
        """
        """
        attrStruct = self.device._getAttrStruct(name)
        if attrStruct is not None:
            if hasattr(attrStruct, '_eventsObj') and \
                    attrStruct._eventsObj is not None:
                quality = attrStruct._eventsObj.lastEventQuality
                self.debug("%s %s in %s = %s"
                           % (name, quality, lst, quality in lst))
                return quality in lst
        return False
