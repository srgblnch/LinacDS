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

from .linacds import LinacDS
from math import isnan
from time import sleep, time

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class AutoStopDescriptor(object):

    _number = None
    _device = None
    _simulator = None
    _attrName = None

    _monitorName = None
    _switchName = None
    _enableName = None
    _thresholds = None
    _integrTimeName = None
    _meanName = None
    _stdName = None
    _triggeredName = None

    def __init__(self, number, device, simulator, name):
        super(AutoStopDescriptor, self).__init__()
        self._number = number
        self._device = device
        self._simulator = simulator
        self._attrName = name
        attrStruct = "self._getAttrStruct('%s')" % (self._attrName)
        self._monitorName = self._device.Exec("%s._plcAttr.name"
                                              % (attrStruct))
        self._switchName = self._device.Exec("%s._switchAttr.name"
                                             % (attrStruct))
        self._enableName = self._device.Exec("%s._enable.alias"
                                             % (attrStruct))
        self._aboveName = self._device.Exec("%s._above.alias" % (attrStruct))
        self._belowName = self._device.Exec("%s._below.alias" % (attrStruct))
        self._integrTimeName = self._device.Exec("%s._integr_t.alias"
                                                 % (attrStruct))
        self._meanName = self._device.Exec("%s._mean.alias" % (attrStruct))
        self._stdName = self._device.Exec("%s._std.alias" % (attrStruct))
        self._triggeredName = self._device.Exec("%s._triggered.alias"
                                                % (attrStruct))

    def __str__(self):
        return "%d:%s" % (self._number, self._attrName)

    def __writeWait(self):
        sleep(0.1)

    @property
    def monitor(self):
        return self._device[self._monitorName].value

    def forceValue(self, value):
        self._simulator.Exec("self._plc.attributes['%s']['ref_value'] = %s"
                             % (self._monitorName, value))

    @property
    def switch(self):
        return self._device[self._switchName].value

    @switch.setter
    def switch(self, value):
        self._device[self._switchName] = value
        self.__writeWait()

    @property
    def spectrum(self):
        return self._device[self._attrName].value

    @property
    def enable(self):
        return self._device[self._enableName].value

    @enable.setter
    def enable(self, value):
        self._device[self._enableName] = value
        self.__writeWait()

    @property
    def below(self):
        if self._belowName != 'None':
            return self._device[self._belowName].value

    @below.setter
    def below(self, value):
        if self._belowName != 'None':
            self._device[self._belowName] = value
            self.__writeWait()

    def forceBelow(self):
        backupValue = float(self._simulator.Exec(
            "self._plc.attributes['%s']['ref_value']" % (self._monitorName)))
        if self.below is not None:
            self.forceValue(self.below*2)
        return backupValue

    @property
    def above(self):
        if self._aboveName != 'None':
            return self._device[self._aboveName].value

    @above.setter
    def above(self, value):
        if self._aboveName != 'None':
            self._device[self._aboveName] = value
            self.__writeWait()

    @property
    def integrationTime(self):
        return self._device[self._integrTimeName].value

    @integrationTime.setter
    def integrationTime(self, value):
        self._device[self._integrTimeName] = value
        self.__writeWait()

    @property
    def mean(self):
        return self._device[self._meanName].value

    @property
    def std(self):
        return self._device[self._stdName].value

    @property
    def triggered(self):
        return self._device[self._triggeredName].value


