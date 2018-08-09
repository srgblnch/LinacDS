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

from testing import (Test01_Constructors,
                     Test02_AttrsRead,
                     Test03_AttrsWrite,
                     Test11_TooFar
                     )
from unittest import main

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

# TODO: To complete the coverage:
# 1 read with checks on the qualities
# 2 write attributes
#   * done what it is to write the same value without raise an exception
#   * pending to write other valid values as well as provoque the exceptions
#     when invalid values are tried to be write.
# * Event generation (events are generated with the expected values)
# * Circular buffers (how different values affect those buffers)
# * Attr memorised (make sure the values are well stored, but also recovered)
# * Meaning attributes (construction of those strings from the ints)
# * History attributes (special case of buffer with certain resets)
# * AutoStop
#   * Well collection of data when on and no data collection if off
#   * reproduce the stop
# * change reporter (test relations propagation)
# * Formulas & masks / logic attrs
# 11 TooFar condition
# * switches and resets
# * group attributes
# * Force to rewrite the write DataBlock

if __name__ == '__main__':
    main()
