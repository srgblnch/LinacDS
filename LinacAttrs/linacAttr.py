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
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


from ast import literal_eval
import functools
from LinacFeatures import Events
from PyTango import AttrQuality, Database, DevFailed, DevState, AttrWriteType
from PyTango import DevUChar, DevShort, DevFloat, DevDouble
from PyTango import DevBoolean, DevString
from time import time, ctime
import traceback


# FIXME: understand why I couldn't make work the *args and **kwargs


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


TYPE_MAP = {DevUChar: ('B', 1),
            DevShort: ('h', 2),
            DevFloat: ('f', 4),
            DevDouble: ('f', 4),
            # the PLCs only use floats of 4 bytes
            }


class LinacAttr(object):

    _readValue = None
    _writeValue = None

    _device = None

    _qualities = None
    _eventsObj = None
    _events = None
    _event_t = None
    _lastEventQuality = AttrQuality.ATTR_INVALID

    _AutoStop = None

    def __init__(self, name, valueType, device=None, *args, **kwargs):
        """ Main superclass for linac attributes.
        """
        super(LinacAttr, self).__init__(*args, **kwargs)
        self._name = name
        if valueType is None:
            self._type = None
        elif valueType in [DevString, DevBoolean]:
            self._type = valueType
        else:
            self._type = TYPE_MAP[valueType]
        self._memorizedLst = []
        self._tangodb = None
        self.device = device
        self._timestamp = time()
        self._quality = AttrQuality.ATTR_VALID

    def __str__(self):
        return "%s (%s)" % (self.name, self.__class__.__name__)

    def __repr__(self):
        repr = "%s:\n" % self
        for key in self.keys():
            if self[key] is None:
                pass  # ignore
            elif type(self[key]) is list and len(self[key]) == 0:
                pass  # ignore
            else:
                repr += "\t%s: %s\n" % (key, self[key])
        return repr

    ################
    # properties ---
    @property
    def name(self):
        return self._name

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        if value is not None:
            # self.debug("Link to the device %s" % value)
            self._device = value
        self._tangodb = Database()
        for suffix in self.memorizedLst:
            self.recoverDynMemorized(self.name, suffix)

    # TODO
    # @property
    # def value(self):
    #     pass

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def quality(self):
        return self._quality

    @property
    def type(self):
        return self._type

    ######################
    # Tango log system ---
    def error(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.error_stream(msg)
        else:
            print("ERROR: %s" % (msg))

    def warning(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.warn_stream(msg)
        else:
            print("WARN: %s" % (msg))

    def info(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.info_stream(msg)
        else:
            print("INFO: %s" % (msg))

    def debug(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.debug_stream(msg)
        else:
            print("DEBUG: %s" % (msg))

    #####################################
    # Dictionary like functionalities ---
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

    def keys(self):
        # FIXME: should this list be made only once?
        keys = []
        discarted = []
        for kls in self.__class__.__mro__:
            klskeys = []
            klsdiscarted = []
            for key, value in kls.__dict__.iteritems():
                if isinstance(value, property):
                    klskeys += [key]
                else:
                    klsdiscarted += [key]
#             self.info("kls: %s" % (kls))
#             self.info("\t* kls keys: %s" % (klskeys))
#             self.info("\t* kls discarted: %s" % (klsdiscarted))
            keys += klskeys
            discarted += klsdiscarted
#         self.info("* keys: %s" % (keys))
#         self.info("* discarted: %s" % (discarted))
        return keys

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

    #######################################################
    # Dictionary properties for backwards compatibility ---
    @property
    def read_value(self):
        return self._readValue

    @read_value.setter
    def read_value(self, value):
        self._readValue = value

    @property
    def write_value(self):
        return self._writeValue

    @write_value.setter
    def write_value(self, value):
        self._writeValue = value

    @property
    def read_t(self):
        return self._timestamp

    @read_t.setter
    def read_t(self, value):
        self._timestamp = value

    @property
    def read_t_str(self):
        if self._timestamp:
            return ctime(self._timestamp)
        return ""

    @property
    def qualities(self):
        return self._qualities

    @qualities.setter
    def qualities(self, value):
        self._qualities = value

    @property
    def events(self):
        return self._events

    @events.setter
    def events(self, value):
        if value:
            self._eventsObj = Events(owner=self)
        else:
            self._eventsObj = None
        self._events = value

    @property
    def event_t(self):
        return self._event_t

    @event_t.setter
    def event_t(self, value):
        self._event_t = value

    @property
    def event_t_str(self):
        if self._event_t:
            return ctime(self._event_t)
        return ""

    @property
    def lastEventQuality(self):
        return self._lastEventQuality

    @lastEventQuality.setter
    def lastEventQuality(self, value):
        self._lastEventQuality = value

    @property
    def AutoStop(self):
        return self._AutoStop

    @AutoStop.setter
    def AutoStop(self, value):
        self._AutoStop = value

    ##########################
    # Tango attribute area ---
    def isAllowed(self):
        if self.device is None:
            return True
        if self.device.get_state() in [DevState.FAULT]:
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
            suffix = self._getSuffix(attrName)
            if not hasattr(self, suffix):
                # FIXME: no way to read, raise exception
                self.warning("No way to read %s" % suffix)
                return  # raise ValueError("Can NOT read %s" % suffix)
            readValue = getattr(self, suffix)
            self._setAttrValue(attr, readValue)

    @AttrExc
    def write_attr(self, attr, value=None):
        if not self.isWriteAllowed():
            return
        if attr is not None:
            attrName = self._getAttrName(attr)
            self.debug("Received a write request for %s, value %s"
                       % (attrName, value))
            suffix = self._getSuffix(attrName)
            if not hasattr(self, suffix):
                # FIXME: no way to read, raise exception
                self.warning("No way to write %s" % suffix)
                return  # raise ValueError("Can NOT write %s" % suffix)
            if hasattr(attr, 'get_write_value'):
                data = []
                attr.get_write_value(data)
                writeValue = data[0]
            elif value is not None:
                writeValue = value
            else:
                self.warning("No value to write")
                return
            self.__class__.__dict__[suffix].fset(self, writeValue)
            readValue = getattr(self, suffix)
            if suffix in self.memorizedLst:
                self.storeDynMemozized(self.name, suffix, readValue)
            self._setAttrValue(attr, readValue)

    #######################
    # Tango events area ---
    def fireEvent(self, name, value, quality=None):
        if self._eventsObj:
            self._eventsObj.FireEvent(name, value, quality)
#         # FIXME: shall be other event types be fired?
#         #        archiver, periodic,...
#         try:
#             if quality is None:
#                 quality = self.quality
#             if self.device is not None:
#                 self.device.push_change_event(name, value, self.timestamp,
#                                               quality)
#             self.debug("fireEvent(%s, %s, %s, %s)" % (name, value,
#                                                       self.timestamp,
#                                                       quality))
#         except DevFailed as e:
#             self.warning("DevFailed in event %s emit: %s"
#                          % (name, e[0].desc))
#         except Exception as e:
#             self.error("Event for %s (with value %s) not emitted due to: %s"
#                        % (name, value, e))

    ########################################
    # Tango memorized dynamic attributes ---
    @property
    def memorizedLst(self):
        return self._memorizedLst[:]

    def setMemorised(self, suffix):
        if suffix not in self._memorizedLst:
            self._memorizedLst.append(suffix)
            if self.device is not None:
                self.recoverDynMemorized(self.name, suffix)

    def storeDynMemozized(self, mainName, suffix, value):
        if self.device is None:
            self.warning("Cannot memorise values outside a "
                         "tango device server")
            return
        self.info("Memorising attribute %s_%s with value %s"
                  % (mainName, suffix, value))
        memoriseName = self.device.get_name() + "/" + mainName
        try:
            self._tangodb.put_device_attribute_property(memoriseName,
                                                        {mainName:
                                                         {suffix: str(value)}})
        except Exception as e:
            self.warning("Property %s_%s cannot be stored due to: %s"
                         % (mainName, suffix, e))

    def recoverDynMemorized(self, mainName, suffix):
        if self.device is None:
            self.warning("Cannot recover memorised values outside a "
                         "tango device server")
            return
        memoriseName = self.device.get_name() + "/" + mainName
        try:
            property = self._tangodb.\
                get_device_attribute_property(memoriseName, [mainName])
            if mainName in property and suffix in property[mainName]:
                try:
                    value = literal_eval(property[mainName][suffix][0])
                except:
                    value = property[mainName][suffix][0]
                self.info("Recovered %r as %s" % (value, type(value)))
            else:
                self.info("Nothing to recover from %s_%s" % (mainName, suffix))
                return
        except Exception as e:
            self.warning("Property %s_%s couldn't be recovered due to: %s"
                         % (mainName, suffix, e))
        else:
            self.info("Recovering memorised value %r for %s_%s"
                      % (value, mainName, suffix))
            try:
                if hasattr(self, suffix):
                    self.__class__.__dict__[suffix].fset(self, value)
                    readback = self.__class__.__dict__[suffix].fget(self)
                    if value != readback:
                        self.warning("readback %s doesn't corresponds with "
                                     "set %s" % (value, readback))
                    else:
                        self.info("Well applied %s_%s: %s"
                                  % (mainName, suffix, value))
            except Exception as e:
                self.error("Exception recovering %s_%s: %s"
                           % (mainName, suffix, e))

    ############################
    # First descending level ---
    def _getAttrName(self, attr):
        if type(attr) == str:
            return attr
        else:
            return attr.get_name()

    def _getSuffix(self, attrName):
        if not attrName.startswith(self.name):
            # FIXME: review naming, but it shall raise an exception
            self.warning("attrName %s is not starting with %s"
                         % (attrName, self.name))
            return
        if attrName == self.name:
            # TODO: there shall be a default behaviour for attrs with no suffix
            return ''
        if attrName.count('_') == 0:
            self.warning("No separable name to distinguish suffix (%s)"
                         % (attrName))
            return ''
        else:
            _, suffix = attrName.rsplit('_', 1)
            return suffix

    def _setAttrValue(self, attr, readValue):
        if type(readValue) == list:
            readValue = "%s" % readValue
        attrName = self._getAttrName(attr)
        self.debug("_setAttrValue(%s, %s, %s, %s)"
                   % (attrName, readValue, self.timestamp, self.quality))
        if type(attr) != str:
            # If its an attribute, part of a device, do the corresponding set
            # print("type(attr) = %s" % type(attr))
            try:
                if self.isWriteAllowed(attr):
                    attr.set_write_value(readValue)
                attr.set_value_date_quality(readValue, self.timestamp,
                                            self.quality)
            except Exception as e:
                self.error("_setAttrValue(%s, %s, %s, %s) exception %s"
                           % (attrName, readValue, self.timestamp,
                              self.quality, e))
                attr.set_value_date_quality('', self.timestamp,
                                            AttrQuality.ATTR_INVALID)