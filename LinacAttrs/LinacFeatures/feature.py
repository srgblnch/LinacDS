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

from .abstract import _AbstractFeatureLog

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class _LinacFeature(_AbstractFeatureLog):

    _name = None
    _owner = None

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


