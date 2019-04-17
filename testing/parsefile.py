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

from .attrdescr import Descriptor
from constants import *
from json import dumps
from os import path
import PyTango
from PyTango import AttrQuality


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
            'AttrPLC': self.specials,
            'AttrEnumeration': self.enumerations,
        })
        self._attrs = {}

    @property
    def attrs(self):
        return self._attrs

    def process(self, name, T=None,
                read_addr=None, read_bit=None,
                write_addr=None, write_bit=None,
                logic=None, meanings=None,
                autoStop=None, attrGroup=None,
                *args, **kwargs):
        # # label=None, desc=None, qualities=None,
        #         minValue=None, maxValue=None, unit=None, format=None,
        #         readback=None, setpoint=None, switch=None,
        #         memorized=False, logLevel=None, xdim=0,
        #         historyBuffer=None, IamChecker=None, events=None,
        #         *args, **kwargs):
        # print("unused: args: %s, kwargs: %s" % (str(args), str(kwargs)))
        self._attrs[name] = Descriptor(name)
        if T in [PyTango.DevFloat, PyTango.DevDouble]:
            self._attrs[name].type = 'float'
            if read_addr is not None:
                self._attrs[name].plc = True
            if write_addr is not None:
                self._attrs[name].writable = True
        elif T in [PyTango.DevShort, PyTango.DevUChar] or \
                read_bit is not None or logic is not None:
            self._attrs[name].type = 'int'
            if read_addr is not None:
                self._attrs[name].plc = True
            if write_addr is not None:
                self._attrs[name].writable = True
        elif T in [PyTango.DevBoolean]:
            self._attrs[name].type = 'bool'
            if read_addr is not None and read_bit is not None:
                self._attrs[name].plc = True
            if write_addr is not None:
                self._attrs[name].writable = True
        if attrGroup is not None:
            self._attrs[name].type = 'bool'
            self._attrs[name].writable = True
            self._attrs[name].group = attrGroup
        if meanings is not None:
            if name.endswith('_ST'):
                statusName = name.replace('_ST', '_Status')
            else:
                statusName = "%s_Status" % (name)
            self._attrs[statusName] = Descriptor(statusName, type='str')
        if autoStop is not None:
            groupName = "%s_%s" % (name, AUTOSTOP)
            self._attrs[groupName] = Descriptor(groupName,
                                                specialCheck='noException')

            enableName = "%s_Enable" % (groupName)
            self._attrs[enableName] = Descriptor(enableName, type='bool',
                                                 writable=True)
            for condition in [BELOW, ABOVE]:
                if condition in autoStop:
                    conditionName = "%s_%s_Threshold" % (groupName, condition)
                    self._attrs[conditionName] = Descriptor(conditionName,
                                                            type='float',
                                                            writable=True)
            integrTimeName = "%s_IntegrationTime" % (groupName)
            self._attrs[integrTimeName] = Descriptor(integrTimeName,
                                                     type='float',
                                                     writable=True)
            for floatNames in ['Mean', 'Std']:
                attrName = "%s_%s" % (groupName, floatNames)
                self._attrs[attrName] = Descriptor(attrName, type='float')
            triggeredName = "%s_Triggered" % (groupName)
            self._attrs[triggeredName] = Descriptor(triggeredName, type='bool')

    def specials(self, heart, lockst, read_lockingAddr, read_lockingBit,
                 write_lockingAddr, write_lockingBit):
        for attrName, attrType, writable in \
                [['HeartBeat', 'bool', False],
                 ['Lock_ST', 'int', False],
                 ['Lock_Status', 'str', False],
                 ['Locking', 'bool', True]]:
            self._attrs[attrName] = Descriptor(attrName, type=attrType,
                                               writable=writable)

    def groups(self, name, attrGroup, *args, **kwargs):

        pass

    def enumerations(self, name, prefix=None):
        if prefix is not None:
            fullname = "%s_%s" % (prefix, name)
        else:
            fullname = name
        self._attrs[fullname] = Descriptor(name, enumeration=True)

    def ignore(self, *args, **kwargs):
        pass  # TODO: not yet implemented how to test those attributes

    def parse_file(self, fname):
        try:
            fullname = "%s/%s" % (path.dirname(path.abspath(__file__)), fname)
            execfile(fullname, self.globals_, self.locals_)
        except Exception as e:
            print("ERROR: %s" % e)


if __name__ == '__main__':
    attrs = {}
    for number in [1, 2, 3]:
        obj = ParseFile()
        obj.parse_file('../plc%d.py' % number)
        attrs[number] = obj.attrs
    obj = ParseFile()
    obj.parse_file('../plck.py')
    attrs[5] = attrs[4] = obj.attrs
    print(dumps(attrs, indent=True))
