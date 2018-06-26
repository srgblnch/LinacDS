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

from .historyAttr import HistoryAttr, BASESET
from .linacAttrBase import LinacAttrBase
from .LinacFeatures import Events, ChangeReporter
from .LinacFeatures import HistoryBuffer

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class LinacAttr(LinacAttrBase):

    _historyObj = None

    _AutoStop = None
    _switchDescriptor = None

    _changeReporter = None

    def __init__(self, *args, **kwargs):
        super(LinacAttr, self).__init__(*args, **kwargs)

    @property
    def AutoStop(self):
        return self._AutoStop

    @AutoStop.setter
    def AutoStop(self, value):
        self._AutoStop = value

    @property
    def switchDescriptor(self):
        return self._switchDescriptor

    @switchDescriptor.setter
    def switchDescriptor(self, value):
        self._switchDescriptor = value

    @property
    def history(self):
        if hasattr(self, '_historyObj') and self._historyObj:
            return self._historyObj

    @history.setter
    def history(self, value):
        if value is not None:
            self._historyObj = HistoryAttr(owner=self)
            if isinstance(value, dict):
                if BASESET in value:
                    self._historyObj.baseSet = value[BASESET]
        else:
            self._historyObj = None

    # FIXME: other features in plcAttr can be moved here to be available for
    #        internal attributes also.

    #############################################################
    # Dependencies between attributes and changes propagation ---
    def addReportTo(self, obj, methodName=None):
        if self._changeReporter is None:
            self._changeReporter = ChangeReporter(self)
        self._changeReporter.addDestination(obj,
                                            methodName or 'evaluateAttrValue')

    @property
    def reporter(self):
        return self._changeReporter
