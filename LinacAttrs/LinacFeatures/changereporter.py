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
import traceback

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class ChangeReporter(_LinacFeature):

    _report_to = None

    # TODO: those changes report may come from more attributes than Logic
    # TODO: those changes may be triggered from read or write operations
    #       and may trigger different operations in the reported attr.

    def __init__(self, *args, **kwargs):
        super(ChangeReporter, self).__init__(*args, **kwargs)
        self._str_ = "%s:ChangeReporter" % (self.owner.name)
        self._report_to = []
        self.debug("becomes a reporter")

    def __str__(self):
        names = []
        for each in self._report_to:
            names.append(each.name)
        return "%s (to %s)" % (self._str_, names)

    def __repr__(self):
        return self.__str__()

    def addDestination(self, obj):
        self._report_to.append(obj)
        self.debug("has new destination to report: %s" % (obj.name))

    def report(self):
        for obj in self._report_to:
            try:
                if hasattr(obj, 'evaluateAttrValue'):
                    obj.evaluateAttrValue()
                else:
                    self.warning("%s cannot report to %s"
                                 % (self.owner, obj.name))
            except Exception as e:
                self.error("%s fail to report to %s: %s"
                           % (self.owner, obj.name, e))
                traceback.print_exc()
            else:
                self.debug("%s change reported to %s" % (self.owner, obj.name))
