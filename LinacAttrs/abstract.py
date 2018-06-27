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

import functools
from .LinacFeatures import Memorised
from PyTango import DevState, AttrWriteType, Attribute, WAttribute, AttrQuality
from PyTango import Database
from PyTango import DevBoolean, DevString
from PyTango import DevUChar, DevShort, DevUShort, DevInt
from PyTango import DevLong, DevLong64, DevULong, DevULong64
from PyTango import DevFloat, DevDouble
import traceback

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class LinacException(Exception):
    pass


def CommandExc(f):
    '''Decorates commands so that the exception is logged and also raised.
    '''
    def g(self, *args, **kwargs):
        inst = self  # < for pychecker
        try:
            return f(inst, *args, **kwargs)
        except LinacException:
            raise
        except Exception, exc:
            traceback.print_exc(exc)
            self._trace = traceback.format_exc(exc)
            raise
    functools.update_wrapper(g, f)
    return g


def AttrExc(f):
    '''Decorates commands so that the exception is logged and also raised.
    '''
    def g(self, attr, *args, **kwargs):
        inst = self  # < for pychecker
        try:
            return f(inst, attr, *args, **kwargs)
        except LinacException:
            raise
        except Exception, exc:
            traceback.print_exc(exc)
            self._trace = traceback.format_exc(exc)
            raise
    functools.update_wrapper(g, f)
    return g


logLevelsLst = ['silence', 'error', 'warning', 'info', 'debug', 'trace']