class Test08_AutoStop(LinacDS):

    _subtotal = None
    _total = None

    def test_AutoStop(self):
        self._total = 0
        attrs = self._collectAttributes()
        self._checkAttributes(attrs)
        self._logger.info("Total %d AutoStop attributes tested"
                          % (self._total))
        self._logger.info("Feature AutoStop test succeed")

    def _collectAttributes(self):
        dct = {}
        for number in self._attrs:
            dct[number] = []
            for attrName, attrDesc in self._attrs[number].iteritems():
                attrStruct = "self._getAttrStruct('%s')" % (attrName)
                query = "%s.__class__.__name__" % (attrStruct)
                device = self._devices[number]
                if device.Exec(query) == 'AutoStopAttr':
                    dct[number].append(attrName)
        return dct

    def _checkAttributes(self, dct):
        for number in dct:
            self._subtotal = 0
            for attrName in dct[number]:
                obj = AutoStopDescriptor(number,
                                         self._devices[number],
                                         self._simulators[number],
                                         attrName)
                # print("Device: %s\nAttrName: %s (%s)\n\n"
                #       "monitor: %s (%s)\nswitch: %s (%s)\n\n"
                #       "Enable: %s (%s)\nbelow: %s (%s)\nabove: %s (%s)\n"
                #       "Integration time: %s (%s)\n"
                #       "mean %s (%s) and std %s (%s)\ntriggered %s (%s)\n"
                #       % (obj._device, obj._attrName, obj.spectrum,
                #          obj._monitorName, obj.monitor,
                #          obj._switchName, obj.switch,
                #          obj._enableName, obj.enable,
                #          obj._belowName, obj.below,
                #          obj._aboveName, obj.above,
                #          obj._integrTimeName, obj.integrationTime,
                #          obj._meanName, obj.mean,
                #          obj._stdName, obj.std,
                #          obj._triggeredName, obj.triggered))
                backupEnable = obj.enable
                backupSwitch = obj.switch
                self._testProcedure(obj)
                if backupEnable != obj.enable:
                    obj.enable = backupEnable
                if backupSwitch != obj.switch:
                    obj.switch = backupSwitch
                self._subtotal += 1
            self._total += self._subtotal
            self._logger.info("plc%d: %d AutoStop attributes tested"
                              % (number, self._subtotal))

    def _testProcedure(self, obj):
        self._disableAndOff(obj)
        self._doEnable(obj)
        self._forceTriggerCondition(obj)
        self._doSwitchOn(obj)
        self._forceTriggerCondition(obj)
        self._cleanTriggerConditions(obj)

    #############
    # First level

    def _disableAndOff(self, obj):
        self._logger.info("%s Disable and switch OFF" % (obj))
        obj.enable, obj.switch = False, False
        self._operationWait()
        self.assertFalse(obj.enable, "it couldn't be disabled")
        self.assertFalse(obj.switch, "it couldn't be switch OFF")
        self._cleanTriggerConditions(obj)
        spectrum = obj.spectrum
        self.assertTrue(spectrum == None,
                        "Data collected data when shouldn't (%s)" % (spectrum))
        mean = obj.mean
        self.assertTrue(isnan(mean),
                         "Mean value when should be a NaN (%s)" % (mean))
        std = obj.std
        self.assertTrue(isnan(std),
                         "Std value when should be a NaN (%s)" % (std))
        triggered = obj.triggered
        self.assertEqual(triggered, False,
                         "Couldn't be triggered when disable and off (%s)"
                         % (triggered))
        self._modifyBelow(obj)
        self._modifyAbove(obj)
        self._modifyIntegrT(obj)

    def _doEnable(self, obj):
        self._logger.info("%s Enable AutoStop feature" % (obj))
        obj.enable = True
        self._operationWait()
        self.assertTrue(obj.enable, "It couldn't be enabled")
        self.assertGreater(len(obj.spectrum), 0,
                               "Data shall be collected")
        self.assertTrue(obj.mean != float('NaN'),
                        "Mean should have a valid value")
        self.assertTrue(obj.std != float('NaN'),
                        "Std should have a valid value")

    def _forceTriggerCondition(self, obj):
        self._logger.info("%s Force trigger condition" % (obj))
        t0 = time()
        backupBelow = obj.forceBelow()
        while time()-t0 < 3:
            self._logger.debug("reading %s (%s) -> %s"
                               % (obj.mean, obj.std,obj.triggered))
            if obj.triggered:
                break
            sleep(0.1)
        self.assertTrue(obj.triggered, "Functionality shall be triggered")
        self._logger.debug("set back to %s" % (backupBelow))
        obj.forceValue(backupBelow)
        # TODO: distinguish above and below

    def _doSwitchOn(self, obj):
        self._logger.info("%s Switch ON" % (obj))
        previousBufferSize = len(obj.spectrum)
        obj.switch = True
        self._operationWait()
        self.assertTrue(obj.switch, "it couldn't be switch ON")
        self.assertFalse(obj.triggered, "Trigger must be clean when switch ON")
        self.assertLess(len(obj.spectrum), previousBufferSize,
                        "Buffer shall be reseted")
        obj.enable = False
        spectrum = obj.spectrum
        self.assertTrue(spectrum == None,
                        "Data collected data when shouldn't (%s)" % (spectrum))
        obj.enable = True

        ##############
    # Second level

    def _operationWait(self):
        sleep(0.9)

    def _cleanTriggerConditions(self, obj):
        attrStruct = "self._getAttrStruct('%s')" % (obj._attrName)
        if obj._device.Exec("%s._triggered.value" % (attrStruct)) == 'True':
            obj._device.Exec("%s._triggered.rvalue = False" % (attrStruct))
            obj._device.Exec("%s._eventsObj.fireEvent(%s, False)"
                             % (attrStruct, obj._triggeredName))

    def _modifyBelow(self, obj):
        backupBelow = obj.below
        if backupBelow is not None:
            obj.below = backupBelow + 1
            self.assertEqual(obj.below, backupBelow + 1,
                             "below should be modifiable")
            obj.below = backupBelow

    def _modifyAbove(self, obj):
        backupAbove = obj.above
        if backupAbove is not None:
            obj.above = backupAbove + 1
            self.assertEqual(obj.above, backupAbove + 1,
                             "above should be modifiable")
            obj.above = backupAbove

    def _modifyIntegrT(self, obj):
        backupIntegrT = obj.integrationTime
        obj.integrationTime = backupIntegrT + 1
        self.assertEqual(obj.integrationTime, backupIntegrT + 1,
                         "integration time should be modifiable")
        obj.integrationTime = backupIntegrT