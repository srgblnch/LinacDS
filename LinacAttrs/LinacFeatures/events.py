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


class Events(_LinacFeature):
    def __init__(self, *args, **kwargs):
        super(Events, self).__init__(*args, **kwargs)

    def fireEvent(self, attrName, value, quality=None):
        if self._owner is None or self._owner.device is None:
            self.warning("Cannot emit events outside a tango device server")
            return
        try:
            if quality is None:
                quality = self.quality
            if self._owner.device is not None:
                self._owner.device.push_change_event(attrName, value,
                                                     self._owner.timestamp,
                                                     quality)
            self.debug("%s.fireEvent(%s, %s, %s, %s)" % (self.name,
                                                         attrName, value,
                                                         self._owner.timestamp,
                                                         quality))
        except DevFailed as e:
            self.warning("DevFailed in event %s emit: %s"
                         % (self.name, e[0].desc))
        except Exception as e:
            self.error("Event for %s (with value %s) not emitted due to: %s"
                       % (self.name, value, e))
