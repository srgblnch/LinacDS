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
        setpoint = self._setpointAttr.rvalue
        readback = self._owner.rvalue
        if setpoint is not None and readback is not None:
            self.info("check condition with readback %s and setpoint %s"
                      % (readback, setpoint))
            setpointClose2Zero = (-self._closeZero<setpoint<self._closeZero)
            readbackClose2Zero = (-self._closeZero<readback<self._closeZero)
            if setpointClose2Zero or readbackClose2Zero:
                diff = abs(setpoint - readback)
                self.info("close to zero (readback %s setpoint %s): "
                          "diff = %s (%s)"
                          % (readbackClose2Zero, setpointClose2Zero,
                             diff, self._closeZero))
                if (diff > self._closeZero):
                    return True
            else:
                diff = abs(setpoint / readback)
                # 10%
                below = 1-self._relPercentage > diff
                above = diff > 1+self._relPercentage
                self.info("10%% difference (below %s above %s)"
                          % (below, above))
                if below or above:
                    return True
        else:
            self.debug("No condition to be checked")
        return False
