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
from .LinacFeatures import CircularBuffer
from .LinacFeatures import _LinacFeature
from PyTango import AttrQuality, DevBoolean, DevFloat
from time import time

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class AutoStopAttr(LinacAttr):
    # TODO: when internalAttr becomes more generic (logicAttr, grpAttr)
    #       make this class inherit from internalAttr.

    _plcAttr = None
    _switchAttr = None
    _enable = None
    _below = None
    _above = None
    _integr_t = None

    _plcUpdatePeriod = None

    _buffer = None

    def __init__(self, plcAttr, below=None, above=None, switchAttr=None,
                 integr_t=None, *args, **kwargs):
        super(AutoStopAttr, self).__init__(*args, **kwargs)
        self._plcAttr = plcAttr
        self._switchAttr = switchAttr
        self._enable = AutoStopParameter(tag="Enable", dataType=DevBoolean,
                                         owner=self,
                                         device=self._plcAttr.device,
                                         hook=self.enable_changed)
        self._below = AutoStopParameter(tag="Below_Threshold",
                                        dataType=DevFloat, owner=self,
                                        device=self._plcAttr.device,
                                        hook=self.below_changed)
        self._above = AutoStopParameter(tag="Above_Threshold",
                                        dataType=DevFloat, owner=self,
                                        device=self._plcAttr.device,
                                        hook=self.above_changed)
        self._plcUpdatePeriod = self.device._getPlcUpdatePeriod()
        self._integr_t = AutoStopParameter(tag="IntegrationTime",
                                           dataType=DevFloat, owner=self,
                                           device=self._plcAttr.device,
                                           hook=self.integr_t_changed)
        # also the mean, std and triggered
        self._mean = AutoStopParameter(tag="Mean", dataType=DevFloat,
                                       owner=self,
                                       device=self._plcAttr.device,
                                       hook=self.mean_changed)
        self._std = AutoStopParameter(tag="Std", dataType=DevFloat, owner=self,
                                      device=self._plcAttr.device)
        self._triggered = AutoStopParameter(tag="Triggered",
                                            dataType=DevBoolean, owner=self,
                                            device=self._plcAttr.device,
                                            hook=self.triggered_changed)
        self._initialiseValues(below, above, integr_t)
        self.info("Build %s between (%s,%s)" % (self.name, self._below.value,
                                                self._above.value))

    def _initialiseValues(self, below, above, integr_t):
        self._enable.rvalue = self._enable._writeValue = False
        self._below.rvalue = self._below._writeValue = below or float('-Inf')
        self._above.rvalue = self._above._writeValue = above or float('Inf')
        self._integr_t.rvalue = self._integr_t._writeValue = \
            integr_t or float('Inf')
        self._mean.rvalue = float('nan')
        self._std.rvalue = float('nan')
        self._triggered.rvalue = False
        bufferSize = round(self._integr_t.value/self._plcUpdatePeriod)
        self._buffer = CircularBuffer([], owner=self)
        self._buffer.resize(bufferSize)
        self._plcAttr.read_value.append_cb(self.newvalue_cb)

    def _proceedConditions(self):
        if self._enable.value and \
                hasattr(self._switchAttr, 'rvalue') and \
                self._switchAttr.rvalue:
            return True
        return False

    def _disableCondition(self):
        if self._mean:
            self._mean.rvalue = float('NaN')
        if self._std:
            self._std.rvalue = float('NaN')

    @property
    def rvalue(self):
        if self._buffer:
            return self._buffer.array
        return []

    @property
    def noneValue(self):
        return []

    @property
    def timestamp(self):
        return self._plcAttr.timestamp

    @property
    def quality(self):
        return self._plcAttr.quality

    def newvalue_cb(self):
        if self._proceedConditions():
            self._buffer.append(self._plcAttr.read_value.value)
            self.reviewPlcPeriod()
            if self._eventsObj:
                self._eventsObj.fireEvent()
            self._mean.rvalue = self._buffer.mean
            self._std.rvalue = self._buffer.std

    @property
    def enable(self):
        return self._enable.value

    def enable_changed(self):
        self.info("Feature %s"
                  % ("enabled" if self._enable.value else "disabled"))
        if self._buffer:
            self._buffer.resetBuffer()
            if self._eventsObj:
                self._eventsObj.fireEvent()
        if not self._enable.value:
            self._disableCondition()

    @property
    def switch(self):
        return self._switchAttr

    def switch_cb(self):
        if self._proceedConditions():
            self._triggered.rvalue = False
        if len(self._buffer) > 0:
            self._buffer.resetBuffer()
            if self._eventsObj:
                self._eventsObj.fireEvent()
        if not self._switchAttr.rvalue:
            self._disableCondition()

    def setSwitchAttr(self, obj):
        self._switchAttr = obj
        self._switchAttr.addReportTo(self, 'switch_cb')

    @property
    def below(self):
        if self.enable:
            return self._below.value
        return float('Inf')

    def below_changed(self):
        self.info("below_changed to %s" % (self.below))

    @property
    def above(self):
        if self.enable:
            return self._above.value
        return float('Inf')

    def above_changed(self):
        self.info("above_changed to %s" % (self.above))

    @property
    def integr_t(self):
        return self._integr_t.value

    def integr_t_changed(self):
        if self._buffer:
            period = self._plcUpdatePeriod
            samples = round(self._integr_t.value / period)
            bufferSize = self._buffer.maxSize()
            if bufferSize != samples:
                self.info("Modify the buffer size (from %d to %d)"
                          % (bufferSize, samples))
                self._buffer.resize(samples)

    def reviewPlcPeriod(self):
        if self._plcUpdatePeriod != self.device._getPlcUpdatePeriod():
            self._plcUpdatePeriod = self.device._getPlcUpdatePeriod()
            self.integr_t_changed()

    @property
    def mean(self):
        if self.enable:
            return self._mean.value
        return float('nan')

    def mean_changed(self):
        if not self.triggered and self._triggerCondition():
            mean, std = self.mean, self.std
            self._triggered.rvalue = True

    def _triggerCondition(self):
        if self.mean > self.above:
            self.info("mean value above the threshold! (%g > %g)"
                      % (self.mean, self.above))
            return True
        elif self.mean < self.below:
            self.info("mean value below the threshold! (%g < %g)"
                      % (self.mean, self.below))
            return True
        return False

    @property
    def std(self):
        if self.enable:
            return self._std.value
        return float('nan')

    @property
    def triggered(self):
        return self._triggered.value

    def triggered_changed(self):
        if self.enable:
            if self.triggered:
                self.warning("AutoStop triggered! Stop the switch")
                self._switchAttr.write_value = False
            else:
                self.info("Rearm the AutoStop")


