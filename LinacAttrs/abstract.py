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

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


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
