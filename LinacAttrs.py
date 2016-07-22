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
from PyTango import AttrQuality, Database, DevFailed, DevState, AttrWriteType
from time import time
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


class _LinacAttr(object):
    def __init__(self, name, device=None):
        """ Main superclass for linac attributes.
        """
        super(_LinacAttr, self).__init__()
        self._name = name
        self._memorizedLst = []
        self._tangodb = None
        self.device = device
        self._timestamp = time()
        self._quality = AttrQuality.ATTR_VALID

    # Main Tango part ---
    @property
    def name(self):
        return self._name

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

    def __repr__(self):
        return "%s: %s" % (self, self.keys())

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value
        if value is not None:
            self.debug("Link to the device %s" % self._device)
        self._tangodb = Database()
        for suffix in self.memorizedLst:
            self.recoverDynMemorized(self.name, suffix)

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def quality(self):
        return self._quality

    # Tango log system ---
    def error(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.error_stream(msg)
        else:
            print("ERROR: %s" % (msg))

    def warning(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.warn_stream(msg)
        else:
            print("WARN: %s" % (msg))

    def info(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.info_stream(msg)
        else:
            print("INFO: %s" % (msg))

    def debug(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.device:
            self.device.debug_stream(msg)
        else:
            print("DEBUG: %s" % (msg))

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

    # Tango events area ---
    def fireEvent(self, name, value, quality=None):
        # FIXME: shall be other event types be fired?
        #        archiver, periodic,...
        try:
            if quality is None:
                quality = self.quality
            if self.device is not None:
                self.device.push_change_event(name, value, self.timestamp,
                                              quality)
            self.debug("fireEvent(%s, %s, %s, %s)" % (name, value,
                                                      self.timestamp,
                                                      quality))
        except DevFailed as e:
            self.warning("DevFailed in event %s emit: %s" % (name, e[0].desc))
        except Exception as e:
            self.error("Event for %s (with value %s) not emitted due to: %s"
                       % (name, value, e))

    # Tango memorized dynamic attributes
    @property
    def memorizedLst(self):
        return self._memorizedLst[:]

    def setMemorised(self, suffix):
        if suffix not in self._memorizedLst:
            self._memorizedLst.append(suffix)

    def storeDynMemozized(self, mainName, suffix, value):
        if self.device is None:
            self.warning("Cannot memorize values outside a "
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
            self.warning("Cannot recover memorized values outside a "
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
                self.debug("Recovered %r as %s" % (value, type(value)))
            else:
                self.info("Nothing to recover from %s_%s" % (mainName, suffix))
                return
        except Exception as e:
            self.warning("Property %s_%s couldn't be recovered due to: %s"
                         % (mainName, suffix, e))
        else:
            self.info("Recovering memorised value %s for %s_%s"
                      % (value, mainName, suffix))
            try:
                if hasattr(self, suffix):
                    self.__class__.__dict__[suffix].fset(self, value)
                    readback = self.__class__.__dict__[suffix].fget(self)
                    if value != readback:
                        self.warning("readback %s doesn't corresponds with set %s"
                                     % (value, readback))
                    else:
                        self.debug("Well applied %s_%s: %s"
                                   % (mainName, suffix, value))
            except Exception as e:
                self.error("Exeption recovering %s_%s: %s"
                           % (mainName, suffix, e))

    # Linac's device structure ---
    def __getitem__(self, name):
        try:
            if name in self.keys():
                for kls in self.__class__.__mro__:
                    if name in kls.__dict__.keys():
                        return kls.__dict__[name].fget(self)
        except Exception as e:
            self.error("Cannot get item for the key %s due to: %s" % (name, e))
            return None

    def __setitem__(self, name, value):
        try:
            if name in self.keys():
                for kls in self.__class__.__mro__:
                    if name in kls.__dict__.keys():
                        if kls.__dict__[name].fset is None:
                            kls.__dict__[name].fset(self, value)
                        else:
                            self.warning("%s NO setter" % name)
        except Exception as e:
            self.error("Cannot set item %s to key %s due to: %s"
                       % (value, name, e))

    def keys(self):
        keys = self.__class__.__dict__.keys()
        # special properties of the superclass
        # accessible for all attribute types
        keys += ['timestamp', 'quality']
        return [k for k in keys if not k.startswith('__')]

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


class EnumerationAttr(_LinacAttr):
    def __init__(self, name, optionsLst=None):
        """Precursor for the future CalibrationAttr class. Based on a list,
           provided by the user, that can be modified (and that's why it is
           memorised) provides a numeric access as well as a string meaning
           that combines both: the number and the string associated.
        """
        super(EnumerationAttr, self).__init__(name)
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
        # preprocess ---
        if type(lst) == list and not any([len(each)-1 for each in lst]):
            # candidate a wrong string made list
            rebuild = "".join("%s" % i for i in lst)
            self.debug("Received a wrong string list %s and rebuild to %s"
                       % (lst, rebuild))
            try:
                lst = eval(rebuild)
            except:
                lst = [rebuild]
        if type(lst) == str:
            # FIXME: check the input to avoid issues
            bar = list(literal_eval(lst))
            self.debug("Received a string %r and understand a list: %s"
                       % (lst, bar))
            lst = bar
        # process ---
        if type(lst) == list:
            for i, element in enumerate(lst):
                lst[i] = str(element).lower().strip()
            self._options = lst
            self._quality = AttrQuality.ATTR_VALID
            self.fireEvent(self.name+'_options', str(self.options))
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
                raise ValueError("%s is not in the available options %s"
                                 % (value, self._options))
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
