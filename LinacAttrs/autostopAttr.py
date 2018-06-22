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

    def __init__(self, plcAttr, below=None, above=None, switchAttr=None,
                 integr_t=None, *args, **kwargs):
        super(AutoStopAttr, self).__init__(*args, **kwargs)
        self._plcAttr = plcAttr
        self._switchAttr = switchAttr
        self._enable = AutoStopParameter(tag="Enable", dataType=DevBoolean,
                                         owner=self,
                                         device=self._plcAttr.device)
        self._below = AutoStopParameter(tag="Below_Threshold",
                                        dataType=DevFloat, owner=self,
                                        device=self._plcAttr.device)
        self._above = AutoStopParameter(tag="Above_Threshold",
                                        dataType=DevFloat, owner=self,
                                        device=self._plcAttr.device)
        self._plcUpdatePeriod = self.device._getPlcUpdatePeriod()
        self._integr_t = AutoStopParameter(tag="IntegrationTime",
                                           dataType=DevFloat, owner=self,
                                           device=self._plcAttr.device)
        # also the mean, std and triggered
        self._mean = AutoStopParameter(tag="Mean", dataType=DevFloat,
                                       owner=self,
                                       device=self._plcAttr.device)
        self._std = AutoStopParameter(tag="Std", dataType=DevFloat, owner=self,
                                      device=self._plcAttr.device)
        self._triggered = AutoStopParameter(tag="Triggered",
                                            dataType=DevBoolean, owner=self,
                                            device=self._plcAttr.device)
        self._enable.rvalue = False
        self._below.rvalue = below or float('-Inf')
        self._above.rvalue = above or float('Inf')
        # TODO: initialisation of the integr_t
        self._integr_t.rvalue = integr_t or float('Inf')
        self._mean.rvalue = float('nan')
        self._std.rvalue = float('nan')
        self._triggered.rvalue = False
        self._plcAttr.read_value.append_cb(self.newvaluecb)
        self._integr_t.hook = self.integr_t_changed
        self._mean.hook = self.mean_changed
        self._triggered.hook = self.triggered_changed
        self.info("Build %s between (%s,%s)" % (self.name, self._below.value,
                                                self._above.value))

    @property
    def rvalue(self):
        return self._plcAttr.read_value.array

    @property
    def timestamp(self):
        return self._plcAttr.timestamp

    @property
    def quality(self):
        return self._plcAttr.quality

    def newvaluecb(self):
        if self._enable.value:
            self.debug("New Value Callback from %s" % (self._plcAttr))
            if self._eventsObj:
                self._eventsObj.fireEvent()
            self._mean.rvalue = self._plcAttr.read_value.mean
            self._std.rvalue = self._plcAttr.read_value.std
            if self._above.rvalue < self._mean.rvalue < self._below.rvalue:
                self._triggered.rvalue = True
            if self._plcUpdatePeriod != self.device._getPlcUpdatePeriod():
                self._plcUpdatePeriod = self.device._getPlcUpdatePeriod()
                self.integr_t_changed()

    @property
    def enable(self):
        return self._enable.value

    @property
    def switch(self):
        return self._switchAttr

    @property
    def below(self):
        return self._below.value

    @property
    def above(self):
        return self._above.value

    @property
    def integr_t(self):
        return self._integr_t.value

    def integr_t_changed(self):
        period = self._plcUpdatePeriod
        samples = round(self._integr_t.value / period)
        bufferSize = self._plcAttr.read_value.maxSize()
        if bufferSize != samples:
            self.info("Modify the buffer size (from %d to %d)"
                      % (bufferSize, samples))
            self._plcAttr.read_value.resize(samples)

    @property
    def mean(self):
        if self.enable:
            return self._mean.value
        return float('nan')

    def mean_changed(self):
        if not self.triggered and self._triggerCondition():
            self._triggered.rvalue = True

    def _triggerCondition(self):
        if self.mean > self.above:
            self.info("mean value above the threshold! (%e > %e)"
                      % (self.mean, self.above))
            return True
        elif self.mean < self.below:
            self.info("mean value below the threshold! (%e < %e)"
                      % (self.mean, self.below))
            return True
        return False

    @property
    def std(self):
        if self._enable.value:
            return self._std.value
        return float('nan')

    @property
    def triggered(self):
        return self._triggered.value

    def triggered_changed(self):
        if self.enable:
            if not self.triggered:
                self.info("AutoStop triggered! Stop the switch")

    def trigger_reset(self):
        if self.triggered:
            self.info("AutoStop trigger reset")
            self._triggered.rvalue = False


class AutoStopParameter(_LinacFeature, LinacAttr):

    _tag = None
    _type = None
    _value = None
    _write_t = None
    _hook = None

    def __init__(self, owner, tag, dataType, *args, **kwargs):
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
                self._write_t = time()
                self._value = value
                self.__event(self._tag, self._value, self._write_t)
                if self.hook:
                    self._hook()
        else:
            try:
                self.rvalue = eval("%s(%s)" % (self._type.__name__, value))
            except:
                self.warning("rvalue assignment failed in the eval() section")

    @property
    def hook(self):
        return self._hook is not None

    @hook.setter
    def hook(self, func):
        self._hook = func

    def __event(self, suffix, value, timestamp):
        if self._owner and self._owner._eventsObj:
            attrName = "%s_%s" % (self._owner.name, suffix)
            eventsObj = self._owner._eventsObj
            # self.info("fireEvent(%s, %s,...)" % (attrName, value))
            eventsObj.fireEvent(attrName, value, timestamp,
                                AttrQuality.ATTR_VALID)
