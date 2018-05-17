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

from feature import _LinacFeature

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


class Logic(_LinacFeature):

    _logic = None
    _operator = None
    _inverted = None

    def __init__(self, owner, logic=None, operator=None, inverted=None,
                 *args, **kwargs):
        super(Logic, self).__init__(owner=owner, *args, **kwargs)
        self._str_ = "%s:Logic" % (self.owner.name)
        self._logic = logic
        self._operator = operator # FIXME: check if it is a valid operator
        self._inverted = inverted
        # TODO: include the logic evaluation 
        #       - triggered by callbacks
        #       - with the necessary event emission

    def __str__(self):
        return "%s (%s, %s, %s)" % (self._str_, self._logic, self._operator,
                                    "inverted" if self._inverted else "normal")

    def __repr__(self):
        return self.__str__()

    #@property
    #def logic(self):
    #    return self._logic

    #@property
    #def operator(self):
    #    return self._operator

    #@property
    #def inverted(self):
    #    return self._inverted
