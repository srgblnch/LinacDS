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

__author__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


from LinacData import AttrExc
from PyTango import AttrQuality
from PyTango import DevState
from time import time


# FIXME: understand why I couldn't make work the *args and **kwargs


class _LinacAttr(object):
    def __init__(self, name, device=None):
        """ Main superclass for linac attributes.
        """
        super(_LinacAttr, self).__init__()
        self._name = name
        self._device = device
        self._timestamp = None
        self._quality = AttrQuality.ATTR_VALID

    # Main Tango part ---
    @property
    def name(self):
        return self._name

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, value):
        self._device = value

    @property
    def timestamp(self):
        return self._timestamp

    @property
    def quality(self):
        return self._quality

    # Tango log system ---
    def error(self, msg):
        if self._device:
            self.device.error_stream(msg)
        else:
            print("ERROR: %s" % (msg))

    def warning(self, msg):
        if self._device:
            self.device.warn_stream(msg)
        else:
            print("WARN: %s" % (msg))

    def info(self, msg):
        if self._device:
            self.device.info_stream(msg)
        else:
            print("INFO: %s" % (msg))

    def debug(self, msg):
        if self._device:
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

    def isWriteAllowed(self):
        return self.isAllowed()

    @AttrExc
    def read_attr(self, attr):
        if not self.isReadAllowed():
            return
        if attr is not None:
            attrName = self._getAttrName(attr)
            suffix = self._getSuffix(attrName)
            if not hasattr(self, suffix):
                # FIXME: no way to read, raise exception
                self.warning("No way to read %s" % suffix)
                return
            readValue = getattr(self, suffix)
            self._setAttrValue(attr, readValue)

    @AttrExc
    def write_attr(self, attr, value=None):
        if not self.isWriteAllowed():
            return
        if attr is not None:
            attrName = self._getAttrName(attr)
            suffix = self._getSuffix(attrName)
            if not hasattr(self, suffix):
                # FIXME: no way to read, raise exception
                self.warning("No way to write %s" % suffix)
                return
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
            self._setAttrValue(attr, writeValue)

    # Tango events area ---
    def fireEvent(self, name, value):
        # FIXME: shall be other event types be fired?
        #        archiver, periodic,...
        if self._device is not None:
            self.device.push_change_event(name, value, self.timestamp,
                                          self.quality)
        else:
            self.info("FireEvent(%s, %s, %s, %s)" % (name, value,
                                                     self.timestamp,
                                                     self.quality))

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
        if attrName.count('_') == 0:
            # TODO: there would be a default main reading
            self.warning("No default reading for %s" % (attrName))
            return
        else:
            nothing, suffix = attrName.rsplit('_')
            return suffix

    def _setAttrValue(self, attr, readValue):
        if type(attr) == str:
            self.info("(%s, %s, %s)" % (readValue, self.timestamp,
                                        self.quality))
        else:
            attr.set_value_date_quality(readValue, self.timestamp,
                                        self.quality)


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
        elif type(optionsLst) == list:
            self._options = optionsLst
        else:
            raise TypeError("options shall be a list (not %s)"
                            % type(optionsLst))
        self._active = None

    @property
    def options(self):
        """List of the options in the enumeration
        """
        return self._options[:]

    @options.setter
    def options(self, lst):
        if type(lst) == list:
            self._options = lst
            if self._active is not None:
                # The active may have changed once the list change
                self.active = self._activ
        else:
            raise TypeError("options shall be a list")

    @property
    def active(self):
        """Indicates which of the options is activated by the user selection.
        """
        if len(self._options) > 0:
            return self._active
        raise ValueError("no options defined")

    @active.setter
    def active(self, value):
        if type(value) == int and value <= len(self._options):
            toBeActive = self._options[value]
        elif value in self._options:
            toBeActive = value
        else:
            raise ValueError("%s is not in the available options" % value)
        self._active = toBeActive
        self._timestamp = time()
        self.fireEvent(self.name+'_number', self.number)
        self.fireEvent(self.name+'_string', self.string)

    @property
    def number(self):
        """Machine-friendly output with the element active.
        """
        if self._active is None:
            raise ValueError("No selection made with the options")
        return self._options.index(self.active)

    @number.setter
    def number(self, value):
        if type(value) == int:
            self.active = value

    @property
    def string(self):
        """Humane-friendly output with the element active.
        """
        if self._active is None:
            raise ValueError("No selection made with the options")
        return "%d:%s" % (self._options.index(self.active), self.active)
