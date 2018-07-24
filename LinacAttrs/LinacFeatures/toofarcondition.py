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

from ..constants import CLOSE_ZERO, REL_PERCENTAGE
from .feature import _LinacFeature

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

ATTR='Attr'

class TooFarCondition(_LinacFeature):

    _setpointAttr = None
    _closeZero = None
    _relPercentage = None

    def __init__(self, setpointAttr, closeZero=CLOSE_ZERO,
                 relPercentage=REL_PERCENTAGE, *args, **kwargs):
        super(TooFarCondition, self).__init__(*args, **kwargs)
        self._setpointAttr = setpointAttr
        self._closeZero = closeZero
        self._relPercentage = relPercentage
        self.info("Build TooFarCondition feature object")

    @property
    def setpointAttr(self):
        return self._setpointAttr

    def checkCondition(self):
        self.info("check condition")
        setpoint = self._setpointAttr.rvalue
        readback = self._owner.rvalue
        if (-self._closeZero < setpoint < self._closeZero) or readback == 0:
            # self.info("(%s < %s < %s) or (%s == 0): %s or %s"
            #           % (-self._closeZero, setpoint, self._closeZero,
            #              readback,
            #              -self._closeZero < setpoint < self._closeZero,
            #              readback == 0))
            diff = abs(setpoint - readback)
            # self.info("diff: abs(%s-%s) = %s" % (setpoint, readback, diff))
            if (diff > self._closeZero):
                return True
        else:
            diff = abs(setpoint / readback)
            # self.info("diff: abs(%s/%s) = %s" % (setpoint, readback, diff))
            # 10%
            # self.info("(1-%s > %s) or (%s > 1+%s) = %s or %s = %s"
            #          % (self._relPercentage, diff, diff, self._relPercentage,
            #             1 - self._relPercentage > diff,
            #             diff > 1 + self._relPercentage,
            #             (1 - self._relPercentage > diff or
            #              diff > 1 + self._relPercentage)))
            if (1 - self._relPercentage > diff or
                    diff > 1 + self._relPercentage):
                return True
        return False