class _AbstractAttrLog(object):

    _name = None
    _logLevel = None
    # By default do not log info and debug for all the attributes,
    # but they can be configured individually to include its own logs:
    # >>> devProxy.Exec("self._getAttrStruct(attrName).logLevel = 'info'")
    # With this the logs can be controlled better to show what one is looking.

    def __init__(self, *args, **kwargs):
        super(_AbstractAttrLog, self).__init__(*args, **kwargs)
        self._logLevel = logLevelsLst.index('warning')

    def __checkDevice__(self):
        return hasattr(self, 'device') and self.device is not None

    @property
    def logLevel(self):
        return logLevelsLst[self._logLevel]

    @logLevel.setter
    def logLevel(self, value):
        if isinstance(value, str):
            if value.lower() not in logLevelsLst:
                raise AssertionError("Unrecognised %s logLevel" % (value))
            newLogLevel = logLevelsLst.index(value.lower())
            if newLogLevel != self._logLevel:
                self.log("change log level from %s to %s"
                         % (self.logLevel, value))
                self._logLevel = newLogLevel

    def log(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkDevice__() and hasattr(self.device, 'info_stream'):
            self.device.info_stream(msg)
        else:
            print("LOG: %s" % (msg))

    def error(self, msg, tagName=True):
        if self._logLevel >= logLevelsLst.index('error'):
            if tagName:
                msg = "[%s] %s" % (self.name, msg)
            if self.__checkDevice__() and hasattr(self.device, 'error_stream'):
                self.device.error_stream(msg)
            else:
                print("ERROR: %s" % (msg))

    def warning(self, msg, tagName=True):
        if self._logLevel >= logLevelsLst.index('warning'):
            if tagName:
                msg = "[%s] %s" % (self.name, msg)
            if self.__checkDevice__() and hasattr(self.device, 'warn_stream'):
                self.device.warn_stream(msg)
            else:
                print("WARN: %s" % (msg))

    def info(self, msg, tagName=True):
        if self._logLevel >= logLevelsLst.index('info'):
            if tagName:
                msg = "[%s] %s" % (self.name, msg)
            if self.__checkDevice__() and hasattr(self.device, 'info_stream'):
                self.device.info_stream(msg)
            else:
                print("INFO: %s" % (msg))

    def debug(self, msg, tagName=True):
        if self._logLevel >= logLevelsLst.index('debug'):
            if tagName:
                msg = "[%s] %s" % (self.name, msg)
            if self.__checkDevice__() and hasattr(self.device, 'debug_stream'):
                self.device.debug_stream(msg)
            else:
                print("DEBUG: %s" % (msg))

    def trace(self, msg, tagName=True):
        if self._logLevel >= logLevelsLst.index('trace'):
            if tagName:
                msg = "[%s] %s" % (self.name, msg)
            msg = "TRACE: %s" % (msg)
            if self.__checkDevice__() and hasattr(self.device, 'debug_stream'):
                self.device.debug_stream(msg)
            else:
                print(msg)


class _AbstractAttrDict(_AbstractAttrLog):

    _keysLst = None

    def __init__(self, *args, **kwargs):
        super(_AbstractAttrDict, self).__init__(*args, **kwargs)

    def __len__(self):
        return len(self.keys())

    def __getitem__(self, name):
        try:
            if name in self.keys():
                for kls in self.__class__.__mro__:
                    if name in kls.__dict__.keys():
                        return kls.__dict__[name].fget(self)
            else:
                # self.error("%s not in keys: %s" % (name, self.keys()))
                return
        except Exception as e:
            self.error("Cannot get item for the key %s due to: %s" % (name, e))
            traceback.print_exc()
            return None

    def __setitem__(self, name, value):
        try:
            if name in self.keys():
                for kls in self.__class__.__mro__:
                    if name in kls.__dict__.keys():
                        if kls.__dict__[name].fset is not None:
                            kls.__dict__[name].fset(self, value)
                        else:
                            self.warning("%s NO setter" % name)
        except Exception as e:
            self.error("Cannot set item %s to key %s due to: %s"
                       % (value, name, e))

    def __delitem__(self, name):
        self.error("Not allowed delitem operation")

    def has_key(self, key):
        return key in self.keys()

    def _buildKeysLst(self):
        # FIXME: should this list be made only once?
        keys = []
        discarted = []
        for kls in self.__class__.__mro__:
            klskeys = []
            klsdiscarted = []
            for key, value in kls.__dict__.iteritems():
                if isinstance(value, property) and key not in keys:
                    klskeys += [key]
                else:
                    klsdiscarted += [key]
            keys += klskeys
            discarted += klsdiscarted
        return keys

    def keys(self):
        if self._keysLst is None:
            self._keysLst = self._buildKeysLst()
        return self._keysLst[:]

    def values(self):
        lst = []
        for key in self.keys():
            lst.append(self[key])
        return lst

    def items(self):
        lst = []
        for key in self.keys():
            lst.append((key, self[key]))
        return lst

    def __iter__(self):
        return self.iterkeys()

    def iterkeys(self):
        for name in self.keys():
            yield name

    def itervalues(self):
        for name in self.keys():
            yield self[name]

    def iteritems(self):
        for name in self.keys():
            yield name, self[name]

    def __reversed__(self):
        keys = self.keys()
        keys.reverse()
        for name in keys:
            yield name

    def __missing__(self, key):
        return key not in self.keys()

    def __contains__(self, key):
        return key in self.keys() and self[key] is not None

    def pop(self, key):
        self[key] = None


class _AbstractAttrTango(_AbstractAttrLog):

    _device = None
    _attr = None

    _memorised = None
    _memorisedLst = None

    def __init__(self, device=None, memorized=False, *args, **kwargs):
        super(_AbstractAttrTango, self).__init__(*args, **kwargs)
        self.device = device
        if memorized:
            self.setMemorised()

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        if value is not None:
            self._device = value
        self._tangodb = Database()
        if self._memorisedLst:
            for suffix in self._memorisedLst:
                self._memorised.recover(suffix)

    def _buildAttrObj(self):
        if self._device is not None:
            if hasattr(self, 'owner') and self.owner is not None:
                multiattr = self._device.get_device_attr()
                self._attr = multiattr.get_attr_by_name(self._alias)
            elif self._name is not None:
                multiattr = self._device.get_device_attr()
                self._attr = multiattr.get_attr_by_name(self._name)

    def isAllowed(self):
        if self.device is None:
            return True
        if self.device.get_state in [DevState.FAULT]:
            return False
        return True

    def isReadAllowed(self):
        return self.isAllowed()

    def isWriteAllowed(self, attr=None):
        if attr is not None:
            if not attr.get_writable() in [AttrWriteType.READ_WRITE]:
                return False
        return self.isAllowed()

    @AttrExc
    def read_attr(self, attr):
        if not self.isReadAllowed():
            return
        if attr is not None:
            attrName = self._getAttrName(attr)
            self.info("Received a read request for %s" % attrName)
            self._setTangoAttrReadValue(attr, self.rvalue)

    @AttrExc
    def write_attr(self, attr):
        if not self.isWriteAllowed():
            self.error("%s is not allowed to be written" % (attr.get_name()))
            return
        if attr is not None:
            attrName = self._getAttrName(attr)
            data = []
            attr.get_write_value(data)
            writeValue = data[0]
            self.info("Received a write request for %s, value %s"
                      % (attrName, writeValue))
            self.write_value = writeValue

    @property
    def memorisedLst(self):
        if self._memorisedLst:
            return self._memorisedLst[:]

    def setMemorised(self, suffix=None):
        if not self._memorised:
            self._memorised = Memorised(owner=self)
        if not suffix:
            if not self._memorised.recover():
                self.info("Cannot recover value %sfrom the database"
                          % ("for %s " % self.alias
                             if self.alias is not None else ""))
            self._memorisedLst = []
        elif self._memorisedLst and suffix not in self._memorisedLst:
            self._memorisedLst.append(suffix)
            if self.device is not None:
                self._memorised.recover(suffix)

    def isMemorised(self):
        return self._memorised is not None

    def store(self, value, suffix=None):
        if self.isMemorised():
            return self._memorised.store(value, suffix)
        return False

    def recover(self, suffix=None):
        if self.isMemorised():
            return self._memorised.recover(suffix)
        return False

    ############################
    # First descending level ---
    def _getAttrName(self, attr):
        if hasattr(attr, 'get_name'):
            return attr.get_name()
        if type(attr) == str:
            return attr
        else:
            self._name

    def _setTangoAttrReadValue(self, attr, readValue):
        attrName = self._getAttrName(attr)
        self.debug("_setTangoAttrReadValue(%s, %s, %s, %s)"
                   % (attrName, readValue, self.timestamp, self.quality))
        if not any([isinstance(attr, kls) for kls in [Attribute, WAttribute]]):
            self.warning("Cannot set attribute read value "
                         "for a non Tango Attribute (%s)"
                         % (attr.__class__.__mro__))
            return
        try:
            attr.set_value_date_quality(readValue, self.timestamp,
                                        self.quality)
            # FIXME: check dimensions if the readValue have
            #        set the paramenter
        except Exception as e:
            self.error("_setTangoAttrReadValue(%s, %s, %s, %s) exception %s"
                       % (attrName, readValue, self.timestamp,
                          self.quality, e))
            if hasattr(self, 'noneValue'):
                value = self.noneValue
            else:
                value = self._getTangoAttrNoneValue(attr)
            try:
                attr.set_value_date_quality(value, self.timestamp,
                                            AttrQuality.ATTR_INVALID)
            except Exception as e:
                self.error("neither None value")
            # FIXME: check dimensions if the readValue have
            #        set the paramenter

    def _getTangoAttrNoneValue(self, attr):
        if attr.get_data_size() > 1:
            return []
        data_type = attr.get_data_type()
        if data_type in [DevString]:
            value = ''
        elif data_type in [DevDouble, DevFloat, DevLong, DevLong64,
                           DevULong, DevULong64, DevShort, DevUShort,
                           DevUChar]:
            value = 0
        else:
            value = None
        return value
