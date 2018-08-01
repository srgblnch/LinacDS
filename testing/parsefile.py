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

from os import path
import PyTango
from PyTango import AttrQuality
from constants import *

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2018, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

def john(sls):
    '''used to encode the messages shown for each state code
    '''
    if type(sls) == dict:
        return '\n'+''.join('%d:%s\n' % (t, sls[t]) for t in sls.keys())
    else:
        return '\n'+''.join('%d:%s\n' % t for t in enumerate(sls))

class ParseFile(object):

    _attrs = None

    def __init__(self):
        super(ParseFile, self).__init__()
        self.locals_ = {}
        self.globals_ = globals()
        self.globals_.update({
            'Attr': self.process,
            'AttrBit': self.process,
            'GrpBit': self.process,
            'AttrLogic': self.process,
            'AttrRampeable': self.process,
            'AttrPLC': self.thethee,
            'AttrEnumeration': self.process,
        })
        self._attrs = {}

    @property
    def attrs(self):
        return self._attrs

    def process(self, name, T=None, read_bit=None, logic=None,
                *args, **kwargs):
        # # label=None, desc=None, qualities=None,
        #         read_addr=None, read_bit=None,
        #         write_addr=None, write_bit=None,
        #         minValue=None, maxValue=None, unit=None, format=None,
        #         readback=None, setpoint=None, switch=None,
        #         memorized=False, logLevel=None, xdim=0,
        #         historyBuffer=None, IamChecker=None, events=None, *args, **kwargs):
        self._attrs[name] = {}
        if T in [PyTango.DevFloat, PyTango.DevDouble]:
            self._attrs[name]['type'] = 'float'
        elif T in [PyTango.DevShort, PyTango.DevUChar] or \
                read_bit is not None or logic is not None:
            self._attrs[name]['type'] = 'int'

    def thethee(self, HeartBeat, Lock_ST,
                rLockingAddr, rLockingBit, wLockingAddr, wLockingBit):
        pass

    def parse_file(self, fname):
        try:
            fullname = "%s/%s" % (path.dirname(path.abspath(__file__)),fname)
            execfile(fullname, self.globals_, self.locals_)
        except Exception as e:
            print("ERROR: %s" % e)
