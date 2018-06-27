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

from .feature import _LinacFeature
from PyTango import Database
import traceback

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


defaultFieldName = '__value'


class Memorised(_LinacFeature):

    _storeValue = None
    _recoverValue = None

    def __init__(self, *args, **kwargs):
        super(Memorised, self).__init__(*args, **kwargs)
        self._tangodb = Database()
        self._storeValue = {}
        self._recoverValue = {}

    def __str__(self):
        if self.owner.alias:
            name = "%s (Memorised)" % self.owner.alias
        else:
            name = "%s (Memorised)" % self.owner.name
        return name

    def __repr__(self):
        content = ""
        if len(self._recoverValue) > 0:
            content = "%s\n\tRecover:" % (content)
            for key in self._recoverValue:
                content = "%s %s:%s" % (content, key, self._recoverValue[key])
        if len(self._storeValue) > 0:
            content = "%s \n\tStore:" % (content)
            for key in self._storeValue:
                content = "%s %s:%s" % (content, key, self._storeValue[key])
        return "%s%s" % (self.__str__(), content)

    def store(self, value, suffix=None):
        if self._owner is None or self._owner.device is None:
            self.warning("Cannot memorise values %soutside a "
                         "tango device server"
                         % ("for %s " % self._owner.alias
                            if self._owner.alias is not None else ""))
            return False
        devName = self._owner.device.get_name()
        attrName = self._owner.alias or self._owner.name
        fieldName = suffix or defaultFieldName
        memorisedName = devName+"/"+attrName
        self.info("Memorising attribute %s%s with value %s"
                  % (attrName, "_%s" % suffix if suffix else "", value))
        try:
            self._tangodb.put_device_attribute_property(memorisedName,
                                                        {attrName:
                                                         {fieldName:
                                                          str(value)}})
            self.info("put_device_attribute_property(%s,{%s:{%s:%s}})"
                      % (memorisedName, attrName, fieldName, str(value)))
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
            self.warning("Cannot recover memorised values %soutside a "
                         "tango device server"
                         % ("for %s " % self._owner.alias
                            if self._owner.alias is not None else ""))
            return False
        devName = self._owner.device.get_name()
        attrName = self._owner.alias or self._owner.name
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
                self._applyValue(attrName, value, fieldName)
            else:
                self._applyValue(attrName, value)
        self._recoverValue[fieldName] = value
        return True

    def _applyValue(self, attrName, value, field=None, check=True,
                    silent=False):
        if field is None:
            for fieldCandidate in ['wvalue', 'rvalue']:
                if self._applyValue(attrName, value, field=fieldCandidate,
                                    check=check, silent=True):
                    self.info("Applied %s to %s[%s]" % (str(value), attrName,
                                                        fieldCandidate))
                    return True
            self.error("Unknown field candidate to apply %s to %s"
                       % (str(value), attrName))
        try:
            dct = self._owner.__class__.__dict__
            if dct[field] is not None:
                dct[field].fset(self._owner, value)
                if check:
                    readback = dct[field].fget(self._owner)
                    if value != readback:
                        if not silent:
                            self.warning("readback %s doesn't corresponds "
                                         "with set %s" % (value, readback))
                return True
        except Exception as e:
            if not silent:
                self.error("Exception applying %s[%s]: %s -> %s(%s)"
                           % (attrName, field, value, type(e).__name__, e))
        return False

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
