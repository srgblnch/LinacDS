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
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

from feature import _LinacFeature
from PyTango import Database


defaultFieldName = '__value'


class Memorised(_LinacFeature):

    _storeValue = {}
    _recoverValue = {}

    def __init__(self, *args, **kwargs):
        super(Memorised, self).__init__(*args, **kwargs)
        self._tangodb = Database()

    def store(self, value, suffix=None):
        if self._owner is None or self._owner.device is None:
            self.warning("Cannot memorise values outside a "
                         "tango device server")
            return False
        devName = self._owner.device.get_name()
        attrName = self._owner.name
        fieldName = suffix or defaultFieldName
        memorisedName = devName+"/"+attrName
        self.info("Memorising attribute %s%s with value %s"
                  % (mainName, "_%s" % suffix if suffix else "", value))
        try:
            self._tangodb.put_device_attribute_property(memorisedName,
                                                        {attrName:
                                                         {fieldName:
                                                          str(value)}})
        except Exception as e:
            self.warning("Property %s_%s cannot be stored due to: %s"
                         % (attrName, "_%s" % suffix if suffix else "", e))
            return False
        self._storeValue[fieldName] = value
        return True

    def recover(self, suffix=None):
        """
            Recover the value from the tangoDB
        """
        if self._owner is None or self._owner.device is None:
            self.warning("Cannot recover memorised values outside a "
                         "tango device server")
            return False
        devName = self._owner.device.get_name()
        attrName = self._owner.name
        fieldName = suffix or defaultFieldName
        memorisedName = devName+"/"+attrName
        try:
            property = self._tangodb.\
                get_device_attribute_property(memorisedName, [attrName])
            if attrName in property and fieldName in property[attrName]:
                try:
                    value = literal_eval(property[attrName][fieldName][0])
                except:
                    value = property[attrName][fieldName][0]
                self.info("Recovered %r as %s" % (value, type(value)))
            else:
                self.info("Nothing to recover from %s%s"
                          % (attrName, "_%s" % suffix if suffix else ""))
                return False
        except Exception as e:
            self.warning("Property %s%s couldn't be recovered due to: %s"
                         % (attrName, "_%s" % suffix if suffix else "", e))
        else:
            self.info("Recovering memorised value %r for %s%s"
                      % (value, attrName, "_%s" % suffix if suffix else ""))
            if hasattr(self, fieldName):
                self._applyValue(attrName, fieldName, value)
            else:
                self._applyValue(attrName, 'read_value', value)
        self._recoverValue[fieldName] = value
        return True

    def _applyValue(self, attrName, field, value, check=True):
        try:
            self.__class__.__dict__[field].fset(self, value)
            if check:
                readback = self.__class__.__dict__[field].fget(self)
                if value != readback:
                    self.warning("readback %s doesn't corresponds with set %s"
                                 % (value, readback))
                else:
                    self.info("Well applied %s[%s]: %s"
                              % (attrName, field, value))
        except Exception as e:
            self.error("Exception applying %s[%s]: %s"
                       % (attrName, field, value))

    def getStoreValue(self, suffix=None):
        if not suffix:
            if defaultFieldName in self._storeValue:
                return self._storeValue[defaultFieldName]
        else:
            if suffix in self._storeValue:
                return self._storeValue[suffix]
        # other case return None

    def getRecoverValue(self, suffix=None):
        if not suffix:
            if defaultFieldName in self._recoverValue:
                return self._recoverValue[defaultFieldName]
        else:
            if suffix in self._recoverValue:
                return self._recoverValue[suffix]
        # other case return None
