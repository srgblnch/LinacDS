from __future__ import print_function
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

from attrdescr import Descriptor
from .linacds import LinacDS
from tango import AttrQuality
from time import time, sleep

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class Test11_TooFar(LinacDS):

    _tooFar = None
    _subtotal = None
    _total = None


    _number = None
    _attrName = None
    _readback = None
    _forceValue = None

    def test_Attributes(self):
        self._total = 0
        attrs = self._collectAttributes()
        self._checkAttributes(attrs)
        self._logger.info("Total %d toofar condition attributes tested"
                          % (self._total))
        self._logger.info("Feature TooFar Condition test succeed")


    def _collectAttributes(self):
        dct = {}
        for number in self._attrs:
            dct[number] = []
            for attrName, attrDesc in self._attrs[number].iteritems():
                attrStruct = "self._getAttrStruct('%s')" % (attrName)
                query = "hasattr(%s, '_tooFarCondition')" \
                        " and " \
                        "%s._tooFarCondition is not None" \
                        % (attrStruct, attrStruct)
                if self._devices[number].Exec(query) == 'True':
                    dct[number].append(attrName)
        return dct

    def _checkAttributes(self, dct):
        for number in dct:
            self._tooFar = 0
            self._number = number
            backvalue = self._devices[self._number]['IsTooFarEnable'].value
            if not backvalue:
                self._devices[self._number]['IsTooFarEnable'] = True
            if len(dct[self._number]) > 0:
                for attrName in dct[self._number]:
                    self._attrName = attrName
                    self._checkSingleAttribute()
                    self._tooFar += 1
            self._devices[self._number]['IsTooFarEnable'] = backvalue
            self._subtotal = self._tooFar
            self._total += self._subtotal
            self._logger.info("plc%d: %d TooFar condition attributes tested"
                              % (self._number, self._subtotal))

    def _checkSingleAttribute(self):
        if not self.__simulatorGetUpdatable():
            self.__simulatorSetUpdatable(True)
            sleep(0.3)
            self.__simulatorSetUpdatable(False)
        else:
            self.__simulatorSetUpdatable(False)
        logLevel = self.__deviceGetLogLevel()
        self.__deviceSetLogLevel('debug')
        self._readback = self.__simulatorGetReadValue()
        if -1 < self._readback < 0:
            self._forceValue = self._readback-2
        elif 0 <= self._readback < 1:
            self._forceValue = self._readback+2
        else:
            self._forceValue = self._readback*1.2
        self._logger.debug("%d:%s force readback from %g to %g"
                           % (self._number, self._attrName,
                              self._readback, self._forceValue))
        self.__simulatorForceReadValue(self._forceValue)
        sleep(0.3)
        self.__waitWarningQuality()
        self.__simulatorForceReadValue(self._readback)
        self.__simulatorSetUpdatable(True)
        self.__deviceSetLogLevel(logLevel)

    def __simulatorGetUpdatable(self):
        query = "self._plc.attributes['%s']['updatable']" % (self._attrName)
        if self._simulators[self._number].Exec(query) == 'True':
            return True
        return False

    def __simulatorSetUpdatable(self, updatable):
        query = "self._plc.attributes['%s']['updatable'] = %s"\
                % (self._attrName, updatable)
        self._simulators[self._number].Exec(query)

    def __simulatorGetReadValue(self, field='read_value'):
        strValue = None
        ctr = 0
        while strValue is None:
            try:
                query = "self._plc.attributes['%s']['%s']"\
                        % (self._attrName, field)
                strValue = self._simulators[self._number].Exec(query)
                value = float(strValue)
            except Exception as e:
                sleep(0.3)
                ctr += 1
                if ctr == 10:
                    break
            else:
                return value
        self.fail("couldn't read plc%d:%s" % (self._number, self._attrName))

    def __simulatorForceReadValue(self, value):
        query = "self._plc.attributes['%s']['read_value'] = %s"\
                % (self._attrName, value)
        self._simulators[self._number].Exec(query)

    def __waitWarningQuality(self):
        t0 = time()
        quality = self.__deviceAttributeQuality()
        while quality is not AttrQuality.ATTR_WARNING:
            if quality is AttrQuality.ATTR_VALID:
                # print(".", end='')
                if time()-t0 > 1:
                    break
            if quality is AttrQuality.ATTR_CHANGING:
                # print(":", end='')
                if time() - t0 > 3:
                    break
            quality = self.__deviceAttributeQuality()
            sleep(0.3)
        self._logger.debug("%d:%s has quality: %s"
                           % (self._number, self._attrName, quality))
        self.assertEqual(quality, AttrQuality.ATTR_WARNING,
                         "plc%d %s" % (self._number, self._attrName))

    def __deviceAttributeQuality(self):
        return self._devices[self._number][self._attrName].quality

    def __deviceGetLogLevel(self):
        query = "self._getAttrStruct('%s').logLevel" % (self._attrName)
        return self._devices[self._number].Exec(query)

    def __deviceSetLogLevel(self, logLevel):
        query = "self._getAttrStruct('%s').logLevel = '%s'" % (self._attrName,
                                                             logLevel)
        self._devices[self._number].Exec(query)
