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


# Circular buffer to store last read values and based on it average define ---
# the attribute quality
import numpy as np
from types import MethodType
from feature import _LinacFeature

DEFAULT_SIZE = 10


class CircularBuffer(_LinacFeature):
    '''This is made to implement an automatic circular buffer using numpy array
       and get some statistical values from the collected data.
       This is used for attributes with changing qualities based on std of
       the last readings. The only way to have that is with a little historic
       of the read values to know if it's readings are below some threshold
       or not.
       It is also used for the collection of number of events emitted and the
       time used for each loop for event emission.
    '''

    def __init__(self, buffer, maxlen=DEFAULT_SIZE, *args, **kwargs):
        super(CircularBuffer, self).__init__(*args, **kwargs)
        self.__maxlen = maxlen
        self._mean = float('NaN')
        self._std = float('NaN')
        self._append_cb = []
        if type(buffer) == list:
            self._buffer = np.array(buffer[-self.__maxlen:])
            if self._buffer.ndim > 1:
                raise BufferError("Not supported multi-dimensions")
        else:
            raise BufferError("Input buffer invalid")

    def __str__(self):
        return self._buffer.__str__()

    def __repr__(self):
        return self._buffer.__repr__()

    def __len__(self):
        return len(self._buffer)

    def __float__(self):
        try:
            return float(self.value)
        except:
            return float('NaN')

    def __int__(self):
        return int(self.value)

    def append(self, value):
        if len(self._buffer) > 0:
            self._buffer = np.append(self._buffer, value)[-self.__maxlen:]
        else:
            self._buffer = np.array([value])
        if self._append_cb:
            self.debug("has %d callback(s)" % (len(self._append_cb)))
            for cb in self._append_cb:
                if callable(cb) and isinstance(cb, MethodType):
                    self.debug("proceeding with callback %s.%s()"
                               % (cb.im_self.name, cb.__name__))
                    cb()

    def append_cb(self, func):
        self._append_cb.append(func)

    def pop_cb(self, func):
        if self._append_cb.count(func):
            return self._append_cb.pop(self._append_cb.index(func))

    @property
    def mean(self):
        if len(self._buffer) > 0:
            return self._buffer.mean()
        else:
            return float('NaN')

    @property
    def std(self):
        if len(self._buffer) > 0:
            return self._buffer.std()
        else:
            return float('NaN')

    @property
    def meanAndStd(self):
        return (self.mean, self.std)

    @property
    def max(self):
        if len(self._buffer) > 0:
            return self._buffer.max()
        else:
            return float('NaN')

    @property
    def min(self):
        if len(self._buffer) > 0:
            return self._buffer.min()
        else:
            return float('NaN')

    @property
    def value(self):
        if len(self._buffer) > 0:
            return self._buffer[-1]
        else:
            return None

    @property
    def array(self):
        if len(self._buffer) > 0:
            return self._buffer
        else:
            return np.array([])

    def maxSize(self):
        return self.__maxlen

    def resize(self, newMaxLen):
        self.__maxlen = newMaxLen

    def resetBuffer(self):
        self._buffer = np.array([])


class HistoryBuffer(CircularBuffer):
    def __init__(self, cleaners, *args, **kwargs):
        super(HistoryBuffer, self).__init__([], *args, **kwargs)
        self._cleaners = cleaners

    def append(self, newElement):
        if newElement in self._cleaners:
            self._buffer = np.array([newElement])
        else:
            CircularBuffer.append(self, newElement)
