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

from ..constants import ACTIVE_RESET_T
from .feature import _LinacFeature
from time import ctime, sleep
from threading import Thread, currentThread

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class InterlockReset(_LinacFeature):

    _waitTime = None
    _thread = None

    def __init__(self, waitTime=ACTIVE_RESET_T, *args, **kwargs):
        super(InterlockReset, self).__init__(*args, **kwargs)
        self._waitTime = waitTime

    def prepare(self):
        if self._thread is None:
            self._thread = Thread(target=self.wait)
            self._thread.setDaemon(True)
            self._thread.start()
        else:
            self.error("Reset in progress")

    def wait(self):
        if currentThread() is self._thread:
            self.info("Thread goes to sleep (%g seconds)" % (self._waitTime))
            sleep(self._waitTime)
            self.clean()
        else:
            self.error("This thread is not allowed to call this method")

    def clean(self):
        if currentThread() is self._thread:
            self.info("Clean the reset")
            #self.owner.write_value = False
            self._thread = None
        else:
            self.error("This thread is not allowed to call this method")
