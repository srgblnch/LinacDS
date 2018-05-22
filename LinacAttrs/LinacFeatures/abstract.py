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


class _AbstractFeatureLog(object):
    def __init__(self, *args, **kwargs):
        super(_AbstractFeatureLog, self).__init__(*args, **kwargs)

    def __checkOwner__(self):
        return hasattr(self, 'owner') and self.owner is not None

    def error(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkOwner__() and hasattr(self.owner, 'error'):
            self.owner.error(msg, tagName=False)
        else:
            print("ERROR: %s" % (msg))

    def warning(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkOwner__() and hasattr(self.owner, 'warning'):
            self.owner.warning(msg, tagName=False)
        else:
            print("WARN: %s" % (msg))

    def info(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkOwner__() and hasattr(self.owner, 'info'):
            self.owner.info(msg, tagName=False)
        else:
            print("INFO: %s" % (msg))

    def debug(self, msg, tagName=True):
        if tagName:
            msg = "[%s] %s" % (self.name, msg)
        if self.__checkOwner__() and hasattr(self.owner, 'debug'):
            self.owner.debug(msg, tagName=False)
        else:
            print("DEBUG: %s" % (msg))
