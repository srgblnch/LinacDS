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


class _LinacFeature(object):

    _name = None

    def __init__(self, owner, *args, **kwargs):
        super(_LinacFeature, self).__init__(*args, **kwargs)
        self._name = self.__class__.__name__
        self._owner = owner

    @property
    def name(self):
        if self.owner:
            return "%s:%s" % (self.owner.name, self._name)
        return ":%s" % (self._name)

    @property
    def owner(self):
        return self._owner

    def error(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.owner:
            self.owner.error(msg, tagName=False)
        else:
            print("ERROR: %s" % (msg))

    def warning(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.owner:
            self.owner.warning(msg, tagName=False)
        else:
            print("WARN: %s" % (msg))

    def info(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.owner:
            self.owner.info(msg, tagName=False)
        else:
            print("INFO: %s" % (msg))

    def debug(self, msg):
        msg = "[%s] %s" % (self.name, msg)
        if self.owner:
            self.owner.debug(msg, tagName=False)
        else:
            print("DEBUG: %s" % (msg))