class AutoStopParameter(_LinacFeature, LinacAttr):

    _tag = None
    _type = None
    _value = None
    _write_t = None
    _hook = None

    def __init__(self, owner, tag, dataType, hook=None, *args, **kwargs):
        super(AutoStopParameter, self).__init__(owner=owner,
                                                name="%s:%s"
                                                % (owner.name, tag),
                                                valueType=dataType,
                                                *args, **kwargs)
        self._tag = tag
        self._name = "%s(%s)" % (self._name, self._tag)
        if dataType == DevFloat:
            self._type = float
        elif dataType == DevBoolean:
            self._type = bool
        else:
            self._type = dataType
        self.hook = hook

    def __str__(self):
        return "%s (%s)" % (self.alias, self.__class__.__name__)

    @property
    def value(self):
        return self.rvalue

    @property
    def rvalue(self):
        return self._value

    @rvalue.setter
    def rvalue(self, value):
        if isinstance(value, self._type):
            if self._value != value:
                self._value = value
                self._timestamp = time()
                self.__event(self._tag, self._value, self._timestamp)
                if self.hook:
                    self._hook()
        else:
            try:
                self.rvalue = eval("%s(%s)" % (self._type.__name__, value))
            except:
                self.warning("rvalue assignment failed in the eval() section")

    def doWriteValue(self, value):
        super(AutoStopParameter, self).doWriteValue(value)
        self._write_t = time()
        self.rvalue = value  # propagate (including the hook)
        if self._memorised is not None:
            self._memorised.store("%s" % self.rvalue)

    @property
    def hook(self):
        return self._hook is not None

    @hook.setter
    def hook(self, func):
        if callable(func):
            self._hook = func

    def __event(self, suffix, value, timestamp):
        if self._owner and self._owner._eventsObj:
            attrName = "%s_%s" % (self._owner.name, suffix)
            eventsObj = self._owner._eventsObj
            eventsObj.fireEvent(name=attrName, value=value,
                                timestamp=timestamp,
                                quality=AttrQuality.ATTR_VALID)
