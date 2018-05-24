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
from PyTango import DevState, AttrWriteType
from PyTango import Database
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


class _AbstractAttrLog(object):
    def __init__(self, *args, **kwargs):
        super(_AbstractAttrLog, self).__init__(*args, **kwargs)

    def __checkDevice__(self):
        return hasattr(self, 'device') and self.device is not None

    def error(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkDevice__() and hasattr(self.device, 'error_stream'):
            self.device.error_stream(msg)
        else:
            print("ERROR: %s" % (msg))

    def warning(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkDevice__() and hasattr(self.device, 'warn_stream'):
            self.device.warn_stream(msg)
        else:
            print("WARN: %s" % (msg))

    def info(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkDevice__() and hasattr(self.device, 'info_stream'):
            self.device.info_stream(msg)
        else:
            print("INFO: %s" % (msg))

    def debug(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkDevice__() and hasattr(self.device, 'debug_stream'):
            self.device.debug_stream(msg)
        else:
            print("DEBUG: %s" % (msg))


class _AbstractAttrDict(object):

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
            # self.info("kls: %s" % (kls))
            # self.info("\t* kls keys: %s" % (klskeys))
            # self.info("\t* kls discarted: %s" % (klsdiscarted))
            keys += klskeys
            discarted += klsdiscarted
        # self.info("* keys: %s" % (keys))
        # self.info("* discarted: %s" % (discarted))
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

class _AbstractAttrTango(object):

    _device = None

    _memorised = None
    _memorisedLst = None

    def __init__(self, device=None, memorized=False, *args, **kwargs):
        super(_AbstractAttrTango, self).__init__(*args, **kwargs)
        self.device = device
        if memorized:
            self.setMemorised()
#             self._memorised = Memorised(owner=self)
#             if not self._memorised.recover():
#                 self.warning("Cannot recover value from the database")
#             self._memorisedLst = []

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        if value is not None:
            # self.debug("Link to the device %s" % value)
            self._device = value
        self._tangodb = Database()
        if self._memorisedLst:
            for suffix in self._memorisedLst:
                self._memorised.recover(suffix)

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
            self.debug("Received a read request for %s" % attrName)
#             suffix = self._getSuffix(attrName)
#             print suffix
#             print "%r"%self
#             if not hasattr(self, suffix):
#                 # FIXME: no way to read, raise exception
#                 self.warning("No way to read %s" % suffix)
#                 return  # raise ValueError("Can NOT read %s" % suffix)
#             readValue = getattr(self, suffix)
            self._setAttrValue(attr, self.value)

    @AttrExc
    def write_attr(self, attr, value=None):
        if not self.isWriteAllowed():
            return
        if attr is not None:
            # stablish the data to be written
            if hasattr(attr, 'get_write_value'):
                data = []
                attr.get_write_value(data)
                writeValue = data[0]
            elif value is not None:
                writeValue = value
            else:
                self.warning("No value to write")
                return
            # then work with the attribute
            attrName = self._getAttrName(attr)
            self.info("Received a write request for %s, value %s"
                      % (attrName, writeValue))
            suffix = self._getSuffix(attrName)
            if self.alias == attrName:
                self.rvalue = writeValue
                readValue = self.value
            elif not hasattr(self, suffix):
                # FIXME: no way to read, raise exception
                self.warning("No way to write %s for %s"
                             % (suffix, self.alias))
                return  # raise ValueError("Can NOT write %s" % suffix)
            else:
                self.__class__.__dict__[suffix].fset(self, writeValue)
                readValue = getattr(self, suffix)
            if self._memorisedLst is not None:
                if suffix in self._memorisedLst:
                    self._memorised.store(readValue, suffix)
                elif len(self._memorisedLst) == 0:
                    self._memorised.store(readValue)
            self._setAttrValue(attr, readValue)

    @property
    def memorisedLst(self):
        if self._memorisedLst:
            return self._memorisedLst[:]

    def setMemorised(self, suffix=None):
        if not self._memorised:
            self._memorised = Memorised(owner=self)
        if not suffix:
            if not self._memorised.recover():
                self.warning("Cannot recover value %sfrom the database"
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
