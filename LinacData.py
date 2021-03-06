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
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

"""Device Server to control the Alba's Linac manufactured by Thales."""

__all__ = ["LinacData", "LinacDataClass", "main"]

__docformat__ = 'restructuredtext'

import PyTango
from PyTango import AttrQuality
import sys
# Add additional import
# PROTECTED REGION ID(LinacData.additionnal_import) ---
from copy import copy
from ctypes import c_uint16, c_uint8, c_float, c_int16
import fcntl
import json  # FIXME: temporal to dump dictionary on the relations collection
from numpy import uint16, uint8, float32, int16
import pprint
import psutil
import Queue
import socket
import struct
import time
import tcpblock
import threading
import traceback
from types import StringType


from constants import *
from LinacAttrs import (LinacException, CommandExc, AttrExc,
                        binaryByte, hex_dump)
from LinacAttrs import (EnumerationAttr, PLCAttr, InternalAttr, MeaningAttr,
                        AutoStopAttr, AutoStopParameter, HistoryAttr,
                        GroupAttr, LogicAttr)
from LinacAttrs.LinacFeatures import CircularBuffer, HistoryBuffer, EventCtr


class release:
    author = 'Lothar Krause &'\
             ' Sergi Blanch-Torne <sblanch@cells.es>'
    hexversion = (((MAJOR_VERSION << 8) | MINOR_VERSION) << 8) | BUILD_VERSION
    __str__ = lambda self: hex(hexversion)


if False:
    TYPE_MAP = {PyTango.DevUChar: c_uint8,
                PyTango.DevShort: c_int16,
                PyTango.DevFloat: c_float,
                PyTango.DevDouble: c_float,
                }
else:
    TYPE_MAP = {PyTango.DevUChar: ('B', 1),
                PyTango.DevShort: ('h', 2),
                PyTango.DevFloat: ('f', 4),
                PyTango.DevDouble: ('f', 4),
                # the PLCs only use floats of 4 bytes
                }


def john(sls):
    '''used to encode the messages shown for each state code
    '''
    if type(sls) == dict:
        return '\n'+''.join('%d:%s\n' % (t, sls[t]) for t in sls.keys())
    else:
        return '\n'+''.join('%d:%s\n' % t for t in enumerate(sls))


def latin1(x):
    return x.decode('utf-8').replace(u'\u2070', u'\u00b0').\
        replace(u'\u03bc', u'\u00b5').encode('latin1')


class AttrList(object):
    '''Manages dynamic attributes and contains methods for conveniently adding
       attributes to a running TANGO device.
    '''
    def __init__(self, device):
        super(AttrList, self).__init__()
        self.impl = device
        self._db20_size = self.impl.ReadSize-self.impl.WriteSize
        self._db22_size = self.impl.WriteSize
        self.alist = list()
        self.locals_ = {}
        self._relations = {}
        self._buider = None
        self._fileParsed = threading.Event()
        self._fileParsed.clear()

        self.globals_ = globals()
        self.globals_.update({
            'DEVICE': self.impl,
            'LIST': self,
            'Attr': self.add_AttrAddr,
            'AttrAddr': self.add_AttrAddr,
            'AttrBit': self.add_AttrAddrBit,
            'GrpBit': self.add_AttrGrpBit,
            'AttrLogic': self.add_AttrLogic,
            'AttrRampeable': self.add_AttrRampeable,
            #'AttrLock_ST': self.add_AttrLock_ST,
            #'AttrLocking': self.add_AttrLocking,
            #'AttrHeartBeat': self.add_AttrHeartBeat,
            'AttrPLC': self.add_AttrPLC,
            'AttrEnumeration': self.add_AttrEnumeration,
            # 'john' : john,
        })

    def add_Attr(self, name, T, rfun=None, wfun=None, label=None, desc=None,
                 minValue=None, maxValue=None, unit=None, format=None,
                 memorized=False, logLevel=None, xdim=0):
        if wfun:
            if xdim == 0:
                attr = PyTango.Attr(name, T, PyTango.READ_WRITE)
            else:
                self.impl.error_stream("Not supported write attribute in "
                                       "SPECTRUMs. %s will be readonly."
                                       % (name))
                attr = PyTango.SpectrumAttr(name, T, PyTango.READ_WRITE, xdim)
        else:
            if xdim == 0:
                attr = PyTango.Attr(name, T, PyTango.READ)
            else:
                attr = PyTango.SpectrumAttr(name, T, PyTango.READ, xdim)
        if logLevel is not None:
            self.impl._getAttrStruct(name).logLevel = logLevel
        aprop = PyTango.UserDefaultAttrProp()
        if unit is not None:
            aprop.set_unit(latin1(unit))
        if minValue is not None:
            aprop.set_min_value(str(minValue))
        if maxValue is not None:
            aprop.set_max_value(str(maxValue))
        if format is not None:
            attrStruct = self.impl._getAttrStruct(name)
            attrStruct['format'] = str(format)
            aprop.set_format(latin1(format))
        if desc is not None:
            aprop.set_description(latin1(desc))
        if label is not None:
            aprop.set_label(latin1(label))
        if memorized:
            attr.set_memorized()
            attr.set_memorized_init(True)
            self.impl.info_stream("Making %s memorized (%s,%s)"
                                  % (name, attr.get_memorized(),
                                     attr.get_memorized_init()))
        attr.set_default_properties(aprop)

        rfun = AttrExc(rfun)
        try:
            if wfun:
                wfun = AttrExc(wfun)
        except Exception as e:
            self.impl.error_stream("Attribute %s build exception: %s"
                                   % (name, e))

        self.impl.add_attribute(attr, r_meth=rfun, w_meth=wfun)
        if name in self.impl._plcAttrs and \
                EVENTS in self.impl._plcAttrs[name]:
            self.impl.set_change_event(name, True, False)
        elif name in self.impl._internalAttrs and \
                EVENTS in self.impl._internalAttrs[name]:
            self.impl.set_change_event(name, True, False)
        self.alist.append(attr)
        return attr

    def __mapTypes(self, attrType):
        # ugly hack needed for SOLEILs archiving system
        if attrType == PyTango.DevFloat:
            return PyTango.DevDouble
        elif attrType == PyTango.DevUChar:
            return PyTango.DevShort
        else:
            return attrType

    def add_AttrAddr(self, name, T, read_addr=None, write_addr=None,
                     meanings=None, qualities=None, events=None,
                     formula=None, label=None, desc=None,
                     readback=None, setpoint=None, switch=None,
                     IamChecker=None, minValue=None, maxValue=None,
                     *args, **kwargs):
        '''This method is a most general builder of dynamic attributes, for RO
           as well as for RW depending on if it's provided a write address.
           There are other optional parameters to configure some special
           characteristics.

           With the meaning parameter, a secondary attribute to the give one
           using the name is created (with the suffix *_Status and They share
           other parameters like qualities and events). The numerical attribute
           can be used in formulas, alarms and any other machine-like system,
           but this secondary attribute is an DevString who concatenates the
           read value with an string specified in a dictionary in side this
           meaning parameter in order to provide a human-readable message to
           understand that value.

           All the Tango attributes have characteristics known as qualities
           (like others like format, units, and so on) used to provide a 5
           level state-like information. They can by 'invalid', 'valid',
           'changing', 'warning' or 'alarm'. With the dictionary provided to
           the parameter qualities it can be defined some ranges or some
           discrete values. The structure splits between this two situations:
           - Continuous ranges: that is mainly used for DevDoubles but also
             integers. As an example of the dictionary:
             - WARNING:{ABSOLUTE:{BELOW:15,ABOVE:80}}
               This will show VALID quality between 15 and 80, but warning
               if in absolute terms the read value goes out this thresholds.
           - Discrete values: that is used mainly in the state-like attributes
             and it will establish the quality by an equality. As example:
             - ALARM:[0],
               WARNING:[1,2,3,5,6,7],
               CHANGING:[4]
               Suppose a discrete attribute with values between 0 and 8. Then
               when value is 8 will be VALID, between 0 and 7 will be WARNING
               with the exception at 4 that will show CHANGING.

           Next of the parameters is events and with this is configured the
           behaviour of the attribute to emit events. Simply by passing a
           dictionary (even void like {}) the attribute will be configured to
           emit events. In this simplest case events will be emitted if the
           value has changed from last reading. But for DevDouble is used a
           key THRESHOLD to indicate that read changes below it will not
           produce events (like below the format representation). For such
           thing is used a circular buffer that collects reads and its mean
           is used to compare with a new reading to decide if an event has to
           be emitted or not.

           Another parameter is the formula. This is mainly used with the
           DevBooleans but it's possible for any other. It's again a dictionary
           with two possible keys 'read' and/or 'write' and their items shall
           be assessed strings in running time that would 'transform' a
           reading.

           The set of arguments about readback, setpoint and switch are there
           to store defined relations between attributes. That is, to allow the
           setpoint (that has a read and write addresses) to know if there is
           another read only attribute that does the measure of what the
           setpoint sets. Also this readback may like to know about the
           setpoint and if the element is switch on or off.

           In the attribute description, one key argument (default None) is:
           'IamChecker'. It is made to, if it contains a list of valid read
           values, add to the tcpblock reader to decide if a received block
           has a valid structure or not.
        '''
        self.__traceAttrAddr(name, T, readAddr=read_addr, writeAddr=write_addr)
        tango_T = self.__mapTypes(T)
        try:
            read_addr = self.__check_addresses_and_block_sizes(
                name, read_addr, write_addr)
        except IndexError:
            return
        self._prepareAttribute(name, T, readAddr=read_addr,
                               writeAddr=write_addr, formula=formula,
                               readback=readback, setpoint=setpoint,
                               switch=switch, label=label, description=desc,
                               minValue=minValue, maxValue=maxValue,
                               *args, **kwargs)
        rfun = self.__getAttrMethod('read', name)

        if write_addr is not None:
            wfun = self.__getAttrMethod('write', name)
        else:
            wfun = None
        # TODO: they are not necessary right now
        #if readback is not None:
        #    self.append2relations(name, READBACK, readback)
        #if setpoint is not None:
        #    self.append2relations(name, SETPOINT, setpoint)
        #if switch is not None:
        #    self.append2relations(name, SWITCH, switch)
        self._prepareEvents(name, events)
        if IamChecker is not None:
            try:
                self.impl.setChecker(read_addr, IamChecker)
            except Exception as e:
                self.impl.error_stream("%s cannot be added in the checker set "
                                       "due to:\n%s" % (name, e))
        if meanings is not None:
            return self._prepareAttrWithMeaning(name, tango_T, meanings,
                                                qualities, rfun, wfun,
                                                **kwargs)
        elif qualities is not None:
            return self._prepareAttrWithQualities(name, tango_T, qualities,
                                                  rfun, wfun, label=label,
                                                  **kwargs)
        else:
            return self.add_Attr(name, tango_T, rfun, wfun, minValue=minValue,
                                 maxValue=maxValue, **kwargs)

    def add_AttrAddrBit(self, name, read_addr=None, read_bit=0,
                        write_addr=None, write_bit=None, meanings=None,
                        qualities=None, events=None, isRst=False,
                        activeRst_t=None, formula=None, switchDescriptor=None,
                        readback=None, setpoint=None, logLevel=None,
                        label=None, desc=None, minValue=None, maxValue=None,
                        *args, **kwargs):
        '''This method is a builder of a boolean dynamic attribute, even for RO
           than for RW. There are many optional parameters.

           With the meanings argument, moreover the DevBoolean a DevString
           attribute will be also generated (suffixed *_Status) with the same
           event and qualities configuration if they are, and will have a
           human readable message from the concatenation of the value and its
           meaning.

           There are also boolean attributes with a reset feature, those are
           attributes that can be triggered and after some short period of time
           they are automatically set back. The time with this reset active
           can be generic (and uses ACTIVE_RESET_T from the constants) or can
           be specified for a particular attribute using the activeRst_t.

           Another feature implemented for this type of attributes is the
           formula. That requires a dictionary with keys:
           + 'read' | 'write': they contain an string to be evaluated when
             value changes like a filter or to avoid an action based on some
             condition.
           For example, this is used to avoid to power up klystrons if there
           is an interlock, or to switch of the led when an interlock occurs.
           {'read':'VALUE and '\
                   'self._plcAttrs[\'HVPS_ST\'][\'read_value\'] == 9 and '\
                   'self._plcAttrs[\'Pulse_ST\'][\'read_value\'] == 8',
            'write':'VALUE and '\
                   'self._plcAttrs[\'HVPS_ST\'][\'read_value\'] == 8 and '\
                   'self._plcAttrs[\'Pulse_ST\'][\'read_value\'] == 7'
            },

           The latest feature implemented has relation with the rampeable
           attributes and this is a secondary configuration for the
           AttrRampeable DevDouble attributes, but in this case the feature
           to complain is to manage ramping on the booleans that power on and
           off those elements.
           The ramp itself shall be defined in the DevDouble attribute, the
           switch attribute only needs to know where to send this when state
           changes.
           The switchDescriptor is a dictionary with keys:
           + ATTR2RAMP: the name of the numerical attribute involved with the
             state transition.
           + WHENON | WHENOFF: keys to differentiate action interval between
             the two possible state changes.
             - FROM: initial value of the state change ramp
             - TO: final value of the state change ramp
             About those two last keys, they can be both or only one.
           + AUTOSTOP: in case it has also the autostop feature, this is used
             to identify the buffer to clean when transition from off to on.

           The set of arguments about readback, setpoint and switch are there
           to store defined relations between attributes. That is, to allow the
           setpoint (that has a read and write addresses) to know if there is
           another read only attribute that does the measure of what the
           setpoint sets. Also this readback may like to know about the
           setpoint and if the element is switch on or off.
        '''
        self.__traceAttrAddr(name, PyTango.DevBoolean, readAddr=read_addr,
                             readBit=read_bit, writeAddr=write_addr,
                             writeBit=write_bit)
        try:
            read_addr = self.__check_addresses_and_block_sizes(
                name, read_addr, write_addr)
        except IndexError:
            return
        self._prepareAttribute(name, PyTango.DevBoolean, readAddr=read_addr,
                               readBit=read_bit, writeAddr=write_addr,
                               writeBit=write_bit, formula=formula,
                               readback=readback, setpoint=setpoint, 
                               label=label, description=desc,
                               minValue=minValue, maxValue=maxValue,
                               *args, **kwargs)
        rfun = self.__getAttrMethod('read', name, isBit=True)

        if write_addr is not None:
            wfun = self.__getAttrMethod('write', name, isBit=True)
            if write_bit is None:
                write_bit = read_bit
        else:
            wfun = None
        if isRst:
            self.impl._plcAttrs[name][ISRESET] = True
            self.impl._plcAttrs[name][RESETTIME] = None
            if activeRst_t is not None:
                self.impl._plcAttrs[name][RESETACTIVE] = activeRst_t
        if type(switchDescriptor) == dict:
            self.impl._plcAttrs[name][SWITCHDESCRIPTOR] = switchDescriptor
            self.impl._plcAttrs[name][SWITCHDEST] = None
            # in the construction of the AutoStopAttr() the current switch
            # may not be build yet. Then now they must be linked together.
            if AUTOSTOP in switchDescriptor:
                autostopAttrName = switchDescriptor[AUTOSTOP]
                if autostopAttrName in self.impl._internalAttrs:
                    autostopper = self.impl._internalAttrs[autostopAttrName]
                    if autostopper.switch == name:
                        autostopper.setSwitchAttr(self.impl._plcAttrs[name])
        self._prepareEvents(name, events)
        if logLevel is not None:
            self.impl._getAttrStruct(name).logLevel = logLevel
        if meanings is not None:
            return self._prepareAttrWithMeaning(name, PyTango.DevBoolean,
                                                meanings, qualities, rfun,
                                                wfun, historyBuffer=None,
                                                **kwargs)
        else:
            return self.add_Attr(name, PyTango.DevBoolean, rfun, wfun,
                                 minValue=minValue, maxValue=maxValue,
                                 **kwargs)

    def add_AttrGrpBit(self, name, attrGroup=None, meanings=None, qualities=None,
                       events=None, **kwargs):
        '''An special type of attribute where, given a set of bits by the pair
           [reg,bit] this attribute can operate all of them as one.
           That is, the read value is True if _all_ are true.
                    the write value, is applied to _all_ of them
                    (almost) at the same time.
        '''
        self.__traceAttrAddr(name, PyTango.DevBoolean, internal=True)
        attrObj = GroupAttr(name=name, device=self.impl, group=attrGroup)
        self.impl._internalAttrs[name] = attrObj
        rfun = attrObj.read_attr
        wfun = attrObj.write_attr
        toReturn = [self.add_Attr(name, PyTango.DevBoolean, rfun, wfun,
                                  **kwargs)]
        if qualities is not None:
            attrObj.qualities = qualities
        if meanings is not None:
            meaningAttr = self._buildMeaningAttr(attrObj, meanings, rfun,
                                                 **kwargs)
            toReturn.append(meaningAttr)
        self._prepareEvents(name, events)
        return tuple(toReturn)

    def add_AttrLogic(self, name, logic, label, desc, events=None,
                      operator='and', inverted=False, **kwargs):
        '''Internal type of attribute made to evaluate a logical formula with
           other attributes owned by the device with a boolean result.
        '''
        self.__traceAttrAddr(name, PyTango.DevBoolean, internalRO=True)
        self.impl.debug_stream("%s logic: %s" % (name, logic))
        # self._prepareInternalAttribute(name, PyTango.DevBoolean, logic=logic,
        #                                operator=operator, inverted=inverted)
        attrObj = LogicAttr(name=name, device=self.impl,
                            valueType=PyTango.DevBoolean,logic=logic,
                            operator=operator, inverted=inverted)
        self.impl._internalAttrs[name] = attrObj
        rfun = self.__getAttrMethod('read', name, isLogical=True)
        wfun = None  # this kind can only be ReadOnly
        for key in logic:
            self.append2relations(name, LOGIC, key)
        self._prepareEvents(name, events)
        return self.add_Attr(name, PyTango.DevBoolean, rfun, wfun, label, **kwargs)

    def add_AttrRampeable(self, name, T, read_addr, write_addr, label, unit,
                          rampsDescriptor, events=None, qualities=None,
                          readback=None, switch=None, desc=None, minValue=None,
                          maxValue=None, *args, **kwargs):
        '''Given 2 plc memory positions (for read and write), with this method
           build a RW attribute that looks like the other RWs but it includes
           ramping features.
           - rampsDescriptor is a dictionary with two main keys:
             + ASCENDING | DESCENDING: Each of these keys contain a
               dictionary in side describing the behaviour of the ramp
               ('+' mandatory keys, '-' optional keys):
               + STEP: value added/subtracted on each step.
               + STEPTIME: seconds until next step.
               - THRESHOLD: initial value from where start ramping.
               - SWITCH: attribute to monitor if it has switched off
           Those keys will generate attributes called '$name_$key' as memorised
           to allow the user to adapt the behaviour depending on configuration.

           About the threshold, it's a request from the user to have, it
           klystronHV, to not apply the ramp between 0 to N and after, if it's
           above, ramp it to the setpoint. Also the request of the user is to
           only do this ramp in the increasing way and decrease goes direct.
           Example:
           - rampsDescriptor = {ASCENDING:
                                   {STEP:0.5,#kV
                                    STEPTIME:1,#s
                                    THRESHOLD:20,#kV
                                    SWITCH:'HVPS_ONC'
                                   }}

           Another request for the Filament voltage is a descending ramp in
           similar characteristics than klystrons, but also: once commanded a
           power off, delay it doing a ramps to 0. This second request will
           be managed from the boolean that does this on/off transition using
           AttrAddrBit() builder together with a switchDescriptor dictionary.
           Example:
           - rampsDescriptor = {DESCENDING:
                                   {STEP:1,#kV
                                    STEPTIME:1,#s
                                    THRESHOLD:-50,#kV
                                    SWITCH:'GUN_HV_ONC'
                                   },
                                ASCENDING:
                                   {STEP:5,#kV
                                    STEPTIME:0.5,#s
                                    THRESHOLD:-90,#kV
                                    SWITCH:'GUN_HV_ONC'
                                   }}
           The set of arguments about readback, setpoint and switch are there
           to store defined relations between attributes. That is, to allow the
           setpoint (that has a read and write addresses) to know if there is
           another read only attribute that does the measure of what the
           setpoint sets. Also this readback may like to know about the
           setpoint and if the element is switch on or off.
        '''
        self.__traceAttrAddr(name, T, readAddr=read_addr, writeAddr=write_addr)
        tango_T = self.__mapTypes(T)
        self._prepareAttribute(name, T, readAddr=read_addr,
                               writeAddr=write_addr, readback=readback,
                               switch=switch, label=label, description=desc,
                               minValue=minValue, maxValue=maxValue,
                               *args, **kwargs)
        rfun = self.__getAttrMethod('read', name)
        wfun = self.__getAttrMethod('write', name, rampeable=True)
        self._prepareEvents(name, events)
        if qualities is not None:
            rampeableAttr = self._prepareAttrWithQualities(name, tango_T,
                                                           qualities, rfun,
                                                           wfun, label=label,
                                                           **kwargs)
        else:
            rampeableAttr = self.add_Attr(name, tango_T, rfun, wfun, label,
                                          minValue=minValue, maxValue=maxValue,
                                          **kwargs)
        # until here, it's not different than another attribute
        # Next is specific for rampeable attributes
        rampAttributes = []
        # FIXME: temporally disabled all the ramps
        # TODO: review if the callback functionality can be usefull here
#         self.impl._plcAttrs[name][RAMP] = rampsDescriptor
#         self.impl._plcAttrs[name][RAMPDEST] = None
#         for rampDirection in rampsDescriptor.keys():
#             if not rampDirection in [ASCENDING,DESCENDING]:
#                 self.impl.error_stream("In attribute %s, the ramp direction "
#                                        "%s has been not recognised."
#                                        %(name,rampDirection))
#             else:
#                 rampAttributes = []
#                 newAttr = self._buildInternalAttr4RampEnable(name,name)
#                 if newAttr != None:
#                     rampAttributes.append(newAttr)
#                 for subAttrName in rampsDescriptor[rampDirection].keys():
#                     if subAttrName in [STEP,STEPTIME,THRESHOLD]:
#                         if subAttrName == STEPTIME:
#                             subAttrUnit = 'seconds'
#                         else:
#                             subAttrUnit = unit
#                         defaultValue = rampsDescriptor[rampDirection]\
#                             [subAttrName]
#                         newAttr = self._buildInternalAttr4Ramping(\
#                             name+'_'+rampDirection, subAttrName,
#                             name+" "+rampDirection, subAttrUnit,
#                             defaultValue)
#                         if newAttr is not None:
#                             rampAttributes.append(newAttr)
        rampAttributes.insert(0, rampeableAttr)
        return tuple(rampAttributes)

    def add_AttrPLC(self, heart, lockst, read_lockingAddr, read_lockingBit,
                    write_lockingAddr, write_lockingBit):
        heartbeat = self.add_AttrHeartBeat(heart)
        lockState, lockStatus = self.add_AttrLock_ST(lockst)
        locking = self.add_AttrLocking(read_lockingAddr, read_lockingBit,
                                       write_lockingAddr, write_lockingBit)
        return (heartbeat, lockState, lockStatus, locking)

    def add_AttrLock_ST(self, read_addr):
        COMM_STATUS = {0: 'unlocked', 1: 'local', 2: 'remote'}
        COMM_QUALITIES = {ALARM: [0], WARNING: [2]}
        plc_name = self.impl.get_name().split('/')[-1]
        desc = 'lock status %s' % plc_name
        # This attr was a number but for the user what shows the ----
        # information is an string
        self.impl.lock_ST = read_addr
        self.impl.setChecker(self.impl.lock_ST, ['\x00', '\x01', '\x02'])
        LockAttrs = self.add_AttrAddr('Lock_ST', PyTango.DevUChar, read_addr,
                                      label=desc, desc=desc+john(COMM_STATUS),
                                      meanings=COMM_STATUS,
                                      qualities=COMM_QUALITIES, events={})
        # This UChar is to know what to read from the plc, the AttrAddr,
        # because it has an enumerate, will set this attr as string
        self.impl.set_change_event('Lock_ST', True, False)
        self.impl.set_change_event('Lock_Status', True, False)
        return LockAttrs

    def add_AttrLocking(self, read_addr, read_bit, write_addr, write_bit):
        desc = 'True when attempting to obtain write lock'
        new_attr = self.add_AttrAddrBit('Locking', read_addr, read_bit,
                                        write_addr, write_bit, desc=desc,
                                        events={})
        locking_attr = self.impl.get_device_attr().get_attr_by_name('Locking')
        self.impl.Locking = locking_attr
        locking_attr.set_write_value(False)
        self.impl.locking_raddr = read_addr
        self.impl.locking_rbit = read_bit
        # TODO: adding this checker, it works worst
        # if hasattr(self.impl,'read_db') and self.impl.read_db si not None:
        #    self.impl.setChecker(self.impl.locking_raddr, ['\x00', '\x01'])
        self.impl.locking_waddr = write_addr
        self.impl.locking_wbit = write_bit
        # TODO: adding this checker, it works worst
        # if hasattr(self.impl,'read_db') and self.impl.read_db is not None:
        #    self.impl.setChecker(self.impl.locking_waddr, ['\x00','\x01'])
        self.impl.set_change_event('Locking', True, False)
        return new_attr

    def add_AttrHeartBeat(self, read_addr, read_bit=0):
        self.impl.heartbeat_addr = read_addr
        desc = 'cadence bit going from True to False when PLC is okay'
        attr = self.add_AttrAddrBit('HeartBeat', read_addr, read_bit,
                                    desc=desc, events={})
        self.impl.set_change_event('HeartBeat', True, False)
        return attr

    def add_AttrEnumeration(self, name, prefix=None, suffixes=None,
                            *args, **kwargs):
        self.impl.info_stream("Building a Enumeration attribute set for %s"
                              % name)
        if prefix is not None:
            # With the klystrons user likes to see the number in the label,
            # we don't want in the attribute name because it will make
            # different between those two equal devices.
            try:
                plcN = int(self.impl.get_name().split('plc')[-1])
            except:
                plcN = 0
            if plcN in [4, 5]:
                label = "%s%d_%s" % (prefix, plcN-3, name)
                name = "%s_%s" % (prefix, name)
            else:
                label = "%s_%s" % (prefix, name)
                name = "%s_%s" % (prefix, name)
            # FIXME: but this is something "ad hoc"
        else:
            label = "%s" % (name)
        if suffixes is None:
            suffixes = {'options': [PyTango.DevString, 'read_write'],
                        'active': [PyTango.DevString, 'read_write'],
                        'numeric': [PyTango.DevUShort, 'read_only'],
                        'meaning': [PyTango.DevString, 'read_only']}
        attrs = []
        try:
            enumObj = EnumerationAttr(name, valueType=None)
            for suffix in suffixes.keys():
                try:
                    attrType = suffixes[suffix][0]
                    rfun = enumObj.read_attr
                    if suffixes[suffix][1] == 'read_write':
                        wfun = enumObj.write_attr
                    else:
                        wfun = None
                    attr = self.add_Attr(name+'_'+suffix, attrType,
                                         label="%s %s" % (label, suffix),
                                         rfun=rfun, wfun=wfun, **kwargs)
                    # FIXME: setup events in the self.add_Attr(...)
                    self.impl.set_change_event(name+'_'+suffix, True, False)
                    attrs.append(attr)
                except Exception as e:
                    self.impl.debug_stream("In %s enumeration, exception "
                                           "with %s: %s" % (name, suffix, e))
            self.impl._internalAttrs[name] = enumObj
            enumObj.device = self.impl
        except Exception as e:
            self.impl.error_stream("Fatal exception building %s: %s"
                                   % (name, e))
            traceback.print_exc()
        # No need to configure device memorised attributes because the
        # _LinacAttr subclasses already have this feature nested in the
        # implementation.
        return tuple(attrs)

    def remove_all(self):
        for attr in self.alist:
            try:
                self.impl.remove_attribute(attr.get_name())
            except ValueError as exc:
                self.impl.debug_stream(attr.get_name()+': '+str(exc))

    def build(self, fname):
        if self._buider is not None:
            if not isinstance(self._buider, threading.Thread):
                msg = "AttrList builder is not a Thread! (%s)" \
                      % (type(self._buider))
                self.impl.error_stream("Ups! This should never happen: %s"
                                       % (msg))
                raise AssertionError(msg)
            elif self._buider.isAlive():
                msg = "AttrList build while it is building"
                self.impl.error_stream("Ups! This should never happen: %s"
                                       % (msg))
                return
            else:
                self._buider = None
        self._buider = threading.Thread(name="FileParser",
                                        target=self.parse_file, args=(fname,))
        self.impl.info_stream("Launch a thread to build the dynamic attrs")
        self._buider.start()

    def parse_file(self,  fname):
        t0 = time.time()
        self._fileParsed.clear()
        msg = "%30s\t%10s\t%5s\t%6s\t%6s"\
            % ("'attrName'", "'Type'", "'RO/RW'", "'read'", "'write'")
        self.impl.info_stream(msg)
        try:
            execfile(fname, self.globals_, self.locals_)
        except IOError as io:
            self.impl.error_stream("AttrList.parse_file IOError: %s\n%s"
                                   % (e, traceback.format_exc()))
            raise LinacException(io)
        except Exception as e:
            self.impl.error_stream("AttrList.parse_file Exception: %s\n%s"
                                   % (e, traceback.format_exc()))
        self.impl.debug_stream('Parse attrFile done.')
        # Here, I can be sure that all the objects are build,
        # then any none existing object reports a configuration
        # mistake in the parsed file.
        for origName in self._relations:
            try:
                origObj = self.impl._getAttrStruct(origName)
                for tag in self._relations[origName]:
                    for destName in self._relations[origName][tag]:
                        try:
                            destObj = self.impl._getAttrStruct(destName)
                            origObj.addReportTo(destObj)
                            self.impl.debug_stream("Linking %s with %s (%s)"
                                                  % (origName, destName, tag))
                            origObj.reporter.report()
                        except Exception as e:
                            self.impl.error_stream("Exception managing the "
                                                   "relation between %s and "
                                                   "%s: %s" % (origName,
                                                               destName, e))
            except Exception as e:
                self.impl.error_stream("Exception managing %s relations: %s"
                                       % (origName, e))
                traceback.print_exc()
        self.impl.applyCheckers()
        self._fileParsed.set()
        tf = time.time()
        self.impl.info_stream("file parsed in %6.3f seconds" % (tf-t0))

    def parse(self, text):
        exec text in self.globals_, self.locals_

    # # internal auxiliar methods ---

    def __getAttrMethod(self, operation, attrName, isBit=False,
                        rampeable=False, internal=False, isGroup=False,
                        isLogical=False):
        # if exist an specific method
        attrStruct = self.impl._getAttrStruct(attrName)
        return getattr(attrStruct, "%s_attr" % (operation))
#         if hasattr(self.impl, "%s_%s" % (operation, attrName)):
#             return getattr(self.impl, "%s_%s" % (operation, attrName))
#         # or use the generic method for its type
#         elif isBit:
#             return getattr(self.impl, "%s_attr_bit" % (operation))
#         elif operation == 'write' and rampeable:
#             # no sense with read operation
#             # FIXME: temporally disabled all the ramps
#             # return getattr(self.impl,"write_attr_with_ramp")
#             return getattr(self.impl, "write_attr")
#         elif isGroup:
#             return getattr(self.impl, '%s_attrGrpBit' % (operation))
#         elif internal:
#             return getattr(self.impl, "%s_internal_attr" % (operation))
#         elif isLogical:
#             return getattr(self.impl, "%s_logical_attr" % (operation))
#         else:
#             return getattr(self.impl, "%s_attr" % (operation))

    def __traceAttrAddr(self, attrName, attrType, readAddr=None, readBit=None,
                        writeAddr=None, writeBit=None, internal=False,
                        internalRO=False):
        # first column is the attrName
        msg = "%30s\t" % ("'%s'" % attrName)
        # second, its type
        msg += "%10s\t" % ("'%s'" % attrType)
        # Then, if it's read only or read/write
        if writeAddr is not None or internal:
            msg += "   'RW'\t"
        else:
            msg += "'RO'   \t"
        if readAddr is not None:
            if readBit is not None:
                read = "'%s.%s'" % (readAddr, readBit)
            else:
                read = "'%s'" % (readAddr)
            msg += "%6s\t" % (read)
        if writeAddr is not None:
            if writeBit is not None:
                write = "'%s.%s'" % (writeAddr, writeBit)
            else:
                write = "'%s'" % (writeAddr)
            msg += "%6s\t" % (write)
        self.impl.info_stream(msg)

    # # prepare attribute structures ---

    def _prepareAttribute(self, attrName, attrType, readAddr, readBit=None,
                          writeAddr=None, writeBit=None, formula=None,
                          readback=None, setpoint=None, switch=None,
                          label=None, description=None,
                          minValue=None, maxValue=None, **kwargs):
        '''This is a constructor of the item in the dictionary of attributes
           related with PLC memory locations. At least they have a read address
           and a type. The booleans also needs a read bit. For writable
           attributes there are the equivalents write addresses and booleans
           also the write bit (it doesn't happen with current PLCs, but we
           support them if different).

           Also is introduced the feature of the formula that can distinguish
           between a read formula and write case. Not needing both coexisting.

           The set of arguments about readback, setpoint and switch are there
           to store defined relations between attributes. That is, to allow the
           setpoint (that has a read and write addresses) to know if there is
           another read only attribute that does the measure of what the
           setpoint sets. Also this readback may like to know about the
           setpoint and if the element is switch on or off.
        '''
        if readAddr is None and writeAddr is not None:
            readAddr = self._db20_size + writeAddr
        attrObj = PLCAttr(name=attrName, device=self.impl, valueType=attrType,
                          readAddr=readAddr, readBit=readBit,
                          writeAddr=writeAddr, writeBit=writeBit,
                          formula=formula,
                          readback=readback, setpoint=setpoint, switch=switch,
                          label=label, description=description,
                          minValue=minValue, maxValue=maxValue)
        self.impl._plcAttrs[attrName] = attrObj
        self._insert2reverseDictionary(attrName, attrType, readAddr, readBit,
                                       writeAddr, writeBit)
        # if readBit is not None:
        #     if readAddr not in self.impl._addrDct:
        #         self.impl._addrDct[readAddr] = {}
        #     self.impl._addrDct[readAddr][readBit] = []
        #     self.impl._addrDct[readAddr][readBit].append(attrName)
        #     if writeAddr is not None:
        #         self.impl._addrDct[readAddr][readBit].append(writeAddr)
        #         if writeBit is not None:
        #             self.impl._addrDct[readAddr][readBit].append(writeBit)
        #         else:
        #             self.impl._addrDct[readAddr][readBit].append(readBit)
        # else:
        #     if readAddr not in self.impl._addrDct:
        #         self.impl._addrDct[readAddr] = []
        #         self.impl._addrDct[readAddr].append(attrName)
        #         self.impl._addrDct[readAddr].append(attrType)
        #         if writeAddr is not None:
        #             self.impl._addrDct[readAddr].append(writeAddr)
        #     else:
        #         self.impl.error_stream("The address %s has been found in the "
        #                                "reverse dictionary" % (readAddr))

    def _insert2reverseDictionary(self, name, valueType, readAddr, readBit,
                                  writeAddr, writeBit):
        '''
        Hackish for the dump of a valid write block when the PLC provides
        invalid values in the write datablock

        :param name:
        :param valueType:
        :param readAddr:
        :param readBit:
        :param writeAddr:
        :param writeBit:
        :return:
        '''
        dct = self.impl._addrDct
        if 'readBlock' not in dct:
            dct['readBlock'] = {}
        rDct = dct['readBlock']
        if 'writeBlock' not in dct:
            dct['writeBlock'] = {}
        wDct = dct['writeBlock']
        if readBit is not None:  # boolean
            if readAddr not in rDct:
                rDct[readAddr] = {}
            if readBit in rDct[readAddr]:
                self.impl.warn_stream(
                    "{0} override readAddr {1} readBit {2}: {3}"
                    "".format(name, readAddr, readBit,
                              rDct[readAddr][readBit]['name']))
            rDct[readAddr][readBit] = {}
            rDct[readAddr][readBit]['name'] = name
            rDct[readAddr][readBit]['type'] = valueType
            if writeAddr is not None:
                rDct[readAddr][readBit]['writeAddr'] = writeAddr
                if writeBit is None:
                    writeBit = readBit
                rDct[readAddr][readBit]['writeBit'] = writeBit
                if writeAddr not in wDct:
                    wDct[writeAddr] = {}
                wDct[writeAddr][writeBit] = {}
                wDct[writeAddr][writeBit]['name'] = name
                wDct[writeAddr][writeBit]['type'] = valueType
                wDct[writeAddr][writeBit]['readAddr'] = readAddr
                wDct[writeAddr][writeBit]['readBit'] = readBit
        else:  # Byte, Word or Float
            if readAddr in rDct:
                self.impl.warn_stream(
                    "{0} override readAddr {1}: {2}"
                    "".format(name, readAddr, rDct[readAddr]['name']))
            rDct[readAddr] = {}
            rDct[readAddr]['name'] = name
            rDct[readAddr]['type'] = valueType
            if writeAddr is not None:
                rDct[readAddr]['writeAddr'] = writeAddr
                if writeAddr in wDct:
                    self.impl.warn_stream(
                        "{0} override writeAddr {1}:{2}"
                        "".format(name, writeAddr, wDct[writeAddr]['name']))
                wDct[writeAddr] = {}
                wDct[writeAddr]['name'] = name
                wDct[writeAddr]['type'] = valueType
                wDct[writeAddr]['readAddr'] = readAddr

    def _prepareInternalAttribute(self, attrName, attrType, memorized=False,
                                  isWritable=False, defaultValue=None,
                                  logic=None, operator=None, inverted=None):
        attrObj = InternalAttr(name=attrName, device=self.impl,
                               valueType=attrType, memorized=memorized,
                               isWritable=isWritable,
                               defaultValue=defaultValue, logic=logic,
                               operator=operator, inverted=inverted)
        self.impl._internalAttrs[attrName] = attrObj

    def _prepareEvents(self, attrName, eventConfig):
        if eventConfig is not None:
            attrStruct = self.impl._getAttrStruct(attrName)
            attrStruct[EVENTS] = eventConfig
            attrStruct[LASTEVENTQUALITY] = PyTango.AttrQuality.ATTR_VALID
            attrStruct[EVENTTIME] = None

    def _prepareAttrWithMeaning(self, attrName, attrType, meanings, qualities,
                                rfun, wfun, historyBuffer=None, **kwargs):
        '''There are some short integers where the number doesn't mean anything
           by itself. The plcs register description shows a relation between
           the possible numbers and its meaning.
           These attributes are splitted in two:
           - one with only the number (machine readable: archiver,plots)
           - another string with the number and its meaning (human readable)

           The historyBuffer parameter has been developed to introduce
           interlock tracking (using a secondary attribute called *_History).
           That is, starting from a set of non interlock values, when the
           attibute reads something different to them, it starts collecting
           those new values in order to provide a line in the interlock
           activity. Until the interlock is cleaned, read value is again in
           the list of non interlock values and this buffer is cleaned.
        '''
        # first, build the same than has been archived
        attrState = self.add_Attr(attrName, attrType, rfun, wfun, **kwargs)
        # then prepare the human readable attribute as a feature
        attrStruct = self.impl._plcAttrs[attrName]
        attrStruct.qualities = qualities
        attrTuple = self._buildMeaningAttr(attrStruct, meanings, rfun,
                                             **kwargs)
        toReturn = (attrState,)
        toReturn += (attrTuple,)
        return toReturn

    def _buildMeaningAttr(self, attrObj, meanings, rfun, historyBuffer=None,
                          **kwargs):
        if attrObj.name.endswith('_ST'):
            name = attrObj.name.replace('_ST', '_Status')
        else:
            name = "%s_Status" % (attrObj.name)
        attrObj.meanings = meanings
        self.impl._plcAttrs[name] = attrObj._meaningsObj
        self.impl._plcAttrs[name].alias = name
        self.impl._plcAttrs[name].meanings = meanings
        self.impl._plcAttrs[name].qualities = attrObj.qualities
        meaningAttr = self.add_Attr(name, PyTango.DevString, rfun, wfun=None,
                                    **kwargs)
        toReturn = (meaningAttr)
        if historyBuffer is not None:
            attrHistoryName = "%s_History" % (attrStruct._meaningsalias)
            attrStruct.history = historyBuffer
            historyStruct = attrStruct._historyObj
            historyStruct.history = historyBuffer
            historyStruct.alias = attrHistoryName
            attrStruct.read_value = HistoryBuffer(
                cleaners=historyBuffer[BASESET], maxlen=HISTORYLENGTH,
                owner=attrStruct)
            xdim = attrStruct.read_value.maxSize()
            self.impl._plcAttrs[attrHistoryName] = historyStruct
            attrHistory = self.add_Attr(attrHistoryName, PyTango.DevString,
                                        rfun=historyStruct.read_attr,
                                        xdim=xdim, **kwargs)
            toReturn += (attrHistory,)
        return toReturn

    def _prepareAttrWithQualities(self, attrName, attrType, qualities,
                                  rfun, wfun, label=None, unit=None,
                                  autoStop=None, **kwargs):
        '''The attributes with qualities definition, but without meanings for
           their possible values, are specifically build to have a
           CircularBuffer as the read element. That is made to collect a small
           record of the previous values, needed for the RELATIVE condition
           (mainly used with CHANGING quality). Without a bit of memory in the
           past is not possible to know what had happen.

           This kind of attributes have another possible keyword named
           'autoStop'. This has been initially made for the eGun HV
           leakage current, to stop it when this leak is too persistent on
           time (adjustable using an extra attribute). Apart from that, the
           user has a feature disable for it.

           TODO: feature 'too far' from a setpoint value.
        '''
        self.impl._plcAttrs[attrName][READVALUE] = \
            CircularBuffer([], owner=self.impl._plcAttrs[attrName])
        self.impl._plcAttrs[attrName][QUALITIES] = qualities
        toReturn = (self.add_Attr(attrName, attrType, rfun, wfun, label=label,
                                  unit=unit, **kwargs),)
        if autoStop is not None:
            # FIXME: shall it be in the AttrWithQualities? Or more generic?
            toReturn += self._buildAutoStopAttributes(attrName, label,
                                                      attrType, autoStop,
                                                      **kwargs)
        return toReturn

    # # Builders for subattributes ---

    def _buildAutoStopAttributes(self, baseName, baseLabel, attrType,
                                 autoStopDesc, logLevel, **kwargs):
        # TODO: review if the callback between attributes can be usefull here
        attrs = []
        autostopperName = "%s_%s" % (baseName, AUTOSTOP)
        autostopperLabel = "%s %s" % (baseLabel, AUTOSTOP)
        autostopSwitch = autoStopDesc.get(SWITCHDESCRIPTOR, None)
        if autostopSwitch in self.impl._plcAttrs:
            autostopSwitch = self.impl._plcAttrs[autostopSwitch]
            # depending on the build process, the switch object may not be
            # build yet. That's why the name (as string) is stored.
            # Later, when the switch (AttrAddrBit) is build, this assignment
            # will be completed.
        autostopper = AutoStopAttr(name=autostopperName,
                                   valueType=attrType,
                                   device=self.impl,
                                   plcAttr=self.impl._plcAttrs[baseName],
                                   below=autoStopDesc.get(BELOW, None),
                                   above=autoStopDesc.get(ABOVE, None),
                                   switchAttr=autostopSwitch,
                                   integr_t=autoStopDesc.get(INTEGRATIONTIME,
                                                             None),
                                   events={})
        self.impl._internalAttrs[autostopperName] = autostopper
        spectrumAttr = self.add_Attr(autostopperName, PyTango.DevDouble,
                                     rfun=autostopper.read_attr, xdim=1000,
                                     label=autostopperLabel)
        attrs.append(spectrumAttr)
        enableAttr = self._buildAutoStopperAttr(autostopperName,
                                                autostopperLabel, ENABLE,
                                                autostopper._enable,
                                                PyTango.DevBoolean,
                                                memorised=True, writable=True)
        attrs.append(enableAttr)
        for condition in [BELOW, ABOVE]:
            if condition in autoStopDesc:
                condAttr = self._buildAutoStopConditionAttr(condition,
                                                            autostopperName,
                                                            autostopperLabel,
                                                            autostopper)
                attrs.append(condAttr)
        integrAttr = self._buildAutoStopperAttr(autostopperName,
                                                autostopperLabel,
                                                INTEGRATIONTIME,
                                                autostopper._integr_t,
                                                PyTango.DevDouble,
                                                memorised=True, writable=True)
        meanAttr = self._buildAutoStopperAttr(autostopperName,
                                              autostopperLabel, MEAN,
                                              autostopper._mean,
                                              PyTango.DevDouble)
        attrs.append(meanAttr)
        stdAttr = self._buildAutoStopperAttr(autostopperName,
                                             autostopperLabel, STD,
                                             autostopper._std,
                                             PyTango.DevDouble)
        attrs.append(stdAttr)
        triggeredAttr = self._buildAutoStopperAttr(autostopperName,
                                                   autostopperLabel, TRIGGERED,
                                                   autostopper._triggered,
                                                   PyTango.DevBoolean)
        attrs.append(triggeredAttr)
        if logLevel is not None:
            autostopper.logLevel = logLevel
            # it is only necessary to set it in one of them (here is the main
            # one), but can be any because they share their logLevel.
        return tuple(attrs)

    def _buildAutoStopperAttr(self, baseName, baseLabel, suffix,
                              autostopperComponent, dataType, memorised=False,
                              writable=False):
        attrName = "%s_%s" % (baseName, suffix)
        attrLabel = "%s %s" % (baseLabel, suffix)
        autostopperComponent.alias = attrName
        if memorised:
            autostopperComponent.setMemorised()
        rfun = autostopperComponent.read_attr
        if writable:
            wfun = autostopperComponent.write_attr
        else:
            wfun = None
        self.impl._internalAttrs[attrName] = autostopperComponent
        return self.add_Attr(attrName, dataType,
                             rfun=rfun, wfun=wfun,
                             label=attrLabel)

    def _buildAutoStopConditionAttr(self, condition, baseName, baseLabel,
                                    autostopper):
        conditionName = "%s_%s_Threshold" % (baseName, condition)
        conditionLabel = "%s %s Threshold" % (baseName, condition)
        conditioner = getattr(autostopper, '_%s' % (condition.lower()))
        conditioner.alias = conditionName
        conditioner.setMemorised()
        self.impl._internalAttrs[conditionName] = conditioner
        return self.add_Attr(conditionName, PyTango.DevDouble,
                             rfun=conditioner.read_attr,
                             wfun=conditioner.write_attr,
                             label=conditionLabel)

    def append2relations(self, origin, tag, dependency):
        self.impl.debug_stream("%s depends on %s (%s)"
                               % (origin, dependency, tag))
        if dependency not in self._relations:
            self._relations[dependency] = {}
        if tag not in self._relations[dependency]:
            self._relations[dependency][tag] = []
        self._relations[dependency][tag].append(origin)

    def __check_addresses_and_block_sizes(self, name, read_addr, write_addr):
        if read_addr is None and write_addr is not None:
            read_addr = self._db20_size+write_addr
            self.impl.debug_stream(
                "{0} define the read_addr {1} relative to the db20 size {2} "
                "and the write_addr{3}".format(name, read_addr,
                                               self._db20_size, write_addr))
        if read_addr > self.impl.ReadSize:
            self.impl.warn_stream(
                "{0} defines a read_addr {1} out of the size of the "
                "db20+db22 {2}: it will not be build"
                "".format(name, read_addr, self.impl.ReadSize))
            raise IndexError("Out of the DB20")
        if write_addr is not None and write_addr > self._db22_size:
            self.impl.warn_stream(
                "{0} defines a write_addr {1} out of the size of the db22 {2}: "
                "it will not be build".format(name, write_addr,
                                              self._db22_size))
            raise IndexError("Out of the DB22")
        return read_addr


def get_ip(iface='eth0'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockfd = sock.fileno()
    SIOCGIFADDR = 0x8915
    ifreq = struct.pack('16sH14s', iface, socket.AF_INET, '\x00'*14)
    try:
        res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
    except:
        return None
    ip = struct.unpack('16sH2x4s8x', res)[2]
    return socket.inet_ntoa(ip)

# PROTECTED REGION END --- LinacData.additionnal_import

# # Device States Description
# # INIT : The device is being initialised.
# # ON : PLC communication normal
# # ALARM : Transient issue
# # FAULT : Unrecoverable issue
# # UNKNOWN : No connection with the PLC, no state information


class LinacData(PyTango.Device_4Impl):

        # --------- Add you global variables here --------------------------
        # PROTECTED REGION ID(LinacData.global_variables) ---
        ReadSize = None
        WriteSize = None
        BindAddress = None  # deprecated
        LocalAddress = None
        RemoteAddress = None
        IpAddress = None  # deprecated
        PlcAddress = None
        Port = None
        LocalPort = None
        RemotePort = None
        # assigned by addAttrLocking
        locking_raddr = None
        locking_rbit = None
        locking_waddr = None
        locking_wbit = None
        lock_ST = None
        Locking = None
        is_lockedByTango = None
        heartbeat_addr = None
        AttrFile = None
        _plcAttrs = {}
        _internalAttrs = {}
        _addrDct = {}

        disconnect_t = 0
        read_db = None
        dataBlockSemaphore = threading.Semaphore()
        _important_logs = []

#         #ramping auxiliars
#         _rampThreads = {}
#         _switchThreads = {}

#         #hackish to reemit events
#         _sayAgainThread = None
#         _sayAgainQueue = None
        # FIXME: remove the expert attributes! ---

        # special event emition trace
        #_traceAttrs = []
        #_tracedAttrsHistory = {}
        #_historySize = 100

        _traceTooClose = []

        _prevMemDump = None
        _prevLockSt = None

        def debug_stream(self, msg):
            super(LinacData, self).debug_stream(
                "[%s] %s" % (threading.current_thread().getName(), msg))

        def info_stream(self, msg):
            super(LinacData, self).info_stream(
                "[%s] %s" % (threading.current_thread().getName(), msg))

        def warn_stream(self, msg):
            super(LinacData, self).warn_stream(
                "[%s] %s" % (threading.current_thread().getName(), msg))

        def error_stream(self, msg):
            super(LinacData, self).error_stream(
                "[%s] %s" % (threading.current_thread().getName(), msg))

        ####
        # PLC connectivity area ---
        def connect(self):
            '''This method is used to build the object that maintain the
               communications with the assigned PLC.
            '''
            if self.read_db is not None:
                return
            self.info_stream('connecting...')
            self.set_status('connecting...')
            try:
                self.read_db = tcpblock.open_datablock(self.PlcAddress,
                                                       self.Port,
                                                       self.ReadSize,
                                                       self.WriteSize,
                                                       self.BindAddress,
                                                       self.info_stream,
                                                       self.debug_stream,
                                                       self.warn_stream,
                                                       self.error_stream,
                                                       self.lock_ST)
                self.info_stream("build the tcpblock, socket %d"
                                 % (self.read_db.sock.fileno()))
                self.write_db = self.read_db
                self.info_stream('connected')
                self.set_state(PyTango.DevState.ON)
                self.set_status('connected')
                self.applyCheckers()
                return True
            except Exception as e:
                self.error_stream('connection failed exception: %s'
                                  % (traceback.format_exc()))
                self.set_state(PyTango.DevState.FAULT)
                self.set_status(traceback.format_exc())
                return False

        def disconnect(self):
            '''This method closes the connection to the assigned PLC.
            '''
            self.info_stream('disconnecting...')
            self.set_status('disconnecting...')
            # self._plcUpdatePeriod = PLC_MAX_UPDATE_PERIOD
            self._setPlcUpdatePeriod(PLC_MAX_UPDATE_PERIOD)
            try:
                if self.is_connected():
                    tcpblock.close_datablock(self.read_db, self.warn_stream)
                    self.read_db = None
                if self.get_state() == PyTango.DevState.ON:
                    self.set_state(PyTango.DevState.OFF)
                    self.set_status('not connected')
                return True
            except:
                return False

        def reconnect(self):
            '''
            '''
            if time.time() - self.last_update_time > self.ReconnectWait:
                self.connect()

        def is_connected(self):
            '''Checks if the object that interfaces the communication with
               the PLC is well made and available.
            '''
            return self.read_db is not None and self.read_db.sock is not None

        def has_data_available(self):
            '''Check if there is some usable data give from the PLC.
            '''
            return self.is_connected() and \
                len(self.read_db.buf) == self.ReadSize

        def setChecker(self, addr, values):
            if not hasattr(self, '_checks'):
                self.debug_stream("Initialise checks dict")
                self._checks = {}
            if isinstance(addr, int) and isinstance(values, list):
                self.debug_stream("Adding a checker for address %d "
                                 "with values %s" % (addr, values))
                self._checks[addr] = values
                return True
            return False

        def applyCheckers(self):
            if hasattr(self, '_checks') and isinstance(self._checks, dict) and \
                    hasattr(self, 'read_db') and isinstance(self.read_db,
                                                            tcpblock.Datablock):
                try:
                    had = len(self.read_db._checks.keys())
                    for addr in self._checks:
                        if not addr in self.read_db._checks:
                            self.debug_stream(
                                "\tfor addr %d insert %s"
                                % (addr, self._checks[addr]))
                            self.read_db.setChecker(addr, self._checks[addr])
                        else:
                            lst = self.read_db.getChecker(addr)
                            for value in self._checks[addr]:
                                if value not in lst:
                                    self.debug_stream(
                                        "\tin addr  %d append %s"
                                        % (addr, self._checks[addr]))
                                    self.read_db._checks.append(value)
                    now = len(self.read_db._checks.keys())
                    if had != now:
                        self.debug_stream("From %d to %d checkers" % (had, now))
                except Exception as e:
                    self.error_stream("Incomplete applyCheckers: %s" % (e))

        def forceWriteAttrs(self):
            '''There are certain situations, like the PLC shutdown, that
               results in a bad DB20 values received. Then the writable values
               cannot be written because the datablock only changes one
               register when many have bad values and is rejected by the plc.

               Due to this we force a construction of a complete write
               datablock to be send once for all.
            '''
            if not hasattr(self, 'write_db') or self.write_db is None:
                return
            wDct = self._addrDct['writeBlock']
            self.info_stream("Force to reconstruct the write data block")
            self.dataBlockSemaphore.acquire()
            self.attr_forceWriteDB_read = "%s\n" % (time.strftime(
                "%Y/%m/%d %H:%M:%S", time.localtime()))
            wblock_was = self.write_db.buf[self.write_db.write_start:]
            try:
                for wAddr in wDct:
                    if 'readAddr' in wDct[wAddr]:  # Uchars, Shorts, floats
                        name = wDct[wAddr]['name']
                        rAddr = wDct[wAddr]['readAddr']
                        T, size = TYPE_MAP[wDct[wAddr]['type']]
                        rValue = self.read_db.get(rAddr, T, size)
                        wValue = self.write_db.get(
                            wAddr+self.write_db.write_start, T, size)
                        msg = "%s = (%s, %s) [%s -> %s, %s, %s]" \
                            % (name, rValue, wValue, rAddr, wAddr, T, size)
                        self.attr_forceWriteDB_read += "%s\n" % msg
                        self.info_stream(msg)
                        self.write_db.write(wAddr, rValue, (T, size),
                                            dry=True)
                    else:  # booleans
                        was = byte = self.write_db.b(
                            wAddr+self.write_db.write_start)
                        msg = "booleans %d" % (wAddr)
                        self.attr_forceWriteDB_read += "%s\n" % msg
                        self.info_stream(msg)
                        for wBit in wDct[wAddr]:
                            name = wDct[wAddr][wBit]['name']
                            rAddr = wDct[wAddr][wBit]['readAddr']
                            rBit = wDct[wAddr][wBit]['readBit']
                            rValue = self.read_db.bit(rAddr, rBit)
                            wValue = self.write_db.bit(
                                wAddr+self.write_db.write_start, rBit)
                            msg = "\t%s = (%s, %s) [%s.%s -> %s.%s]" \
                                % (name, rValue, wValue, rAddr, rBit,
                                   wAddr, wBit)
                            self.attr_forceWriteDB_read += "%s\n" % msg
                            self.info_stream(msg)
                            if rValue is True:
                                byte = byte | (int(1) << wBit)
                            else:
                                byte = byte & ((0xFF) ^ (1 << wBit))
                        msg = "%d = %s -> %s" \
                              % (wAddr, binaryByte(was), binaryByte(byte))
                        self.attr_forceWriteDB_read += "%s\n" % msg
                        self.info_stream(msg)
                self.write_db.rewrite()
                wblock_is = self.write_db.buf[self.write_db.write_start:]
                i = 0
                msg = "writeblock:\n%-11s\t%-11s\n" % ("was:","now:")
                while i < len(wblock_was):
                    line = "%-11s\t%-11s\n" % (
                        ' '.join("%02x" % x for x in wblock_was[i:i+4]),
                        ' '.join("%02x" % x for x in wblock_is[i:i + 4]))
                    msg += line
                    i += 4
                self.attr_forceWriteDB_read += "%s\n" % msg
                self.info_stream(msg)
            except Exception as e:
                msg = "Could not complete the force Write\n%s" % (e)
                self.attr_forceWriteDB_read += "%s\n" % msg
                self.error_stream(msg)
            self.dataBlockSemaphore.release()

        # def _getWattrList(self):
        #     wAttrNames = []
        #     for attrName in self._plcAttrs.keys():
        #         attrStruct = self._getAttrStruct(attrName)
        #         if WRITEVALUE in attrStruct:
        #             wAttrNames.append(attrName)
        #     return wAttrNames

        # def _forceWriteDB(self, attr2write):
        #     for attrName in attr2write:
        #         attrStruct = self._getAttrStruct(attrName)
        #         write_addr = attrStruct[WRITEADDR]
        #         write_value = attrStruct[READVALUE]
        #         if type(attrStruct[READVALUE]) in [CircularBuffer,
        #                                            HistoryBuffer]:
        #             write_value = attrStruct[READVALUE].value
        #         else:
        #             write_value = attrStruct[READVALUE]
        #         self.info_stream("Dry write of %s value %s"
        #                          % (attrName, write_value))
        #         if WRITEBIT in attrStruct:
        #             read_addr = attrStruct[READADDR]
        #             write_bit = attrStruct[WRITEBIT]
        #             self.__writeBit(attrName, read_addr, write_addr, write_bit,
        #                             write_value, dry=True)
        #         else:
        #             self.write_db.write(write_addr, write_value,
        #                                 attrStruct[TYPE], dry=True)
        #     self.write_db.rewrite()
        # Done PLC connectivity area ---

        ####
        # state/status manager methods ---
        def set_state(self, newState, log=True):
            '''Overload of the superclass method to add event
               emission functionality.
            '''
            if self.get_state() != newState:
                if log:
                    self.warn_stream("Change state from %s to %s"
                                     % (self.get_state(), newState))
                PyTango.Device_4Impl.set_state(self, newState)
                self.push_change_event('State', newState)
                self.set_status("")
                # as this changes the state, clean non important
                # messages in status

        def set_status(self, newLine2status, important=False):
            '''Overload of the superclass method to add the extra feature of
               the persistent messages added to the status string.
            '''
            # self.debug_stream("In set_status()")
            newStatus = ""  # The device is in %s state.\n"%(self.get_state())
            for importantMsg in self._important_logs:
                if len(importantMsg) > 0:
                    newStatus = "%s%s\n" % (newStatus, importantMsg)
            if len(newLine2status) > 0 and \
                    newLine2status not in self._important_logs:
                newStatus = "%s%s\n" % (newStatus, newLine2status)
                if important:
                    self._important_logs.append(newLine2status)
            if len(newStatus) == 0:
                newStatus = "The device is in %s state.\n" % (self.get_state())
            oldStatus = self.get_status()
            if newStatus != oldStatus:
                PyTango.Device_4Impl.set_status(self, newStatus)
                self.warn_stream("New status message: %s"
                                 % (repr(self.get_status())))
                self.push_change_event('Status', newStatus)

        def clean_status(self):
            '''With the extra feature of the important logs, this method allows
               to clean all those logs as a clean interlocks method does.
            '''
            self.debug_stream("In clean_status()")
            self._important_logs = []
            self.set_status("")
        # done state/status manager methods ---

#         def __doTraceAttr(self, attrName, tag):
#             if attrName in self._traceAttrs:
#                 attrStruct = self._getAttrStruct(attrName)
#                 readValue = attrStruct[READVALUE]
#                 if WRITEVALUE in attrStruct:
#                     writeValue = attrStruct[WRITEVALUE]
#                 else:
#                     writeValue = float('NaN')
#                 quality = "%s" % attrStruct[LASTEVENTQUALITY]
#                 timestamp = time.ctime(attrStruct[READTIME])
#                 if attrName not in self._tracedAttrsHistory:
#                     self._tracedAttrsHistory[attrName] = []
#                 self._tracedAttrsHistory[attrName].append(
#                     [tag, readValue, writeValue, quality, timestamp])
#                 self.debug_stream("Traceing %s with %s tag: "
#                                   "read = %s, write = %s (%s,%s)"
#                                   % (attrName, tag, readValue, writeValue,
#                                      quality, timestamp))
#                 while len(self._tracedAttrsHistory[attrName]) > \
#                         self._historySize:
#                     self._tracedAttrsHistory[attrName].pop(0)

        ####
        # event methods ---
        def fireEvent(self, attrEventStruct, timestamp=None):
            '''Method with the procedure to emit an event from one existing
               attribute. Minimal needs are the attribute name and the value
               to emit, but also can be specified the quality and the timestamp
            '''
            attrName = attrEventStruct[0]
            if attrName not in ['lastUpdate', 'lastUpdateStatus']:
                self.warn_stream("DEPRECATED: fireEvent(%s)" % attrName)
            attrValue = attrEventStruct[1]
            if timestamp is None:
                timestamp = time.time()
            if len(attrEventStruct) == 3:  # the quality is specified
                quality = attrEventStruct[2]
            else:
                quality = PyTango.AttrQuality.ATTR_VALID
            # self.__doTraceAttr(attrName, "fireEvent(%s)" % attrValue)
            if self.__isHistoryBuffer(attrName):
                attrValue = self.__buildHistoryBufferString(attrName)
                self.push_change_event(attrName, attrValue, timestamp, quality)
            else:
                self.push_change_event(attrName, attrValue, timestamp, quality)
            attrStruct = self._getAttrStruct(attrName)
            if attrStruct is not None and \
                    LASTEVENTQUALITY in attrStruct and \
                    not quality == attrStruct[LASTEVENTQUALITY]:
                attrStruct[LASTEVENTQUALITY] = quality
            if attrStruct is not None and EVENTTIME in attrStruct:
                now = time.time()
                attrStruct[EVENTTIME] = now
                attrStruct[EVENTTIMESTR] = time.ctime(now)

        def fireEventsList(self, eventsAttrList, timestamp=None, log=False):
            '''Given a set of pair [attr,value] (with an optional third element
               with the quality) emit events for all of them with the same
               timestamp.
            '''
            if log:
                self.debug_stream("In fireEventsList(): %d events:\n%s"
                                  % (len(eventsAttrList),
                                     ''.join("\t%s\n" % line
                                             for line in eventsAttrList)))
            if timestamp is None:
                timestamp = time.time()
            attrNames = []
            for attrEvent in eventsAttrList:
                try:
                    self.fireEvent(attrEvent, timestamp)
                    attrNames.append(attrEvent[0])
                except Exception as e:
                    self.error_stream("In fireEventsList() Exception with "
                                      "attribute %s: %s" % (attrEvent, e))
                    traceback.print_exc()
        # done event methods ---

        ####
        # Read Attr method for dynattrs ---
        # def __applyReadValue(self, attrName, attrValue, timestamp=None):
        #     '''Hide the internal differences of the stored attribute struct
        #        and return the last value read from the PLC for a certain attr.
        #     '''
        #     self.warn_stream("DEPRECATED: __applyReadValue(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     if timestamp is None:
        #         timestamp = time.time()
        #     if not self.__filterAutoStopCollection(attrName):
        #         return
        #     if type(attrStruct[READVALUE]) in [CircularBuffer, HistoryBuffer]:
        #         attrStruct[READVALUE].append(attrValue)
        #     else:
        #         attrStruct[READVALUE] = attrValue
        #     attrStruct[READTIME] = timestamp
        #     # attrStruct[READTIMESTR] = time.ctime(timestamp)

        # def __filterAutoStopCollection(self, attrName):
        #     '''This method is made to manage the collection of data on the
        #        integration buffer for attributes with the autostop feature.
        #        No data shall be collected when it is already off (and the
        #        autostop will not stop anything).
        #     '''
        #     self.warn_stream("DEPRECATED: __filterAutoStopCollection(%s)"
        #                      % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     if AUTOSTOP in attrStruct and \
        #             SWITCHDESCRIPTOR in attrStruct[AUTOSTOP]:
        #         switchName = attrStruct[AUTOSTOP][SWITCHDESCRIPTOR]
        #         switchStruct = self._getAttrStruct(switchName)
        #         if READVALUE in switchStruct and not switchStruct[READVALUE]:
        #             # do not collect data when the switch to stop
        #             # is already off
        #             self.debug_stream("The switch for %s the autostopper is "
        #                               "off, no needed to collect values"
        #                               % (attrName))
        #             # if there is data collected, do not clean it until a new
        #             # transition from off to on.
        #             return False
        #     return True

        # def __applyWriteValue(self, attrName, attrValue):
        #     '''Hide the internal attribute struct representation and give an
        #        interface to set a value to be written.
        #     '''
        #     self.warn_stream("DEPRECATED: __applyWriteValue(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     if WRITEVALUE in attrStruct:
        #         attrStruct[WRITEVALUE] = attrValue

        # def __buildAttrMeaning(self, attrName, attrValue):
        #     '''As some (state-like) attributes have a meaning, there is a
        #        status-like attribute that reports what the documentation
        #        assign to the enumeration.
        #     '''
        #     self.warn_stream("DEPRECATED: __buildAttrMeaning(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     meanings = attrStruct[MEANINGS]
        #     if attrValue in meanings:
        #         return "%d:%s" % (attrValue, meanings[attrValue])
        #     else:
        #         return "%d:unknown" % (attrValue)

        # def __buildAttrQuality(self, attrName, attrValue):
        #     '''Resolve the quality the an specific value has for an attribute.
        #     '''
        #     self.warn_stream("DEPRECATED: __buildAttrQuality(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     if QUALITIES in attrStruct:
        #         qualities = attrStruct[QUALITIES]
        #         if self.__checkQuality(attrName, attrValue, ALARM):
        #             return PyTango.AttrQuality.ATTR_ALARM
        #         elif self.__checkQuality(attrName, attrValue, WARNING):
        #             return PyTango.AttrQuality.ATTR_WARNING
        #         elif self.__checkQuality(attrName, attrValue, CHANGING):
        #             return PyTango.AttrQuality.ATTR_CHANGING
        #     if self.attr_IsTooFarEnable_read and \
        #             SETPOINT in attrStruct:
        #         try:
        #             # This is to review if, not having the value changing
        #             # (previous if) the readback value is or not too far away
        #             # from the given setpoint.
        #             setpointAttrName = attrStruct[SETPOINT]
        #             try:
        #                 readback = attrStruct[READVALUE].value
        #             except:
        #                 return PyTango.AttrQuality.ATTR_INVALID
        #             setpoint = \
        #                 self._getAttrStruct(setpointAttrName)[READVALUE].value
        #             if setpoint is not None:
        #                 if self.__tooFar(attrName, setpoint, readback):
        #                     if attrName in self._traceTooClose:
        #                         self.warn_stream("Found %s readback (%6.3f) "
        #                                          "too far from setpoint "
        #                                          "(%6.3f)" % (attrName,
        #                                                       readback,
        #                                                       setpoint))
        #                     return PyTango.AttrQuality.ATTR_WARNING
        #                 if attrName in self._traceTooClose:
        #                     self.info_stream("Found %s readback (%6.3f) "
        #                                      "close enought to the setpoint "
        #                                      "(%6.3f)" % (attrName, readback,
        #                                                   setpoint))
        #         except Exception as e:
        #             self.warn_stream("Error comparing readback with "
        #                              "setpoint: %s" % (e))
        #             traceback.print_exc()
        #             return PyTango.AttrQuality.ATTR_INVALID
        #     return PyTango.AttrQuality.ATTR_VALID

        # def __tooFar(self, attrName, setpoint, readback):
        #     '''
        #         Definition of 'too far': when the readback and the setpoint
        #         differ more than a certain percentage, the quality of the
        #         readback attribute is warning.
        #         But this doesn't apply when the setpoint is too close to 0.
        #
        #         Definition of 'too far': there are two different definitions
        #         - When the setpoint is "close to 0" the warning quality alert
        #           will be raised if the readback has a difference bigger than
        #           0.1 (plus minus).
        #         - If the setpoint is not that close to 0, the warning alert
        #           will be raised when their difference is above the 10%.
        #           It has been used a multiplicative notation but it can be
        #           made also with additive notation using a multiplication
        #           factor.
        #     '''
        #     self.warn_stream("DEPRECATED: __tooFar(%s)" % (attrName))
        #     if (-CLOSE_ZERO < setpoint < CLOSE_ZERO) or readback == 0:
        #         diff = abs(setpoint - readback)
        #         if (diff > CLOSE_ZERO):
        #             return True
        #     else:
        #         diff = abs(setpoint / readback)
        #         # 10%
        #         if (1-REL_PERCENTAGE > diff or diff > 1+REL_PERCENTAGE):
        #             return True
        #     return False

        # def __checkQuality(self, attrName, attrValue, qualityInQuery):
        #     '''Check if this attrName with the give attrValue is with in the
        #        threshold of the give quality
        #     '''
        #     self.warn_stream("DEPRECATED: __checkQuality(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     qualities = attrStruct[QUALITIES]
        #     if qualityInQuery in qualities:
        #         if type(qualities[qualityInQuery]) == dict:
        #             if self.__checkAbsoluteRange(qualities[qualityInQuery],
        #                                          attrValue):
        #                 return True
        #             buffer = attrStruct[READVALUE]
        #             if self.__checkRelativeRange(qualities[qualityInQuery],
        #                                          buffer,
        #                                          attrValue):
        #                 return True
        #             return False
        #         elif type(qualities[qualityInQuery]) == list:
        #             if attrValue in qualities[qualityInQuery]:
        #                 return True
        #     return False

        # def __checkAbsoluteRange(self, qualityDict, referenceValue):
        #     '''Check if the a value is with in any of the configured absolute
        #        ranges for the specific configuration with in an attribute.
        #     '''
        #     # self.warn_stream("DEPRECATED: __checkAbsoluteRango()")
        #     if ABSOLUTE in qualityDict:
        #         if ABOVE in qualityDict[ABSOLUTE]:
        #             above = qualityDict[ABSOLUTE][ABOVE]
        #         else:
        #             above = float('inf')
        #         if BELOW in qualityDict[ABSOLUTE]:
        #             below = qualityDict[ABSOLUTE][BELOW]
        #         else:
        #             below = float('-inf')
        #         if UNDER in qualityDict[ABSOLUTE] and \
        #                 qualityDict[ABSOLUTE][UNDER]:
        #             if above < referenceValue < below:
        #                 return True
        #         else:
        #             if not below <= referenceValue <= above:
        #                 return True
        #     return False

        # def __checkRelativeRange(self, qualityDict, buffer, referenceValue):
        #     '''Check if the a value is with in any of the configured relative
        #        ranges for the specific configuration with in an attribute.
        #     '''
        #     # self.warn_stream("DEPRECATED: __checkRelativeRange()")
        #     if RELATIVE in qualityDict and isintance(buffer, CircularBuffer):
        #         if buffer.std >= qualityDict[RELATIVE]:
        #             return True
        #     return False

        def _getAttrStruct(self, attrName):
            '''Given an attribute name, return the internal structure that
               defines its behaviour.
            '''
            try:
                return self._plcAttrs[
                    self.__getDctCaselessKey(attrName, self._plcAttrs)]
            except ValueError as e:
                pass  # simply was not in the plcAttrs
            try:
                return self._internalAttrs[
                    self.__getDctCaselessKey(attrName, self._internalAttrs)]
            except ValueError as e:
                pass  # simply was not in the internalAttrs
            if attrName.count('_'):
                mainName, suffix = attrName.rsplit('_', 1)
                try:
                    return self._internalAttrs[
                        self.__getDctCaselessKey(mainName,
                                                 self._internalAttrs)]
                except ValueError as e:
                    pass  # simply was not in the internalAttrs
            return None

        def __getDctCaselessKey(self, key, dct):
            position = [e.lower() for e in dct].index(key.lower())
            return dct.keys()[position]

        # def __solveFormula(self, attrName, VALUE, formula):
        #     '''Some attributes can have a formula to interpret or modify the
        #        value given from the PLC to the value reported by the device.
        #     '''
        #     self.warn_stream("DEPRECATED: __solveFormula(%s)" % (attrName))
        #     result = eval(formula)
        #     # self.debug_stream("%s formula eval(\"%s\") = %s" % (attrName,
        #     #                                                     formula,
        #     #                                                     result))
        #     return result

        # def __setAttrValue(self, attr, attrName, attrType, attrValue,
        #                    timestamp):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: __setAttrValue(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     self.__applyReadValue(attrName, attrValue, timestamp)
        #     if attrValue is None:
        #         attr.set_value_date_quality(0, timestamp,
        #                                     PyTango.AttrQuality.ATTR_INVALID)
        #     # if MEANINGS in attrStruct:
        #     #      attrMeaning = self.__buildAttrMeaning(attrName, attrValue)
        #     #     attrQuality = self.__buildAttrQuality(attrName, attrValue)
        #     #     attr.set_value_date_quality(attrMeaning, timestamp,
        #     #                                 attrQuality)
        #     elif QUALITIES in attrStruct:
        #         attrQuality = self.__buildAttrQuality(attrName, attrValue)
        #         attr.set_value_date_quality(attrValue, timestamp,
        #                                     attrQuality)
        #     else:
        #         attrQuality = PyTango.AttrQuality.ATTR_VALID
        #         attr.set_value_date_quality(attrValue, timestamp, attrQuality)
        #     if WRITEADDR in attrStruct:
        #         writeAddr = attrStruct[WRITEADDR]
        #         sp_addr = self.offset_sp + writeAddr
        #         if WRITEBIT in attrStruct:
        #             writeBit = attrStruct[WRITEBIT]
        #             writeValue = self.read_db.bit(sp_addr, writeBit)
        #         else:
        #             writeValue = self.read_db.get(sp_addr, *attrType)
        #             if FORMULA in attrStruct and \
        #                     'write' in attrStruct[FORMULA]:
        #                 try:
        #                     writeValue = self.\
        #                         __solveFormula(attrName, writeValue,
        #                                        attrStruct[FORMULA]['write'])
        #                 except Exception as e:
        #                     self.error_stream("Cannot solve formula for the "
        #                                       "attribute %s: %s" % (attrName,
        #                                                             e))
        #             # if attrStruct.formula is not None:
        #             #     try:
        #             #         writeValue = attrStruct.formula.writeHook(
        #             #             writeValue)
        #             #     except Exception as e:
        #             #         self.error_stream("Cannot solve formula for the "
        #             #                           "attribute %s: %s" % (attrName,
        #             #                                                 e))
        #             if 'format' in attrStruct:
        #                 try:
        #                     format = attrStruct['format']
        #                     if format.endswith("d"):
        #                         writeValue = int(format % writeValue)
        #                     else:
        #                         writeValue = float(format % writeValue)
        #                 except Exception as e:
        #                     self.error_stream("Cannot format value for the "
        #                                       "attribute %s: %s"
        #                                       % (attrName, e))
        #         self.__applyWriteValue(attrName, writeValue)
        #         try:
        #             attr.set_write_value(writeValue)
        #         except PyTango.DevFailed as e:
        #             self.tainted = "%s/%s: failed to set point %s (%s)"\
        #                            % (self.get_name(), attrName, writeValue, e)
        #             self.error_stream(self.tainted)
        #     elif WRITEVALUE in attrStruct:
        #         try:
        #             writeValue = attrStruct[WRITEVALUE]
        #             attr.set_write_value(writeValue)
        #         except PyTango.DevFailed:
        #             self.tainted = self.get_name() + '/'+attrName + \
        #                 ': failed to set point '+str(writeValue)
        #             self.error_stream("On setAttrValue(%s,%s) tainted: %s"
        #                               % (attrName, str(attrValue),
        #                                  self.tainted))
        #         except Exception as e:
        #             self.warn_stream("On setAttrValue(%s,%s) Exception: %s"
        #                              % (attrName, str(attrValue), e))
        #     # self.__doTraceAttr(attrName, "__setAttrvalue")
        #     # Don't need to trace each time the attribute is read.

        @AttrExc
        def read_attr(self, attr):
            '''
            '''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            name = attr.get_name()
            attrStruct = self._getAttrStruct(name)
            if any([isinstance(attrStruct, kls) for kls in [PLCAttr,
                                                            InternalAttr,
                                                            EnumerationAttr,
                                                            MeaningAttr,
                                                            HistoryAttr,
                                                            AutoStopAttr,
                                                            AutoStopParameter,
                                                            GroupAttr
                                                            ]]):
                attrStruct.read_attr(attr)
                return
        #     self.warn_stream("DEPRECATED read_attr for %s" % (name))
        #     attrType = attrStruct[TYPE]
        #     read_addr = attrStruct[READADDR]
        #     if READBIT in attrStruct:
        #         read_bit = attrStruct[READBIT]
        #     else:
        #         read_bit = None
        #     try:
        #         if read_bit:
        #             read_value = self.read_db.bit(read_addr, read_bit)
        #         else:
        #             read_value = self.read_db.get(read_addr, *attrType)
        #             if FORMULA in attrStruct and \
        #                     'read' in attrStruct[FORMULA]:
        #                 read_value = self.\
        #                     __solveFormula(name, read_value,
        #                                    attrStruct[FORMULA]['read'])
        #         read_t = time.time()
        #     except Exception as e:
        #         self.error_stream('Trying to read %s/%s and looks to be not '
        #                           'well connected to the plc.'
        #                           % (self.get_name(), attr.get_name()))
        #         self.debug_stream('Exception (%s/%s): %s'
        #                           % (self.get_name(), attr.get_name(), e))
        #         traceback.print_exc()
        #     else:
        #         self.__setAttrValue(attr, name, attrType, read_value, read_t)

        # @AttrExc
        # def read_spectrumAttr(self, attr):
        #     '''This method is a generic read for dynamic spectrum attributes in
        #        this device. But right now only supports the historic buffers.
        #
        #        The other spectrum attributes, related with the events
        #        generation are not using this because they have they own method.
        #     '''
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     name = attr.get_name()
        #     attrStruct = self._getAttrStruct(name)
        #     if any([isinstance(attrStruct, kls) for kls in [PLCAttr,
        #                                                     InternalAttr,
        #                                                     EnumerationAttr,
        #                                                     MeaningAttr,
        #                                                     AutoStopAttr,
        #                                                     AutoStopParameter,
        #                                                     GroupAttr
        #                                                     ]]):
        #         attrStruct.read_spectrumAttr(attr)
        #         return
        #     self.warn_stream("DEPRECATED read_spectrumAttr for %s" % (name))
        #     if BASESET in attrStruct:
        #         attrValue = self.__buildHistoryBufferString(name)
        #     elif AUTOSTOP in attrStruct:
        #         attrValue = attrStruct[READVALUE].array
        #     attrTimeStamp = attrStruct[READTIME] or time.time()
        #     attrQuality = attrStruct[LASTEVENTQUALITY] or \
        #         PyTango.AttrQuality.ATTR_VALID
        #     self.debug_stream("Attribute %s: value=%s timestamp=%g quality=%s "
        #                       "len=%d" % (name, attrValue, attrTimeStamp,
        #                                   attrQuality, len(attrValue)))
        #     attr.set_value_date_quality(attrValue, attrTimeStamp, attrQuality)

        # def read_logical_attr(self, attr):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: read_logical_attr(%s)"
        #                      % attr.get_name())
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     attrName = attr.get_name()
        #     if attrName in self._internalAttrs:
        #         ret = self._evalLogical(attrName)
        #         read_t = self._internalAttrs[attrName][READTIME]
        #         self.__setAttrValue(attr, attrName, PyTango.DevBoolean, ret,
        #                             read_t)

        # def _evalLogical(self, attrName):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: _evalLogical(%s)" % (attrName))
        #     if attrName not in self._internalAttrs:
        #         return
        #     attrStruct = self._internalAttrs[attrName]
        #     if attrStruct.logicObj is None:
        #         return
        #     logic = attrStruct.logicObj.logic
        #     values = []
        #     self.info_stream("Evaluate %s LogicAttr" % attrName)
        #     for key in logic.keys():
        #         try:
        #             if type(logic[key]) == dict:
        #                 values.append(self.__evaluateDict(key, logic[key]))
        #             elif type(logic[key]) == list:
        #                 values.append(self.__evaluateList(key, logic[key]))
        #             else:
        #                 self.warn_stream("step less to evaluate %s for "
        #                                  "key %s unmanaged content type"
        #                                  % (attrName, key))
        #         except Exception as e:
        #             self.error_stream("cannot eval logic attr %s for key %s: "
        #                               "%s" % (attrName, key, e))
        #             traceback.print_exc()
        #     if attrStruct.logicObj.operator == 'or':
        #         ret = any(values)
        #     elif attrStruct.logicObj.operator == 'and':
        #         ret = all(values)
        #     attrStruct.read_t = time.time()
        #     if attrStruct.logicObj.inverted:
        #         ret = not ret
        #         self.info_stream("For %s: values %s (%s) (inverted) answer %s"
        #                          % (attrName, values, attrStruct.operator, ret))
        #     else:
        #         self.info_stream("For %s: values %s (%s) answer %s"
        #                          % (attrName, values, attrStruct.operator, ret))
        #     attrStruct.read_value = ret
        #     return ret

        # def __evaluateDict(self, attrName, dict2eval):
        #     """
        #     """
        #     self.warn_stream("DEPRECATED: __evaluateDict(%s)" % (attrName))
        #     self.info_stream("%s dict2eval: %s" % (attrName, dict2eval))
        #     for key in dict2eval.keys():
        #         if key == QUALITIES:
        #             return self.__evaluateQuality(attrName, dict2eval[key])

        # def __evaluateList(self, attrName, list2eval):
        #     """
        #     """
        #     self.warn_stream("DEPRECATED: __evaluateList(%s)" % (attrName))
        #     self.info_stream("%s list2eval: %r" % (attrName, list2eval))
        #     value = self.__getAttrReadValue(attrName)
        #     self.info_stream("%s value: %r" % (attrName, value))
        #     return value in list2eval

        # def __evaluateQuality(self, attrName, searchList):
        #     """
        #     """
        #     self.warn_stream("DEPRECATED: __evaluateQuality(%s)" % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     if LASTEVENTQUALITY in attrStruct:
        #         quality = attrStruct[LASTEVENTQUALITY]
        #         return quality in searchList
            return False

        # FIXME: this method is merged with read_attr(), and once write
        #        versions become also merged, they will be not necessary
        #        anymore.
        # @AttrExc
        # def read_attr_bit(self, attr):
        #     '''
        #     '''
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     name = attr.get_name()
        #     attrType = PyTango.DevBoolean
        #     attrStruct = self._getAttrStruct(name)
        #     if any([isinstance(attrStruct, kls) for kls in [PLCAttr,
        #                                                     InternalAttr,
        #                                                     EnumerationAttr,
        #                                                     MeaningAttr,
        #                                                     AutoStopAttr,
        #                                                     AutoStopParameter,
        #                                                     GroupAttr
        #                                                     ]]):
        #         attrStruct.read_attr(attr)
        #         return
        #     self.warn_stream("DEPRECATED read_attr_bit for %s" % (name))
        #     read_addr = attrStruct[READADDR]
        #     read_bit = attrStruct[READBIT]
        #     # if WRITEADDR in attrStruct:
        #     #     write_addr = attrStruct[WRITEADDR]
        #     #     write_bit = attrStruct[WRITEBIT]
        #     # else:
        #     #     write_addr = None
        #     #     write_bit = None
        #     try:
        #         if read_addr and read_bit:
        #             read_value = self.read_db.bit(read_addr, read_bit)
        #             if FORMULA in attrStruct and \
        #                     'read' in attrStruct[FORMULA]:
        #                 read_value = self.\
        #                     __solveFormula(name, read_value,
        #                                    attrStruct[FORMULA]['read'])
        #             read_t = time.time()
        #         else:
        #             read_value, read_t, _ = attrStruct.vtq
        #             attrType = attrStruct.type
        #     except Exception as e:
        #         self.error_stream('Trying to read %s/%s and looks to be not '
        #                           'well connected to the plc.'
        #                           % (self.get_name(), attr.get_name()))
        #         self.debug_stream('Exception (%s/%s): %s'
        #                           % (self.get_name(), attr.get_name(), e))
        #     else:
        #         self.__setAttrValue(attr, name, attrType, read_value, read_t)

        # def read_attrGrpBit(self, attr):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: read_attrGrpBit(%s)"
        #                      % (attr.get_name()))
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     attrName = attr.get_name()
        #     if attrName in self._internalAttrs:
        #         attrStruct = self._getAttrStruct(attrName)
        #         if 'read_set' in attrStruct:
        #             read_value = self.__getGrpBitValue(attrName,
        #                                                attrStruct['read_set'],
        #                                                self.read_db)
        #             read_t = time.time()
        #             if 'write_set' in attrStruct:
        #                 write_set = attrStruct['write_set']
        #                 write_value = self.__getGrpBitValue(attrName,
        #                                                     write_set,
        #                                                     self.write_db)
        #                 self.__applyWriteValue(attrName,
        #                                        attrStruct[WRITEVALUE])
        #             self.__setAttrValue(attr, attrName, PyTango.DevBoolean,
        #                                 read_value, read_t)

        # def __getGrpBitValue(self, attrName, addrSet, memSegment):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: __getGrpBitValue(%s)" % (attrName))
        #     try:
        #         bitSet = []
        #         for addr, bit in addrSet:
        #             bitSet.append(memSegment.bit(addr, bit))
        #         if all(bitSet):
        #             return True
        #     except Exception as e:
        #         self.error_stream("Cannot get the bit group for %s [%s]: %s\n"
        #                           % (attrName, str(addrSet), e,
        #                              str(self._internalAttrs[attrName])))
        #     return False

        def read_lock(self):
            '''
            '''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            rbyte = self.read_db.b(self.locking_raddr)
            locker = bool(rbyte & (1 << self.locking_rbit))
            return locker

        @AttrExc
        def read_Locking(self, attr):
            '''The read of this attribute is a boolean to represent if the
               control of the plc has been take by tango. This doesn't look
               to correspond exactly with the same meaning of the "Local Lock"
               boolean in the memory map of the plc'''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            self._checkLocking()
            attrName = attr.get_name()
            value, timestamp, quality = self._plcAttrs[attrName].vtq
            attr.set_value_date_quality(value, timestamp, quality)

        @AttrExc
        def read_Lock_ST(self, attr):
            '''
            '''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            attrName = attr.get_name()
            self.info_stream('DEPRECATED: reading %s' % (attrName))
            value, timestamp, quality = self._plcAttrs[attrName].vtq
            attr.set_value_date_quality(value, timestamp, quality)

        def _checkLocking(self):
            if self._isLocalLocked() or self._isRemoteLocked():
                self._lockingChange(True)
            else:
                self._lockingChange(False)

        def _isLocalLocked(self):
            return self._deviceIsInLocal and \
                self._plcAttrs['Lock_ST'].rvalue == 1

        def _isRemoteLocked(self):
            return self._deviceIsInRemote and \
                self._plcAttrs['Lock_ST'].rvalue == 2

        def _lockingChange(self, newLockValue):
            if self.is_lockedByTango != newLockValue:
                if 'Locking' in self._plcAttrs:
                    self._plcAttrs['Locking'].read_value = newLockValue
                self.is_lockedByTango = newLockValue

        # @AttrExc
        # def read_internal_attr(self, attr):
        #     '''this is referencing to a device attribute that doesn't
        #         have plc representation
        #     '''
        #     self.warn_stream("DEPRECATED: read_internal_attr(%s)"
        #                      % (attr.get_name()))
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     try:
        #         attrName = attr.get_name()
        #         if attrName in self._internalAttrs:
        #             attrStruct = self._getAttrStruct(attrName)
        #             if READVALUE in attrStruct:
        #                 read_value = attrStruct[READVALUE]
        #                 if read_value is None:
        #                     attr.set_value_date_quality(0, time.time(),
        #                                                 PyTango.AttrQuality.
        #                                                 ATTR_INVALID)
        #                 else:
        #                     attr.set_value(read_value)
        #             else:
        #                 attr.set_value_date_quality(0, time.time(),
        #                                             PyTango.AttrQuality.
        #                                             ATTR_INVALID)
        #             if WRITEVALUE in attrStruct:
        #                 write_value = attrStruct[WRITEVALUE]
        #                 attr.set_write_value(write_value)
        #     except Exception as e:
        #         self.error_stream("read_internal_attr(%s) Exception %s"
        #                           % (attr.get_name(), e))
        # # Read Attr method for dynattrs ---

        ####
        # Write Attr method for dynattrs ---
        def prepare_write(self, attr):
            '''
            '''
            self.warn_stream(": prepare_write(%s)"
                             % (attr.get_name()))
            data = []
            self.Locking.get_write_value(data)
            val = data[0]
            if attr.get_name().lower() in ['locking']:
                self.debug_stream("Do not do the write checks, when what is "
                                  "wanted is to write the locker")
                # FIXME: perhaps check if it is already lock by another program
            elif not self.read_lock():
                try:
                    exceptionMsg = 'first required to set Locking flag on '\
                        '%s device' % self.get_name()
                except Exception as e:
                    self.error_stream("Exception in prepare_write(): %s" % (e))
                else:
                    raise LinacException(exceptionMsg)
            if self.tainted:
                raise LinacException('mismatch with '
                                     'specification:\n'+self.tainted)
            data = []
            attr.get_write_value(data)
            return data[0]

        @AttrExc
        def write_attr(self, attr):
            '''
            '''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            name = attr.get_name()
            attrStruct = self._getAttrStruct(name)
            if any([isinstance(attrStruct, kls) for kls in [PLCAttr,
                                                            InternalAttr,
                                                            EnumerationAttr,
                                                            MeaningAttr,
                                                            AutoStopAttr,
                                                            AutoStopParameter,
                                                            GroupAttr
                                                            ]]):
                attrStruct.write_attr(attr)
                return
        #     self.warn_stream("DEPRECATED write_attr for %s" % (name))
        #     attrType = attrStruct[TYPE]
        #     write_addr = attrStruct[WRITEADDR]
        #     write_value = self.prepare_write(attr)
        #     if FORMULA in attrStruct and 'write' in attrStruct[FORMULA]:
        #         write_value = self.__solveFormula(name, write_value,
        #                                           attrStruct[FORMULA]['write'])
        #     attrStruct[WRITEVALUE] = write_value
        #     # self.__doTraceAttr(name, "write_attr")
        #     self.write_db.write(write_addr, write_value, attrType)

        # @AttrExc
        # def write_attr_bit(self, attr):
        #     '''
        #     '''
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     name = attr.get_name()
        #     write_value = self.prepare_write(attr)
        #     self.doWriteAttrBit(attr, name, write_value)
        #     # self.__doTraceAttr(name, "write_attr_bit")

#         def doWriteAttrBit(self, attr, name, write_value):
#             attrStruct = self._getAttrStruct(name)
#             if any([isinstance(attrStruct, kls) for kls in [PLCAttr,
#                                                             InternalAttr,
#                                                             EnumerationAttr,
#                                                             MeaningAttr,
#                                                             AutoStopAttr,
#                                                             AutoStopParameter,
#                                                             GroupAttr
#                                                             ]]):
#                 attrStruct.write_attr(attr)
#                 return
#             self.warn_stream("DEPRECATED write_attr_bit for %s" % (name))
#             read_addr = attrStruct[READADDR]
#             write_addr = attrStruct[WRITEADDR]
#             write_bit = attrStruct[WRITEBIT]
#             if FORMULA in attrStruct and 'write' in attrStruct[FORMULA]:
#                 formula_value = self.\
#                     __solveFormula(name, write_value,
#                                    attrStruct[FORMULA]['write'])
#                 self.info_stream("%s received %s formula eval(\"%s\") = %s"
#                                  % (name, write_value,
#                                     attrStruct[FORMULA]['write'],
#                                     formula_value))
#                 if formula_value != write_value and \
#                         'write_not_allowed' in attrStruct[FORMULA]:
#                     reason = "Write %s not allowed" % write_value
#                     description = attrStruct[FORMULA]['write_not_allowed']
#                     PyTango.Except.throw_exception(reason,
#                                                    description,
#                                                    name,
#                                                    PyTango.ErrSeverity.WARN)
#                 else:
#                     write_value = formula_value
#             if SWITCHDESCRIPTOR in attrStruct:
#                 # For the switch with autostop, when transition to power on, is
#                 # necessary to clean the old collected information or it will
#                 # produce an influence on the conditions.
#                 descriptor = attrStruct[SWITCHDESCRIPTOR]
#                 if AUTOSTOP in descriptor:
#                     # if self.__stateTransitionToOn(write_value,descriptor) \
#                     #                        and descriptor.has_key(AUTOSTOP):
#                     self.__cleanAutoStopCollection(
#                         attrStruct[SWITCHDESCRIPTOR][AUTOSTOP])
# #                 #Depending to the on or off transition keys, this will launch
# #                 #a thread who will modify the ATTR2RAMP, and when that
# #                 #finishes the write will be set.
# #                 self.info_stream("attribute %s has receive a write %s"
# #                                  %(name,write_value))
# #                 if self.__stateTransitionNeeded(write_value,name):
# #                                                 #attrStruct[SWITCHDESCRIPTOR]):
# #                     self.info_stream("doing state transition for %s"%(name))
# #                     attrStruct[SWITCHDEST] = write_value
# #                     self.createSwitchStateThread(name)
# #                     return
#                 # The returns are necessary to avoid the write that is set
#                 # later on this method. But in the final else case it has to
#                 # continue.
#             self.__writeBit(name, read_addr, write_addr, write_bit,
#                             write_value)
#             attrStruct[WRITEVALUE] = write_value
#             self.info_stream("Received write %s (%s)" % (name,
#                                                          write_value))
#             if self.__isRstAttr(name) and write_value:
#                 attrStruct[RESETTIME] = time.time()

        # def __cleanAutoStopCollection(self, attrName):
        #     '''This will clean the buffer with autostop condition collected
        #        data and also the triggered boolean if it was raised.
        #     '''
        #     self.warn_stream("DEPRECATED: __cleanAutoStopCollection(%s)"
        #                      % (attrName))
        #     attrStruct = self._getAttrStruct(attrName)
        #     if READVALUE in attrStruct and len(attrStruct[READVALUE]) != 0:
        #         self.info_stream("Clean up the buffer because collected data "
        #                          "doesn't have sense having the swithc off.")
        #         attrStruct[READVALUE].resetBuffer()
        #     self._cleanTriggeredFlag(attrName)

        # def __writeBit(self, name, read_addr, write_addr, write_bit,
        #                write_value, dry=False):
        #     '''
        #     '''
        #     rbyte = self.read_db.b(read_addr)
        #     attrStruct = self._getAttrStruct(name)
        #     if write_value:
        #         # sets bit 'bitno' of b
        #         toWrite = rbyte | (int(1) << write_bit)
        #         # a byte of 0s with a unique 1 in the place to set this 1
        #     else:
        #         # clears bit 'bitno' of b
        #         toWrite = rbyte & ((0xFF) ^ (1 << write_bit))
        #         # a byte of 1s with a unique 0 in the place to set this 0
        #     if not dry:
        #         self.write_db.write(write_addr, toWrite,
        #                             TYPE_MAP[PyTango.DevUChar])
        #         reRead = self.read_db.b(read_addr)
        #         self.debug_stream("Writing %s boolean to %6s (%d.%d) byte was "
        #                           "%s; write %s; now %s"
        #                           % (name, write_value, write_addr, write_bit,
        #                              bin(rbyte), bin(toWrite), bin(reRead)))

        # def write_attrGrpBit(self, attr):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: write_attrGrpBit(%s)"
        #                      % (attr.get_name()))
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     attrName = attr.get_name()
        #     if attrName in self._internalAttrs:
        #         attrDescr = self._internalAttrs[attrName]
        #         if 'write_set' in attrDescr:
        #             writeValue = self.prepare_write(attr)
        #             self.__setGrpBitValue(attrDescr['write_set'],
        #                                   self.write_db, writeValue)

        # def __setGrpBitValue(self, addrSet, memSegment, value):
        #     '''
        #     '''
        #     # self.warn_stream("DEPRECATED: __setGrpBitValue()")
        #     try:
        #         for addr, bit in addrSet:
        #             rbyte = self.read_db.b(self.offset_sp+addr)
        #             if value:
        #                 toWrite = rbyte | (int(value) << bit)
        #             else:
        #                 toWrite = rbyte & (0xFF) ^ (1 << bit)
        #             memSegment.write(addr, toWrite, TYPE_MAP[PyTango.DevUChar])
        #             reRead = self.read_db.b(self.offset_sp+addr)
        #             self.debug_stream("Writing boolean to %6s (%d.%d) byte "
        #                               "was %s; write %s; now %s"
        #                               % (value, addr, bit, bin(rbyte),
        #                                  bin(toWrite), bin(reRead)))
        #     except Exception as e:
        #         self.error_stream("Cannot set the bit group: %s" % (e))

#         @AttrExc
#         def write_Locking(self, attr):
#             '''
#             '''
#             if self.get_state() == PyTango.DevState.FAULT or \
#                     not self.has_data_available():
#                 return  # raise AttributeError("Not available in fault state!")
#             try:
#                 self.write_lock(attr.get_write_value())
#             except:
#                 self.error_stream('Trying to write %s/%s and looks to be not '
#                                   'well connected to the plc.'
#                                   % (self.get_name(), attr.get_name()))

#         def check_lock(self):
#             '''Drops lock if write_value is True, but did not receive
#                lock_state if re
#             '''
#             pass

        # # autostop area ---
#         def _refreshInternalAutostopParams(self, attrName):
#             '''There are auxiliar attibutes with the autostop conditions and
#                when their values change them have to be introduced in the
#                structure of the main attribute with the buffer, who will use it
#                to take the decission.
#                This includes the resizing task of the CircularBuffer.
#             '''
#             # FIXME: use the spectrum attribute and left the circular buffer
#             # as it was to avoid side effects on relative events.
#             if attrName not in self._internalAttrs:
#                 return
#             attrStruct = self._internalAttrs[attrName]
#             if AUTOSTOP not in attrStruct:
#                 return
#             stopperDict = attrStruct[AUTOSTOP]
#             if 'is'+ENABLE in stopperDict:
#                 refAttr = self._getAttrStruct(stopperDict['is'+ENABLE])
#                 refAttr[AUTOSTOP][ENABLE] = attrStruct[READVALUE]
#             if 'is'+INTEGRATIONTIME in stopperDict:
#                 refAttr = self._getAttrStruct(stopperDict['is' +
#                                                           INTEGRATIONTIME])
#                 refAttr[AUTOSTOP][INTEGRATIONTIME] = attrStruct[READVALUE]
#                 # resize the CircularBuffer
#                 #   time per sample int(INTEGRATIONTIME/self._plcUpdatePeriod)
#                 newBufferSize = \
#                     int(attrStruct[READVALUE]/self._getPlcUpdatePeriod())
#                 if refAttr[READVALUE].maxSize() != newBufferSize:
#                     self.info_stream("%s buffer to be resized from %d to %d "
#                                      "(integration time %f seconds with a "
#                                      "plc reading period of %f seconds)"
#                                      % (attrName, refAttr[READVALUE].maxSize(),
#                                         newBufferSize, attrStruct[READVALUE],
#                                         self._plcUpdatePeriod))
#                     refAttr[READVALUE].resize(newBufferSize)
#             else:
#                 for condition in [BELOW, ABOVE]:
#                     if 'is'+condition+THRESHOLD in stopperDict:
#                         key = 'is'+condition+THRESHOLD
#                         refAttr = self._getAttrStruct(stopperDict[key])
#                         refAttr[AUTOSTOP][condition] = attrStruct[READVALUE]

        def _getPlcUpdatePeriod(self):
            return self._plcUpdatePeriod

        def _setPlcUpdatePeriod(self, value):
            self.info_stream("modifying PLC Update period: was %.3f and now "
                             "becomes %.3f." % (self._plcUpdatePeriod, value))
            self._plcUpdatePeriod = value
            # FIXME: this is hardcoding!!
            # self._refreshInternalAutostopParams('GUN_HV_I_AutoStop')

#         def _updateStatistic(self, attrName):
#             if attrName not in self._internalAttrs:
#                 return
#             attrStruct = self._internalAttrs[attrName]
#             if MEAN in attrStruct:
#                 refAttr = attrStruct[MEAN]
#                 if refAttr not in self._plcAttrs:
#                     return
#                 attrStruct[READVALUE] = self._plcAttrs[refAttr][READVALUE].mean
#             elif STD in attrStruct:
#                 refAttr = attrStruct[STD]
#                 if refAttr not in self._plcAttrs:
#                     return
#                 attrStruct[READVALUE] = self._plcAttrs[refAttr][READVALUE].std

#         def _cleanTriggeredFlag(self, attrName):
#             triggerName = "%s_%s" % (attrName, TRIGGERED)
#             if triggerName not in self._internalAttrs:
#                 return
#             if self._internalAttrs[triggerName][TRIGGERED]:
#                 # if it's powered off and it was triggered, then this
#                 # power off would be because autostop has acted.
#                 # Is needed to clean the flag.
#                 self.info_stream("Clean the autostop triggered flag "
#                                  "for %s" % (attrName))
#                 self._internalAttrs[triggerName][TRIGGERED] = False

#         def _checkAutoStopConditions(self, attrName):
#             '''The attribute with the Circular buffer has to do some checks
#                to decide if it's necessary to proceed with the autostop
#                procedure.
#             '''
#             if attrName not in self._plcAttrs:
#                 return
#             attrStruct = self._plcAttrs[attrName]
#             if AUTOSTOP not in attrStruct:
#                 return
#             if ENABLE not in attrStruct[AUTOSTOP] or \
#                     not attrStruct[AUTOSTOP][ENABLE]:
#                 return
#             if SWITCHDESCRIPTOR in attrStruct[AUTOSTOP]:
#                 switchStruct = \
#                     self._getAttrStruct(attrStruct[AUTOSTOP][SWITCHDESCRIPTOR])
#                 if READVALUE in switchStruct and \
#                         not switchStruct[READVALUE]:
#                     return
#             if len(attrStruct[READVALUE]) < attrStruct[READVALUE].maxSize():
#                 return
#             if SWITCHDESCRIPTOR in attrStruct[AUTOSTOP]:
#                 switchStruct = \
#                     self._getAttrStruct(attrStruct[AUTOSTOP][SWITCHDESCRIPTOR])
#                 if switchStruct is None or READVALUE not in switchStruct:
#                     return
#                 if SWITCHDEST in switchStruct:
#                     if switchStruct[SWITCHDEST]:
#                         return
#                     elif not switchStruct[READVALUE]:
#                         return
#                 for condition in [BELOW, ABOVE]:
#                     if condition in attrStruct[AUTOSTOP]:
#                         refValue = attrStruct[AUTOSTOP][condition]
#                         meanValue = attrStruct[READVALUE].mean
#                         # BELOW and ABOVE is compared with mean
#                         if condition == BELOW and refValue > meanValue:
#                             self.info_stream("Attribute %s stop condition "
#                                              "%s is met ref=%g > mean=%g"
#                                              % (attrName, condition,
#                                                 refValue, meanValue))
#                             self._doAutostop(attrName, condition)
#                         elif condition == ABOVE and refValue < meanValue:
#                             self.info_stream("Attribute %s stop condition "
#                                              "%s is met ref=%g < mean=%g"
#                                              % (attrName, condition,
#                                                 refValue, meanValue))
#                             self._doAutostop(attrName, condition)

#         def _doAutostop(self, attrName, condition):
#             attrStruct = self._plcAttrs[attrName]
#             refValue = attrStruct[AUTOSTOP][condition]
#             meanValue, stdValue = attrStruct[READVALUE].meanAndStd
#             self.doWriteAttrBit(attrStruct[AUTOSTOP][SWITCHDESCRIPTOR], False)
#             triggerStruct = self._internalAttrs["%s_%s"
#                                                 % (attrName, TRIGGERED)]
#             self.warn_stream("Flag the autostop trigger for attribute %s"
#                              % (attrName))
#             triggerStruct[TRIGGERED] = True

        # done autostop area ---

        def __isHistoryBuffer(self, attrName):
            attrStruct = self._getAttrStruct(attrName)
            if attrStruct is not None and BASESET in attrStruct and \
                    type(attrStruct[READVALUE]) == HistoryBuffer:
                return True
            return False

        # def __buildHistoryBufferString(self, attrName):
        #     if self.__isHistoryBuffer(attrName):
        #         valuesList = self._getAttrStruct(attrName)[READVALUE].array
        #         self.debug_stream("For %s, building string list from %s"
        #                           % (attrName, valuesList))
        #         strList = []
        #         for value in valuesList:
        #             strList.append(self.__buildAttrMeaning(attrName, value))
        #         return strList
        #     return None

        # @AttrExc
        # def write_internal_attr(self, attr):
        #     '''this is referencing to a device attribute that doesn't
        #        have plc representation'''
        #     self.warn_stream("DEPRECATED: write_internal_attr(%s)"
        #                      % (attr.get_name()))
        #     if self.get_state() == PyTango.DevState.FAULT or \
        #             not self.has_data_available():
        #         return  # raise AttributeError("Not available in fault state!")
        #     attrName = attr.get_name()
        #     self.info_stream('write_internal_attr(%s)' % (attrName))
        #
        #     data = []
        #     attr.get_write_value(data)
        #     # FIXME: some cases must not allow values <= 0 ---
        #     if attrName in self._internalAttrs:
        #         attrDescr = self._internalAttrs[attrName]
        #         if WRITEVALUE in attrDescr:
        #             attrDescr[WRITEVALUE] = data[0]
        #             if attrDescr[TYPE] in [PyTango.DevDouble,
        #                                    PyTango.DevFloat]:
        #                 attrValue = float(data[0])
        #             elif attrDescr[TYPE] in [PyTango.DevBoolean]:
        #                 attrValue = bool(data[0])
        #             attrDescr[READVALUE] = attrValue
        #             attrQuality = self.\
        #                 __buildAttrQuality(attrName, attrDescr[READVALUE])
        #             attrDescr.store(attrDescr[WRITEVALUE])
        #             if EVENTS in attrDescr:
        #                 self.fireEventsList([[attrName, attrValue,
        #                                       attrQuality]], log=True)

        def loadAttrFile(self):
            self.attr_loaded = True
            if self.AttrFile:
                attr_fname = self.AttrFile
            else:
                attr_fname = self.get_name().split('/')[-1]+'.py'
            try:
                self.attr_list.build(attr_fname.lower())
            except Exception as e:
                if self.get_state() != PyTango.DevState.FAULT:
                    self.set_state(PyTango.DevState.FAULT)
                    self.set_status("ReloadAttrFile() failed (%s)" % (e),
                                    important=True)

        @AttrExc
        def read_lastUpdateStatus(self, attr):
            '''
            '''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            attr.set_value(self.read_lastUpdateStatus_attr)

        @AttrExc
        def read_lastUpdate(self, attr):
            '''
            '''
            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            attr.set_value(self.read_lastUpdate_attr)

        # Done Write Attr method for dynattrs ---

        # PROTECTED REGION END --- LinacData.global_variables

        def __init__(self, cl, name):
                PyTango.Device_4Impl.__init__(self, cl, name)
                self.log = self.get_logger()
                LinacData.init_device(self)

        def delete_device(self):
                self.info_stream('deleting device '+self.get_name())
                self._plcUpdateJoiner.set()
                self._tangoEventsJoiner.set()
                self._newDataAvailable.set()
                self.attr_list.remove_all()

        def init_device(self):
            try:
                self.debug_stream("In "+self.get_name()+"::init_device()")
                self.set_change_event('State', True, False)
                self.set_change_event('Status', True, False)
                self.attr_IsSayAgainEnable_read = False
                self.attr_IsTooFarEnable_read = True
                self.attr_forceWriteDB_read = ""
                self.attr_cpu_percent_read = 0.0
                self.attr_mem_percent_read = 0.0
                self.attr_mem_rss_read = 0
                self.attr_mem_swap_read = 0
                # The attributes Locking, Lock_ST, and HeartBeat have also
                # events but this call is made in each of the AttrList method
                # who dynamically build them.
                self.set_state(PyTango.DevState.INIT)
                self.set_status('inititalizing...')
                self.get_device_properties(self.get_device_class())
                self.debug_stream('AttrFile='+str(self.AttrFile))
                self._locals = {'self': self}
                self._globals = globals()
                # String with human infomation about the last update
                self.read_lastUpdateStatus_attr = ""
                attr = PyTango.Attr('lastUpdateStatus',
                                    PyTango.DevString, PyTango.READ)
                attrProp = PyTango.UserDefaultAttrProp()
                attrProp.set_label('Last Update Status')
                attr.set_default_properties(attrProp)
                self.add_attribute(attr, r_meth=self.read_lastUpdateStatus)
                self.set_change_event('lastUpdateStatus', True, False)
                # numeric attr about the lapsed time of the last update
                self.read_lastUpdate_attr = None
                attr = PyTango.Attr('lastUpdate',
                                    PyTango.DevDouble, PyTango.READ)
                attrProp = PyTango.UserDefaultAttrProp()
                attrProp.set_format(latin1('%f'))
                attrProp.set_label('Last Update')
                attrProp.set_unit('s')
                attr.set_default_properties(attrProp)
                self.add_attribute(attr, r_meth=self.read_lastUpdate)
                self.set_change_event('lastUpdate', True, False)

                self._process = psutil.Process()

                self.attr_list = AttrList(self)

                ########
                # region to setup the network communication parameters

                # restrictions and rename of PLC's ip address
                if self.IpAddress == '' and self.PlcAddress == '':
                    self.error_stream("The PLC ip address must be set")
                    self.set_state(PyTango.DevState.FAULT)
                    self.set_status("Please set the PlcAddress property",
                                    important=True)
                    return
                elif not self.IpAddress == '' and self.PlcAddress == '':
                    self.warn_stream("Deprecated property IpAddress, "
                                     "please use PlcAddress")
                    self.PlcAddress = self.IpAddress
                elif not self.IpAddress == '' and not self.PlcAddress == '' \
                        and not self.IpAddress == self.PlcAddress:
                    self.warn_stream("Both PlcAddress and IpAddress "
                                     "properties are defined and with "
                                     "different values, prevail PlcAddress")

                # get the ip address of the host where the device is running
                # this to know if the device is running in local or remote
                thisHostIp = get_ip()
                if not thisHostIp == self.BindAddress:
                    if not self.BindAddress == '':
                        self.warn_stream("BindAddress property defined but "
                                         "deprecated and it doesn't match "
                                         "with the host where device runs. "
                                         "Overwrite BindAddress with '%s'"
                                         % thisHostIp)
                    else:
                        self.debug_stream("BindAddress of this host '%s'"
                                          % (thisHostIp))
                    self.BindAddress = thisHostIp

                # check if the port corresponds to local and remote modes
                if thisHostIp == self.LocalAddress:
                    self.info_stream('Connection to the PLC will be '
                                     'local mode')
                    self.set_status('Connection in local mode', important=True)
                    self._deviceIsInLocal = True
                    self._deviceIsInRemote = False
                    try:
                        if self.LocalPort is not None:
                            self.info_stream('Using specified local port %s'
                                             % (self.LocalPort))
                            self.Port = self.LocalPort
                        else:
                            self.warn_stream('Local port not specified, '
                                             'trying to use deprecated '
                                             'definition')
                            if self.Port > 2010:
                                self.Port -= 10
                                self.warn_stream('converted the port to local'
                                                 ' %s' % self.Port)
                    except:
                        self.error_stream('Error in the port setting')
                elif thisHostIp == self.RemoteAddress:
                    self.info_stream('Connection to the PLC with be '
                                     'remote mode')
                    self.set_status('Connection in remote mode',
                                    important=True)
                    self._deviceIsInLocal = False
                    self._deviceIsInRemote = True
                    try:
                        if self.RemotePort is not None:
                            self.info_stream('Using specified remote port %s'
                                             % (self.RemotePort))
                            self.Port = self.RemotePort
                        else:
                            self.warn_stream('Remote port not specified, '
                                             'trying to use deprecated '
                                             'definition')
                            if self.Port < 2010:
                                self.Port += 10
                                self.warn_stream('converted the port to '
                                                 'remote %s'
                                                 % (self.RemotePort))
                    except:
                        self.error_stream('Error in the port setting')
                else:
                    self.warn_stream('Unrecognized IP for local/remote '
                                     'modes (%s)' % thisHostIp)
                    self.set_status('Unrecognized connection for local/remote'
                                    ' mode', important=True)
                    self._deviceIsInLocal = False
                    self._deviceIsInRemote = False

                # restrictions and renames of the Port's properties
                if self.Port is None:
                    self.debug_stream("The PLC ip port must be set")
                    self.set_state(PyTango.DevState.FAULT)
                    self.set_status("Please set the plc ip port",
                                    important=True)
                    return

                # end the region to setup the network communication parameters
                ########

                if self.ReadSize <= 0 or self.WriteSize <= 0:
                    self.set_state(PyTango.DevState.FAULT)
                    self.set_status("Block Read/Write sizes not well "
                                    "set (r=%d,w=%d)" % (self.ReadSize,
                                                         self.WriteSize),
                                    important=True)
                    return

                # true when reading some attribute failed....
                self.tainted = ''
                # where the readback of the set points begins
                self.offset_sp = self.ReadSize-self.WriteSize

                self.attr_loaded = False
                self.last_update_time = time.time()

                try:
                    self.connect()
                except Exception:
                    traceback.print_exc()
                    self.disconnect()
                    self.set_state(PyTango.DevState.UNKNOWN)
                self.info_stream('initialized')
                # self.set_state(PyTango.DevState.UNKNOWN)

                self._threadingBuilder()
            except Exception:
                self.error_stream('initialization failed')
                self.debug_stream(traceback.format_exc())
                self.set_state(PyTango.DevState.FAULT)
                self.set_status(traceback.format_exc())

        # --------------------------------------------------------------------
        #    LinacData read/write attribute methods
        # --------------------------------------------------------------------

        # PROTECTED REGION ID(LinacData.initialize_dynamic_attributes) ---
        def initialize_dynamic_attributes(self):
            self.loadAttrFile()
            self.attr_list._fileParsed.wait()
            self.info_stream("with all the attributes build, proceed...")

        # PROTECTED REGION END --- LinacData.initialize_dynamic_attributes

        # ------------------------------------------------------------------
        #    Read EventsTime attribute
        # ------------------------------------------------------------------
        def read_EventsTime(self, attr):
            # self.debug_stream("In " + self.get_name() + ".read_EventsTime()")
            # PROTECTED REGION ID(LinacData.EventsTime_read) --
            self.attr_EventsTime_read = self._tangoEventsTime.array
            # PROTECTED REGION END --- LinacData.EventsTime_read
            attr.set_value(self.attr_EventsTime_read)

        # ------------------------------------------------------------------
        #    Read EventsTimeMix attribute
        # ------------------------------------------------------------------
        def read_EventsTimeMin(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsTimeMin()")
            # PROTECTED REGION ID(LinacData.EventsTimeMin_read) --
            self.attr_EventsTimeMin_read = self._tangoEventsTime.array.min()
            if self._tangoEventsTime.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsTimeMin_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            # PROTECTED REGION END --- LinacData.EventsTimeMin_read
            attr.set_value(self.attr_EventsTimeMin_read)

        # ------------------------------------------------------------------
        #    Read EventsTimeMax attribute
        # ------------------------------------------------------------------
        def read_EventsTimeMax(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsTimeMax()")
            # PROTECTED REGION ID(LinacData.EventsTimeMax_read) --
            self.attr_EventsTimeMax_read = self._tangoEventsTime.array.max()
            if self._tangoEventsTime.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsTimeMax_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            elif self.attr_EventsTimeMax_read >= self._getPlcUpdatePeriod()*3:
                attr.set_value_date_quality(self.attr_EventsTimeMax_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_WARNING)
                return
            # PROTECTED REGION END --- LinacData.EventsTimeMax_read
            attr.set_value(self.attr_EventsTimeMax_read)

        # ------------------------------------------------------------------
        #    Read EventsTimeMean attribute
        # ------------------------------------------------------------------
        def read_EventsTimeMean(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsTimeMean()")
            # PROTECTED REGION ID(LinacData.EventsTimeMean_read) --
            self.attr_EventsTimeMean_read = self._tangoEventsTime.array.mean()
            if self._tangoEventsTime.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsTimeMean_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            elif self.attr_EventsTimeMean_read >= self._getPlcUpdatePeriod():
                attr.set_value_date_quality(self.attr_EventsTimeMean_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_WARNING)
                return
            # PROTECTED REGION END --- LinacData.EventsTimeMean_read
            attr.set_value(self.attr_EventsTimeMean_read)

        # ------------------------------------------------------------------
        #    Read EventsTimeStd attribute
        # ------------------------------------------------------------------
        def read_EventsTimeStd(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsTimeStd()")
            # PROTECTED REGION ID(LinacData.EventsTimeStd_read) --
            self.attr_EventsTimeStd_read = self._tangoEventsTime.array.std()
            if self._tangoEventsTime.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsTimeStd_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            # PROTECTED REGION END --- LinacData.EventsTimeStd_read
            attr.set_value(self.attr_EventsTimeStd_read)

        # ------------------------------------------------------------------
        #    Read EventsNumber attribute
        # ------------------------------------------------------------------
        def read_EventsNumber(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsNumber()")
            # PROTECTED REGION ID(LinacData.EventsNumber_read) ---
            self.attr_EventsNumber_read = self._tangoEventsNumber.array
            # PROTECTED REGION END --- LinacData.EventsNumber_read
            attr.set_value(self.attr_EventsNumber_read)

        # ------------------------------------------------------------------
        #    Read EventsNumberMin attribute
        # ------------------------------------------------------------------
        def read_EventsNumberMin(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsNumberMin()")
            # PROTECTED REGION ID(LinacData.EventsNumberMin_read) ---
            self.attr_EventsNumberMin_read = \
                int(self._tangoEventsNumber.array.min())
            if self._tangoEventsNumber.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsNumberMin_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            # PROTECTED REGION END --- LinacData.EventsNumberMin_read
            attr.set_value(self.attr_EventsNumberMin_read)

        # ------------------------------------------------------------------
        #    Read EventsNumberMax attribute
        # ------------------------------------------------------------------
        def read_EventsNumberMax(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsNumberMax()")
            # PROTECTED REGION ID(LinacData.EventsNumberMax_read) ---
            self.attr_EventsNumberMax_read = \
                int(self._tangoEventsNumber.array.max())
            if self._tangoEventsNumber.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsNumberMax_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            # PROTECTED REGION END --- LinacData.EventsNumberMax_read
            attr.set_value(self.attr_EventsNumberMax_read)

        # ------------------------------------------------------------------
        #    Read EventsNumberMean attribute
        # ------------------------------------------------------------------
        def read_EventsNumberMean(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsNumberMean()")
            # PROTECTED REGION ID(LinacData.EventsNumberMean_read) ---
            self.attr_EventsNumberMean_read = \
                self._tangoEventsNumber.array.mean()
            if self._tangoEventsNumber.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsNumberMean_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            # PROTECTED REGION END --- LinacData.EventsNumberMean_read
            attr.set_value(self.attr_EventsNumberMean_read)

        # ------------------------------------------------------------------
        #    Read EventsNumberStd attribute
        # ------------------------------------------------------------------
        def read_EventsNumberStd(self, attr):
            # self.debug_stream("In " + self.get_name() +
            #                   ".read_EventsNumberStd()")
            # PROTECTED REGION ID(LinacData.EventsNumberStd_read) ---
            self.attr_EventsNumberStd_read = \
                self._tangoEventsNumber.array.std()
            if self._tangoEventsNumber.array.size < HISTORY_EVENT_BUFFER:
                attr.set_value_date_quality(self.attr_EventsNumberStd_read,
                                            time.time(),
                                            PyTango.AttrQuality.ATTR_CHANGING)
                return
            # PROTECTED REGION END --- LinacData.EventsNumberStd_read
            attr.set_value(self.attr_EventsNumberStd_read)

        # ------------------------------------------------------------------
        #    Read IsTooFarEnable attribute
        # ------------------------------------------------------------------
        def read_IsTooFarEnable(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".read_IsTooFarEnable()")
            # PROTECTED REGION ID(LinacData.IsTooFarEnable_read) ---

            # PROTECTED REGION END --- LinacData.IsTooFarEnable_read
            attr.set_value(self.attr_IsTooFarEnable_read)

        # ------------------------------------------------------------------
        #    Write IsTooFarEnable attribute
        # ------------------------------------------------------------------
        def write_IsTooFarEnable(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".write_IsTooFarEnable()")
            data = attr.get_write_value()
            # PROTECTED REGION ID(LinacData.IsTooFarEnable_write) ---
            self.attr_IsTooFarEnable_read = bool(data)
            # PROTECTED REGION END -- LinacData.IsTooFarEnable_write

        # ------------------------------------------------------------------
        #    Read forceWriteDB attribute
        # ------------------------------------------------------------------
        def read_forceWriteDB(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".read_forceWriteDB()")
            # PROTECTED REGION ID(LinacData.forceWriteDB_read) ---

            # PROTECTED REGION END --- LinacData.forceWriteDB_read
            attr.set_value(self.attr_forceWriteDB_read)


        # ------------------------------------------------------------------
        #    Read cpu_percent attribute
        # ------------------------------------------------------------------
        def read_cpu_percent(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".read_cpu_percent()")
            # PROTECTED REGION ID(LinacData.cpu_percent_read) ---
            self.attr_cpu_percent_read = self._process.cpu_percent()
            # PROTECTED REGION END --- LinacData.cpu_percent_read
            attr.set_value(self.attr_cpu_percent_read)

        # ------------------------------------------------------------------
        #    Read mem_percent attribute
        # ------------------------------------------------------------------
        def read_mem_percent(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".read_mem_percent()")
            # PROTECTED REGION ID(LinacData.mem_percent_read) ---
            self.attr_mem_percent_read = self._process.memory_percent()
            # PROTECTED REGION END --- LinacData.mem_percent_read
            attr.set_value(self.attr_mem_percent_read)

        # ------------------------------------------------------------------
        #    Read mem_rss attribute
        # ------------------------------------------------------------------
        def read_mem_rss(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".read_mem_rss()")
            # PROTECTED REGION ID(LinacData.mem_rss_read) ---
            self.attr_mem_rss_read = self._process.memory_info().rss
            # PROTECTED REGION END --- LinacData.mem_rss_read
            attr.set_value(self.attr_mem_rss_read)

        # ------------------------------------------------------------------
        #    Read mem_swap attribute
        # ------------------------------------------------------------------
        def read_mem_swap(self, attr):
            self.debug_stream("In " + self.get_name() +
                              ".read_mem_swap()")
            # PROTECTED REGION ID(LinacData.mem_swap_read) ---
            self.attr_mem_swap_read = self._process.memory_full_info().swap
            # PROTECTED REGION END --- LinacData.mem_swap_read
            attr.set_value(self.attr_mem_swap_read)

        # ---------------------------------------------------------------------
        #    LinacData command methods
        # ---------------------------------------------------------------------
        @CommandExc
        def ReloadAttrFile(self):
            """Reload the file containing the attr description for a
               particular plc

            :param argin:
            :type: PyTango.DevVoid
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In ReloadAttrFile()')
            # PROTECTED REGION ID(LinacData.ReloadAttrFile) ---
            self.loadAttrFile()
            # PROTECTED REGION END --- LinacData.ReloadAttrFile

        @CommandExc
        def Exec(self, cmd):
            """ Direct command to execute python with in the device, use it
                very carefully it's good for debuging but it's a security
                thread.

            :param argin:
            :type: PyTango.DevString
            :return:
            :rtype: PyTango.DevString """
            self.debug_stream('In Exec()')
            # PROTECTED REGION ID(LinacData.Exec) ---
            L = self._locals
            G = self._globals
            try:
                try:
                    # interpretation as expression
                    result = eval(cmd, G, L)
                except SyntaxError:
                    # interpretation as statement
                    exec cmd in G, L
                    result = L.get("y")

            except Exception as exc:
                # handles errors on both eval and exec level
                result = exc

            if type(result) == StringType:
                return result
            elif isinstance(result, BaseException):
                return "%s!\n%s" % (result.__class__.__name__, str(result))
            else:
                return pprint.pformat(result)
            # PROTECTED REGION END --- LinacData.Exec

        @CommandExc
        def GetBit(self, args):
            """ Command to direct Read a bit position from the PLC memory

            :param argin:
            :type: PyTango.DevVarShortArray
            :return:
            :rtype: PyTango.DevBoolean """
            self.debug_stream('In GetBit()')
            # PROTECTED REGION ID(LinacData.GetBit) ---
            idx, bitno = args
            if self.read_db is not None and hasattr(self.read_db, 'bit'):
                return self.read_db.bit(idx, bitno)
            raise IOError("No access to the hardware")
            # PROTECTED REGION END --- LinacData.GetBit

        @CommandExc
        def GetByte(self, idx):
            """Command to direct Read a byte position from the PLC memory

            :param argin:
            :type: PyTango.DevShort
            :return:
            :rtype: PyTango.DevShort """
            self.debug_stream('In GetByte()')
            # PROTECTED REGION ID(LinacData.GetByte) ---
            if self.read_db is not None and hasattr(self.read_db, 'b'):
                return self.read_db.b(idx)
            raise IOError("No access to the hardware")
            # PROTECTED REGION END --- LinacData.GetByte

        @CommandExc
        def GetShort(self, idx):
            """Command to direct Read two consecutive byte positions from the
               PLC memory and understand it as an integer

            :param argin:
            :type: PyTango.DevShort
            :return:
            :rtype: PyTango.DevShort """
            self.debug_stream('In GetShort()')
            # PROTECTED REGION ID(LinacData.GetShort)  ---
            if self.read_db is not None and hasattr(self.read_db, 'i16'):
                return self.read_db.i16(idx)
            raise IOError("No access to the hardware")
            # PROTECTED REGION END --- LinacBData.GetShort

        @CommandExc
        def GetFloat(self, idx):
            """ Command to direct Read four consecutive byte positions from the
                PLC memory and understand it as an float

            :param argin:
            :type: PyTango.DevShort
            :return:
            :rtype: PyTango.DevFloat """
            self.debug_stream('In GetFloat()')
            # PROTECTED REGION ID(LinacData.GetFloat) ---
            if self.read_db is not None and hasattr(self.read_db, 'f'):
                return self.read_db.f(idx)
            raise IOError("No access to the hardware")
            # PROTECTED REGION END --- LinacData.GetFloat

        @CommandExc
        def HexDump(self):
            """ Hexadecimal dump of all the registers in the plc

            :param argin:
            :type: PyTango.DevVoid
            :return:
            :rtype: PyTango.DevString """
            self.debug_stream('In HexDump()')
            # PROTECTED REGION ID(LinacData.HexDump) ---
            rblock = self.read_db.buf[:]
            wblock = self.write_db.buf[self.write_db.write_start:]
            return hex_dump([rblock, wblock])
            # PROTECTED REGION END --- LinacData.HexDump

        @CommandExc
        def Hex(self, idx):
            """ Hexadecimal dump the given register of the plc

            :param argin:
            :type: PyTango.DevShort
            :return:
            :rtype: PyTango.DevString """
            self.debug_stream('In Hex()')
            # PROTECTED REGION ID(LinacData.Hex) ---
            return hex(self.read_db.b(idx))
            # PROTECTED REGION END --- LinacData.Hex

        @CommandExc
        def DumpTo(self, arg):
            """ Hexadecimal dump of all the registers in the plc to a file

            :param argin:
            :type: PyTango.DevString
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In DumpTo()')
            # PROTECTED REGION ID(LinacData.DumpTo) ---
            fout = open(arg, 'w')
            fout.write(self.read_db.buf.tostring())
            # PROTECTED REGION END --- LinacData.DumpTo

        @CommandExc
        def WriteBit(self, args):
            """ Write a single bit in the memory of the plc [reg,bit,value]

            :param argin:
            :type: PyTango.DevVarShortArray
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In WriteBit()')
            # PROTECTED REGION ID(LinacData.WriteBit) ---
            idx, bitno, v = args
            idx += bitno / 8
            bitno %= 8
            v = bool(v)
            b = self.write_db.b(idx)  # Get the byte where the bit is
            b = b & ~(1 << bitno) | (v << bitno)
            # change only the expected bit
            # The write operation of a bit, writes the Byte where it is
            self.write_db.write(idx, b, TYPE_MAP[PyTango.DevUChar])
            # PROTECTED REGION END --- LinacData.WriteBit

        @CommandExc
        def WriteByte(self, args):
            """ Write a byte in the memory of the plc [reg,value]

            :param argin:
            :type: PyTango.DevVarShortArray
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In WriteByte()')
            # PROTECTED REGION ID(LinacData.WriteByte) ---
            # args[1] = c_uint8(args[1])
            register = args[0]
            value = uint8(args[1])
            # self.write_db.write( *args )
            self.write_db.write(register, value, TYPE_MAP[PyTango.DevUChar])
            # PROTECTED REGION END --- LinacData.WriteByte

        @CommandExc
        def WriteShort(self, args):
            """ Write two consecutive bytes in the memory of the plc
               [reg,value]

            :param argin:
            :type: PyTango.DevVarShortArray
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In WriteShort()')
            # PROTECTED REGION ID(LinacData.WriteShort) ---
            # args[1] = c_int16(args[1])
            register = args[0]
            value = int16(args[1])
            # self.write_db.write( *args )
            self.write_db.write(register, value, TYPE_MAP[PyTango.DevShort])
            # PROTECTED REGION END --- LinacData.WriteShort

        @CommandExc
        def WriteFloat(self, args):
            """ Write the representation of a float in four consecutive bytes
                in the memory of the plc [reg,value]

            :param argin:
            :type: PyTango.DevVarShortArray
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In WriteFloat()')
            # PROTECTED REGION ID(LinacData.WriteFloat) ---
            idx = int(args[0])
            f = float32(args[1])
            self.write_db.write(idx, f, TYPE_MAP[PyTango.DevFloat])
            # PROTECTED REGION END --- LinacData.WriteFloat

        @CommandExc
        def ResetState(self):
            """ Clean the information set in the Status message and restore
                the state

            :param argin:
            :type: PyTango.DevVoid
            :return:
            :rtype: PyTango.DevVoid """
            self.debug_stream('In ResetState()')
            # PROTECTED REGION ID(LinacData.ResetState) ---
            self.info_stream('resetting state %s...' % str(self.get_state()))
            if self.get_state() == PyTango.DevState.FAULT:
                if self.disconnect():
                    self.set_state(PyTango.DevState.OFF)  # self.connect()
            elif self.is_connected():
                self.set_state(PyTango.DevState.ON)
                self.clean_status()
            else:
                self.set_state(PyTango.DevState.UNKNOWN)
                self.set_status("")
            # PROTECTED REGION END --- LinacData.ResetState

        @CommandExc
        def RestoreReadDB(self):
            self.forceWriteAttrs()

        # To be moved ---
        def _threadingBuilder(self):
            # Threading joiners ---
            self._plcUpdateJoiner = threading.Event()
            self._plcUpdateJoiner.clear()
            self._tangoEventsJoiner = threading.Event()
            self._tangoEventsJoiner.clear()
            # Threads declaration ---
            self._plcUpdateThread = \
                threading.Thread(name="PlcUpdater",
                                 target=self.plcUpdaterThread)
            self._tangoEventsThread = \
                threading.Thread(name="EventManager",
                                 target=self.newValuesThread)
            self._tangoEventsTime = \
                CircularBuffer([], maxlen=HISTORY_EVENT_BUFFER, owner=None)
            self._tangoEventsNumber = \
                CircularBuffer([], maxlen=HISTORY_EVENT_BUFFER, owner=None)
            # Threads configuration ---
            self._plcUpdateThread.setDaemon(True)
            self._tangoEventsThread.setDaemon(True)
            self._plcUpdatePeriod = PLC_MAX_UPDATE_PERIOD
            self._newDataAvailable = threading.Event()
            self._newDataAvailable.clear()
            # Launch those threads ---
            self._plcUpdateThread.start()
            self._tangoEventsThread.start()

        def plcUpdaterThread(self):
            '''
            '''
            while not self._plcUpdateJoiner.isSet():
                try:
                    start_t = time.time()
                    if self.is_connected():
                        self._readPlcRegisters()
                        self._addaptPeriod(time.time()-start_t)
                    else:
                        if self._plcUpdateJoiner.isSet():
                            return
                        self.info_stream('plc not connected')
                        self.reconnect()
                        time.sleep(self.ReconnectWait)
                except Exception as e:
                    self.error_stream("In plcUpdaterThread() "
                                      "exception: %s" % (e))
                    traceback.print_exc()

        def _readPlcRegisters(self):
            """ Do a read of all the registers in the plc and update the
                mirrored memory

            :param argin:
            :type: PyTango.DevVoid
            :return:
            :rtype: PyTango.DevVoid """

            # faults are critical and can not be recovered by restarting things
            # INIT states mean something is going is on that interferes with
            #      updating, such as connecting
            start_update_time = time.time()
            if (self.get_state() == PyTango.DevState.FAULT) or \
                    not self.is_connected():
                if start_update_time - self.last_update_time \
                        < self.ReconnectWait:
                    return
                else:
                    if self.connect():
                        self.set_state(PyTango.DevState.UNKNOWN)
                    return
            # relock if auto-recover from fault ---
            try:
                self.auto_local_lock()
                self.dataBlockSemaphore.acquire()
                try:
                    e = None
                    # The real reading to the hardware:
                    up = self.read_db.readall()
                except Exception as e:
                    self.error_stream(
                        "Could not complete the readall()\n%s" % (e))
                finally:
                    self.dataBlockSemaphore.release()
                    if e is not None:
                        raise e
                if up:
                    self.last_update_time = time.time()
                    if self.get_state() == PyTango.DevState.ALARM:
                        # This warning would be because attributes with
                        # this quality, don't log because it happens too often.
                        self.set_state(PyTango.DevState.ON, log=False)
                    if not self.get_state() in [PyTango.DevState.ON]:
                        # Recover a ON state when it is responding and the
                        # state was showing something different.
                        self.set_state(PyTango.DevState.ON)
                else:
                    self.set_state(PyTango.DevState.FAULT)
                    self.set_status("No data received from the PLC")
                    self.disconnect()
                end_update_t = time.time()
                diff_t = (end_update_t - start_update_time)
                if end_update_t-self.last_update_time > self.TimeoutAlarm:
                    self.set_state(PyTango.DevState.ALARM)
                    self.set_status("Timeout alarm!")
                    return
                # disconnect if no new information is send after long time
                if end_update_t-self.last_update_time > self.TimeoutConnection:
                    self.disconnect()
                    self.set_state(PyTango.DevState.FAULT)
                    self.set_status("Timeout connection!")
                    return
                self.read_lastUpdate_attr = diff_t
                timeFormated = time.strftime('%F %T')
                self.read_lastUpdateStatus_attr = "last updated at %s in %f s"\
                                                  % (timeFormated, diff_t)
                attr2Event = [['lastUpdate', self.read_lastUpdate_attr],
                              ['lastUpdateStatus',
                               self.read_lastUpdateStatus_attr]]
                self.fireEventsList(attr2Event,
                                    timestamp=self.last_update_time)
                self._newDataAvailable.set()
                # when an update goes fine, the period is reduced one step
                # until the minumum
                if self._getPlcUpdatePeriod() > PLC_MIN_UPDATE_PERIOD:
                    self._setPlcUpdatePeriod(self._plcUpdatePeriod -
                                             PLC_STEP_UPDATE_PERIOD)
            except tcpblock.Shutdown as exc:
                self.set_state(PyTango.DevState.FAULT)
                msg = 'communication shutdown requested '\
                      'at '+time.strftime('%F %T')
                self.set_status(msg)
                self.error_stream(msg)
                self.disconnect()
            except socket.error as exc:
                self.set_state(PyTango.DevState.FAULT)
                msg = 'broken socket at %s\n%s' % (time.strftime('%F %T'),
                                                   str(exc))
                self.set_status(msg)
                self.error_stream(msg)
                self.disconnect()
            except Exception as exc:
                self.set_state(PyTango.DevState.FAULT)
                msg = 'update failed at %s\n%s: %s' % (time.strftime('%F %T'),
                                                       str(type(exc)),
                                                       str(exc))
                self.set_status(msg)
                self.error_stream(msg)
                self.disconnect()
                self.last_update_time = time.time()
                traceback.print_exc()

        def _addaptPeriod(self, diff_t):
            current_p = self._getPlcUpdatePeriod()
            max_t = PLC_MAX_UPDATE_PERIOD
            step_t = PLC_STEP_UPDATE_PERIOD
            if diff_t > max_t:
                if current_p < max_t:
                    self.warn_stream(
                        "plcUpdaterThread() has take too much time "
                        "(%3.3f seconds)" % (diff_t))
                    self._setPlcUpdatePeriod(current_p+step_t)
                else:
                    self.error_stream(
                        "plcUpdaterThread() has take too much time "
                        "(%3.3f seconds), but period cannot be increased more "
                        "than %3.3f seconds" % (diff_t, current_p))
            elif diff_t > current_p:
                exceed_t = diff_t-current_p
                factor = int(exceed_t/step_t)
                increment_t = step_t+(step_t*factor)
                if current_p+increment_t >= max_t:
                    self.error_stream(
                        "plcUpdaterThread() it has take %3.6f seconds "
                        "(%3.6f more than expected) and period will be "
                        "increased to the maximum (%3.6f)"
                        % (diff_t, exceed_t, max_t))
                    self._setPlcUpdatePeriod(max_t)
                else:
                    self.warn_stream(
                        "plcUpdaterThread() it has take %3.6f seconds, "
                        "%f over the expected, increase period "
                        "(%3.3f + %3.3f seconds)" % (diff_t, exceed_t,
                                                     current_p, increment_t))
                    self._setPlcUpdatePeriod(current_p+increment_t)
            else:
                # self.debug_stream(
                #     "plcUpdaterThread() it has take %3.6f seconds, going to "
                #     "sleep %3.3f seconds (update period %3.3f seconds)"
                #     % (diff_t, current_p-diff_t, current_p))
                time.sleep(current_p-diff_t)

        def newValuesThread(self):
            '''
            '''
            if not self.attr_list._fileParsed.isSet():
                self.info_stream("Event generator thread will wait until "
                                 "file is parsed")
            self.attr_list._fileParsed.wait()
            while not self.has_data_available():
                time.sleep(self._getPlcUpdatePeriod()*2)
                self.debug_stream("Event generator thread wait for connection")
            event_ctr = EventCtr()
            while not self._tangoEventsJoiner.isSet():
                try:
                    if self._newDataAvailable.isSet():
                        start_t = time.time()
                        self.propagateNewValues()
                        diff_t = time.time() - start_t
                        n_events = event_ctr.ctr
                        event_ctr.clear()
                        self._tangoEventsTime.append(diff_t)
                        self._tangoEventsNumber.append(n_events)
                        if n_events > 0:
                            self.debug_stream(
                                "newValuesThread() it has take %3.6f seconds "
                                "for %d events" % (diff_t, n_events))
                        self._newDataAvailable.clear()
                    else:
                        self._newDataAvailable.wait()
                except Exception as exc:
                    self.error_stream(
                        "In newValuesThread() exception: %s" % (exc))
                    traceback.print_exc()

        def propagateNewValues(self):
            """
Check the attributes that comes directly from the PLC registers, to check if
the information stored in the device needs to be refresh, events emitted, as
well as for each of them, inter-attribute dependencies are required to be
triggered.
            """
            attrs = self._plcAttrs.keys()[:]
            for attrName in attrs:
                attrStruct = self._plcAttrs[attrName]
                if hasattr(attrStruct, 'hardwareRead'):
                    attrStruct.hardwareRead(self.read_db)

#         def plcBasicAttrEvents(self):
#             '''This method is used, after all reading from the PLC to update
#                the most basic attributes to indicate everything is fine.
#                Those attributes are:
#                - lastUpdate{,Status}
#                - HeartBeat
#                - Lock_{ST,Status}
#                - Locking
#             '''
#             # Heartbit
#             if self.heartbeat_addr:
#                 self.read_heartbeat_attr =\
#                     self.read_db.bit(self.heartbeat_addr, 0)
#                 HeartBeatStruct = self._plcAttrs['HeartBeat']
#                 if not self.read_heartbeat_attr == HeartBeatStruct[READVALUE]:
#                     HeartBeatStruct[READTIME] = time.time()
#                     HeartBeatStruct[READVALUE] = self.read_heartbeat_attr
#             # Locks
#             if self.lock_ST:
#                 self.read_lock_ST_attr = self.read_db.get(self.lock_ST, 'B', 1)
#                 # lock_str, lock_quality = self.convert_Lock_ST()
#                 if self.read_lock_ST_attr not in [0, 1, 2]:
#                     self.warn_stream("<<<Invalid locker code %d>>>"
#                                      % (self.read_lock_ST_attr))
#                 Lock_STStruct = self._getAttrStruct('Lock_ST')
#                 if not self.read_lock_ST_attr == Lock_STStruct[READVALUE]:
#                     # or (now - Lock_STStruct[READTIME]) > PERIODIC_EVENT:
#                     Lock_STStruct[READTIME] = time.time()
#                     Lock_STStruct[READVALUE] = self.read_lock_ST_attr
#                 # Lock_StatusStruct = self._getAttrStruct('Lock_Status')
#                 # if not lock_str == Lock_StatusStruct[READVALUE]:
#                 #     or (now - Lock_StatusStruct[READTIME]) > PERIODIC_EVENT:
#                 #     Lock_StatusStruct[READTIME] = time.time()
#                 #     Lock_StatusStruct[READVALUE] = lock_str
#                 # locking = self.read_lock()
#                 LockingStruct = self._getAttrStruct('Locking')
#                 self._checkLocking()
#                 # if not self.is_lockedByTango == LockingStruct[READVALUE]:
#                 #     # or (now - LockingStruct[READTIME]) > PERIODIC_EVENT:
#                 #     LockingStruct[READTIME] = time.time()
#                 #     LockingStruct[READVALUE] = self.is_lockedByTango

#         def __attrHasEvents(self, attrName):
#             '''
#             '''
#             attrStruct = self._getAttrStruct(attrName)
#             if attrStruct._eventsObj:
#                 return True
#             return False
#             # if attrName in self._plcAttrs and \
#             #         EVENTS in self._plcAttrs[attrName]:
#             #     return True
#             # elif attrName in self._internalAttrs and \
#             #         EVENTS in self._internalAttrs[attrName].keys():
#             #     return True
#             # return False

#         def __getAttrReadValue(self, attrName):
#             '''
#             '''
#             attrStruct = self._getAttrStruct(attrName)
#             if READVALUE in attrStruct:
#                 if type(attrStruct[READVALUE]) == CircularBuffer:
#                     return attrStruct[READVALUE].value
#                 elif type(attrStruct[READVALUE]) == HistoryBuffer:
#                     return attrStruct[READVALUE].array
#                 return attrStruct[READVALUE]
#             return None



#         def __lastEventHasChangingQuality(self, attrName):
#             attrStruct = self._getAttrStruct(attrName)
#             if MEANINGS in attrStruct or ISRESET in attrStruct:
#                 # To these attributes this doesn't apply
#                 return False
#             if LASTEVENTQUALITY in attrStruct:
#                 if attrStruct[LASTEVENTQUALITY] == \
#                         PyTango.AttrQuality.ATTR_CHANGING:
#                     return True
#                 else:
#                     return False
#             else:
#                 return False
  
#         def __attrValueHasThreshold(self, attrName):
#             if EVENTS in self._getAttrStruct(attrName) and \
#                     THRESHOLD in self._getAttrStruct(attrName)[EVENTS]:
#                 return True
#             else:
#                 return False

        # def __isRstAttr(self, attrName):
        #     self.warn_stream("DEPRECATED: __isRstAttr(%s)" % (attrName))
        #     if attrName.startswith('lastUpdate'):
        #         return False
        #     if ISRESET in self._getAttrStruct(attrName):
        #         return self._getAttrStruct(attrName)[ISRESET]
        #     else:
        #         return False

#         def __checkAttrEmissionParams(self, attrName, newValue):
#             if not self.__attrHasEvents(attrName):
#                 self.warn_stream("No events for the attribute %s" % (attrName))
#                 return False
#             lastValue = self.__getAttrReadValue(attrName)
#             if lastValue is None:
#                 # If there is no previous read, it has to be emitted
#                 return True
#             # after that we know the values are different
#             if self.__isRstAttr(attrName):
#                 writeValue = self._getAttrStruct(attrName)[WRITEVALUE]
#                 rst_t = self._getAttrStruct(attrName)[RESETTIME]
#                 if newValue and not lastValue and writeValue and \
#                         rst_t is not None:
#                     return True
#                 elif not newValue and lastValue and not writeValue \
#                         and rst_t is None:
#                     return True
#                 else:
#                     return False
#             if self.__attrValueHasThreshold(attrName):
#                 diff = abs(lastValue - newValue)
#                 threshold = self._getAttrStruct(attrName)[EVENTS][THRESHOLD]
#                 if diff > threshold:
#                     return True
#                 elif self.__lastEventHasChangingQuality(attrName):
#                     # below the threshold and last quality changing is an
#                     # indicative that a movement has finish, then it's time
#                     # to emit an event with a quality valid.
#                     return True
#                 else:
#                     return False
#             if self.__isHistoryBuffer(attrName):
#                 if len(lastValue) == 0 or \
#                         newValue != lastValue[len(lastValue)-1]:
#                     return True
#                 else:
#                     return False
#             # At this point any special case has been treated, only avoid
#             # to emit if value doesn't change
#             if newValue != lastValue:
#                 return True
#             # when non case before, no event
#             return False

#         def plcGeneralAttrEvents(self):
#             '''This method is used to periodically loop to review the list of
#                attribute (above the basics) and check if they need event
#                emission.
#             '''
#             now = time.time()
#             # attributeList = []
#             # for attrName in self._plcAttrs.keys():
#             #     if attrName not in ['HeartBeat', 'Lock_ST', 'Lock_Status',
#             #                         'Locking']:
#             #         attributeList.append(attrName)
#             attributeList = self._plcAttrs.keys()
#             for exclude in ['HeartBeat', 'Lock_ST', 'Lock_Status', 'Locking']:
#                 if attributeList.count(exclude):
#                     attributeList.pop(attributeList.index(exclude))
#             # Iterate the remaining to know if they need something to be done
#             for attrName in attributeList:
#                 self.checkResetAttr(attrName)
#                 attrStruct = self._plcAttrs[attrName]
#                 if hasattr(attrStruct, 'hardwareRead'):
#                     attrStruct.hardwareRead(self.read_db)
#                 
#                 
#                 # First check if for this element, it's prepared for events
# #                 if self.__attrHasEvents(attrName):
# #                     try:
# #                         attrStruct = self._plcAttrs[attrName]
# #                         attrType = attrStruct[TYPE]
# #                         # lastValue = self.__getAttrReadValue(attrName)
# #                         last_read_t = attrStruct[READTIME]
# #                         if READADDR in attrStruct:
# #                             # read_addr = attrStruct[READADDR]
# #                             # if READBIT in attrStruct:
# #                             #     read_bit = attrStruct[READBIT]
# #                             #     newValue = self.read_db.bit(read_addr,
# #                             #                                 read_bit)
# #                             # else:
# #                             #     newValue = self.read_db.get(read_addr,
# #                             #                                 *attrType)
# #                             newValue = attrStruct.hardwareRead(self.read_db)
# #                             if FORMULA in attrStruct and \
# #                                     'read' in attrStruct[FORMULA]:
# #                                 newValue = \
# #                                     self.__solveFormula(attrName, newValue,
# #                                                         attrStruct[FORMULA]
# #                                                         ['read'])
# #                         if self.__checkAttrEmissionParams(attrName, newValue):
# #                             self.__applyReadValue(attrName, newValue,
# #                                                   self.last_update_time)
# #                             if MEANINGS in attrStruct:
# #                                 if BASESET in attrStruct:
# #                                     attrValue = attrStruct[READVALUE].array
# #                                 else:
# #                                     attrValue = \
# #                                         self.__buildAttrMeaning(attrName,
# #                                                                 newValue)
# #                                 attrQuality = \
# #                                     self.__buildAttrQuality(attrName, newValue)
# #                             elif QUALITIES in attrStruct:
# #                                 attrValue = newValue
# #                                 attrQuality = \
# #                                     self.__buildAttrQuality(attrName,
# #                                                             attrValue)
# #                             elif AUTOSTOP in attrStruct:
# #                                 attrValue = attrStruct[READVALUE].array
# #                                 attrQuality = PyTango.AttrQuality.ATTR_VALID
# #                                 self._checkAutoStopConditions(attrName)
# #                             else:
# #                                 attrValue = newValue
# #                                 attrQuality = PyTango.AttrQuality.ATTR_VALID
# #                             # store the current quality to know an end of
# #                             # a movement: quality from changing to valid
# #                             attrStruct[LASTEVENTQUALITY] = attrQuality
# #                             # collect to launch fire event
# #                             self.__doTraceAttr(attrName,
# #                                                "plcGeneralAttrEvents(%s)"
# #                                                % (attrValue))
# #                         # elif self.__checkEventReEmission(attrName):
# #                             #  Even there is no condition to emit an event
# #                             #  Check the RE_EVENTS_PERIOD to know if a refresh
# #                             #  would be nice
# #                         #     self.__eventReEmission(attrName)
# #                         #     attr2Reemit += 1
# #                     except Exception as e:
# #                         self.warn_stream("In plcGeneralAttrEvents(), "
# #                                          "exception in attribute %s: %s"
# #                                          % (attrName, e))
# #                         traceback.print_exc()
#             # if len(attr2Event) > 0:
#             #     self.fireEventsList(attr2Event, timestamp=now, log=True)
# #             if attr2Reemit > 0:
# #                 self.debug_stream("%d events due to periodic reemission"
# #                                   % attr2Reemit)
# #             self.debug_stream("plcGeneralAttrEvents(): %d events from %d "
# #                               "attributes" % (len(attr2Event),
# #                                               len(attributeList)))
 
#         def internalAttrEvents(self):
#             '''
#             '''
#             now = time.time()
#             attributeList = self._internalAttrs.keys()
#             attr2Event = []
#             for attrName in attributeList:
#                 if self.__attrHasEvents(attrName):
#                     try:
#                         # evaluate if emit is needed
#                         # internal attr types:
#                         # - logical
#                         # - sets
#                         attrStruct = self._getAttrStruct(attrName)
#                         attrType = attrStruct[TYPE]
#                         lastValue = self.__getAttrReadValue(attrName)
#                         last_read_t = attrStruct[READTIME]
#                         if LOGIC in attrStruct:
#                             # self.info_stream("Attribute %s is from logical "
#                             #                  "type"%(attrName))
#                             newValue = self._evalLogical(attrName)
#                         elif 'read_set' in attrStruct:
#                             # self.info_stream("Attribute %s is from group "
#                             #                  "type" % (attrName))
#                             newValue = \
#                                 self.__getGrpBitValue(attrName,
#                                                       attrStruct['read_set'],
#                                                       self.read_db)
#                         elif AUTOSTOP in attrStruct:
#                             newValue = lastValue
#                             # FIXME: do it better.
#                             # Don't emit events on the loop, because they shall
#                             # be only emitted when they are written.
#                             self._refreshInternalAutostopParams(attrName)
#                             # FIXME: this is task for a internalUpdaterThread
#                         elif MEAN in attrStruct or STD in attrStruct:
#                             # self._updateStatistic(attrName)
#                             newValue = attrStruct[READVALUE]
#                         elif TRIGGERED in attrStruct:
#                             newValue = attrStruct[TRIGGERED]
#                         elif isinstance(attrStruct, EnumerationAttr):
#                             newValue = lastValue  # avoid emit
#                         else:
#                             # self.warn_stream("In internalAttrEvents(): "
#                             #                  "unknown how to emit events "
#                             #                  "for %s attribute" % (attrName))
#                             newValue = lastValue
#                         emit = False
#                         if newValue != lastValue:
#                             # self.info_stream("Emit because %s!=%s"
#                             #                  % (str(newValue),
#                             #                     str(lastValue)))
#                             emit = True
#                         elif (last_read_t is None):
#                             # self.info_stream("Emit new value because it "
#                             #                  "wasn't read before")
#                             emit = True
#                         else:
#                             pass
#                             # self.info_stream("No event to emit "
#                             #                  "(lastValue %s (%s), "
#                             #                  "newValue %s)"
#                             #                  %(str(lastValue),
#                             #                    str(last_read_t),
#                             #                    str(newValue)))
#                     except Exception as e:
#                         self.error_stream("In internalAttrEvents(), "
#                                           "exception reading attribute %s: %s"
#                                           % (attrName, e))
#                         traceback.print_exc()
#                     else:
#                         # prepare to emit
#                         try:
#                             if emit:
#                                 self.__applyReadValue(attrName,
#                                                       newValue,
#                                                       self.last_update_time)
#                                 if MEANINGS in attrStruct:
#                                     attrValue = \
#                                         self.__buildAttrMeaning(attrName,
#                                                                 newValue)
#                                     attrQuality = \
#                                         self.__buildAttrQuality(attrName,
#                                                                 newValue)
#                                 elif QUALITIES in attrStruct:
#                                     attrValue = newValue
#                                     attrQuality = \
#                                         self.__buildAttrQuality(attrName,
#                                                                 attrValue)
#                                 else:
#                                     attrValue = newValue
#                                     attrQuality =\
#                                         PyTango.AttrQuality.ATTR_VALID
#                                 attr2Event.append([attrName, attrValue])
#                                 self.__doTraceAttr(attrName,
#                                                    "internalAttrEvents(%s)"
#                                                    % (attrValue))
#                         except Exception as e:
#                             self.error_stream("In internalAttrEvents(), "
#                                               "exception on emit attribute "
#                                               "%s: %s" % (attrName, e))
# #             if len(attr2Event) > 0:
# #                 self.fireEventsList(attr2Event, timestamp=now, log=True)
# #             self.debug_stream("internalAttrEvents(): %d events from %d "
# #                               "attributes" % (len(attr2Event),
# #                                               len(attributeList)))
#             return len(attr2Event)

        # def checkResetAttr(self, attrName):
        #     '''
        #     '''
        #     self.warn_stream("DEPRECATED: checkResetAttr(%s)" % (attrName))
        #     if not self.__isRstAttr(attrName):
        #         return
        #     # FIXME: ---
        #     # if this is moved to a new thread separated to the event
        #     # emit, the system must be changed to be passive waiting
        #     # (that it Threading.Event())
        #     if self.__isCleanResetNeed(attrName):
        #         self._plcAttrs[attrName][RESETTIME] = None
        #         readAddr = self._plcAttrs[attrName][READADDR]
        #         writeAddr = self._plcAttrs[attrName][WRITEADDR]
        #         writeBit = self._plcAttrs[attrName][WRITEBIT]
        #         writeValue = False
        #         self.__writeBit(attrName, readAddr,
        #                         writeAddr, writeBit, writeValue)
        #         self._plcAttrs[attrName][WRITEVALUE] = writeValue
        #         self.info_stream("Set back to 0 a RST attr %s" % (attrName))
        #         # self._plcAttrs[attrName][READVALUE] = False
        #         # self.fireEvent([attrName, False], time.time())

        # def __isCleanResetNeed(self, attrName):
        #     '''
        #     '''
        #     now = time.time()
        #     if self.__isResetAttr(attrName):
        #         read_value = self._plcAttrs[attrName][READVALUE]
        #         rst_t = self._plcAttrs[attrName][RESETTIME]
        #         if read_value and rst_t is not None:
        #             diff_t = now-rst_t
        #             if RESETACTIVE in self._plcAttrs[attrName]:
        #                 activeRst_t = self._plcAttrs[attrName][RESETACTIVE]
        #             else:
        #                 activeRst_t = ACTIVE_RESET_T
        #             if activeRst_t-diff_t < 0:
        #                 self.info_stream("Attribute %s needs clean reset"
        #                                  % (attrName))
        #                 return True
        #             self.info_stream("Do not clean reset flag yet for %s "
        #                              "(%6.3f seconds left)"
        #                              % (attrName, activeRst_t-diff_t))
        #     return False

        # def __isResetAttr(self, attrName):
        #     '''
        #     '''
        #     if attrName in self._plcAttrs and \
        #             ISRESET in self._plcAttrs[attrName] and \
        #             self._plcAttrs[attrName][ISRESET]:
        #         return True
        #     return False

        def auto_local_lock(self):
            if self._deviceIsInLocal:
                if 'Locking' in self._plcAttrs:
                    if not self._plcAttrs['Locking'].rvalue:
                        self.info_stream("Device is in Local mode and "
                                         "not locked. Proceed to lock it")
                        with self.dataBlockSemaphore:
                            self.relock()
                            time.sleep(self._getPlcUpdatePeriod())
                    # else:
                    #     self.info_stream("Device is in Local mode and locked")
                else:
                    self.warn_stream("Device in Local mode but 'Locking' "
                                     "attribute not yet present")
            # else:
            #     self.info_stream("Device is not in Local mode")

        def relock(self):
            '''
            '''
            if 'Locking' in self._plcAttrs and \
                    not self._plcAttrs['Locking'].wvalue:
                self.write_lock(True)
        # end "To be moved" section

        def write_lock(self, value):
            '''
            '''

            if self.get_state() == PyTango.DevState.FAULT or \
                    not self.has_data_available():
                return  # raise AttributeError("Not available in fault state!")
            if not isinstance(value, bool):
                raise ValueError("write_lock argument must be a boolean")
            if 'Locking' in self._plcAttrs:
                raddr = self._plcAttrs['Locking'].read_addr
                rbit = self._plcAttrs['Locking'].read_bit
                rbyte = self.read_db.b(raddr)
                waddr = self._plcAttrs['Locking'].write_bit
                if value:
                    # sets bit 'bitno' of b
                    toWrite = rbyte | (int(value) << rbit)
                    # a byte of 0s with a unique 1 in the place to set this 1
                else:
                    # clears bit 'bitno' of b
                    toWrite = rbyte & (0xFF) ^ (1 << rbit)
                    # a byte of 1s with a unique 0 in the place to set this 0
                self.write_db.write(waddr, toWrite, TYPE_MAP[PyTango.DevUChar])
                time.sleep(self._getPlcUpdatePeriod())
                reRead = self.read_db.b(raddr)
                self.info_stream("Writing Locking boolean to %s (%d.%d) byte "
                                  "was %s; write %s; now %s"
                                  % ("  lock" if value else "unlock",
                                     raddr, rbit, bin(rbyte), bin(toWrite),
                                     bin(reRead)))
                self._plcAttrs['Locking'].write_value = value

        @CommandExc
        def Update(self):
            '''Deprecated
            '''
            pass
            # PROTECTED REGION END --- LinacData.Update


# ==================================================================
#
#       LinacDataClass class definition
#
# ==================================================================
class LinacDataClass(PyTango.DeviceClass):
        # -------- Add you global class variables here ------------------------
        # PROTECTED REGION ID(LinacData.global_class_variables) ---

        # PROTECTED REGION END --- LinacData.global_class_variables

        def dyn_attr(self, dev_list):
            """Invoked to create dynamic attributes for the given devices.
            Default implementation calls
            :meth:`LinacData.initialize_dynamic_attributes` for each device

            :param dev_list: list of devices
            :type dev_list: :class:`PyTango.DeviceImpl`"""

            for dev in dev_list:
                try:
                    dev.initialize_dynamic_attributes()
                except:
                    dev.warn_stream("Failed to initialize dynamic attributes")
                    dev.debug_stream("Details: " + traceback.format_exc())
            # PROTECTED REGION ID(LinacData.dyn_attr) ENABLED START ---

            # PROTECTED REGION END --- LinacData.dyn_attr

        # Class Properties ---
        class_property_list = {}

        # Device Properties ---
        device_property_list = {'ReadSize': [PyTango.DevShort,
                                             "how many bytes to read (should "
                                             "be a multiple of 2)", 0
                                             ],
                                'WriteSize': [PyTango.DevShort,
                                              "size of write data block", 0],
                                'IpAddress': [PyTango.DevString,
                                              "ipaddress of linac PLC "
                                              "(deprecated)", ''],
                                'PlcAddress': [PyTango.DevString,
                                               "ipaddress of linac PLC", ''],
                                'Port': [PyTango.DevShort,
                                         "port of linac PLC (deprecated)",
                                         None],
                                'LocalPort': [PyTango.DevShort,
                                              "port of linac PLC (deprecated)",
                                              None],
                                'RemotePort': [PyTango.DevShort,
                                               "port of linac PLC "
                                               "(deprecated)", None],
                                'AttrFile': [PyTango.DevString,
                                             "file that contains description "
                                             "of attributes of this "
                                             "Linac data block", ''],
                                'BindAddress': [PyTango.DevString,
                                                'ip of the interface used to '
                                                'communicate with plc '
                                                '(deprecated)', ''],
                                'LocalAddress': [PyTango.DevString,
                                                 'ip of the interface used '
                                                 'to communicate with plc as '
                                                 'the local', '10.0.7.100'],
                                'RemoteAddress': [PyTango.DevString,
                                                  'ip of the interface used '
                                                  'to communicate with plc as '
                                                  'the remote', '10.0.7.1'],
                                'TimeoutAlarm': [PyTango.DevDouble,
                                                 "after how many seconds of "
                                                 "silence the state is set "
                                                 "to alarm, this should be "
                                                 "less than TimeoutConnection",
                                                 1.0],
                                'TimeoutConnection': [PyTango.DevDouble,
                                                      "after how many seconds "
                                                      "of silence the "
                                                      "connection is assumed "
                                                      "to be interrupted",
                                                      1.5],
                                'ReconnectWait': [PyTango.DevDouble,
                                                  "after how many seconds "
                                                  "since the last update the "
                                                  "next connection attempt is "
                                                  "made", 6.0],
                                }
        class_property_list['TimeoutAlarm'] = \
            device_property_list['TimeoutAlarm']
        class_property_list['TimeoutConnection'] = \
            device_property_list['TimeoutConnection']
        class_property_list['ReconnectWait'] = \
            device_property_list['ReconnectWait']

        # Command definitions ---
        cmd_list = {'ReloadAttrFile': [[PyTango.DevVoid, ""],
                                       [PyTango.DevVoid, ""]],
                    'Exec': [[PyTango.DevString, "statement to executed"],
                             [PyTango.DevString, "result"],
                             {'Display level': PyTango.DispLevel.EXPERT, }],
                    'GetBit': [[PyTango.DevVarShortArray, "idx"],
                               [PyTango.DevBoolean, ""],
                               {'Display level': PyTango.DispLevel.EXPERT, }],
                    'GetByte': [[PyTango.DevShort, "idx"],
                                [PyTango.DevShort, ""],
                                {'Display level': PyTango.DispLevel.EXPERT, }],
                    'GetShort': [[PyTango.DevShort, "idx"],
                                 [PyTango.DevShort, ""],
                                 {'Display level':
                                  PyTango.DispLevel.EXPERT, }],
                    'GetFloat': [[PyTango.DevShort, "idx"],
                                 [PyTango.DevFloat, ""],
                                 {'Display level':
                                  PyTango.DispLevel.EXPERT, }],
                    'HexDump': [[PyTango.DevVoid, "idx"],
                                [PyTango.DevString, "hexdump of all data"]],
                    'Hex': [[PyTango.DevShort, "idx"],
                            [PyTango.DevString, ""]],
                    'DumpTo': [[PyTango.DevString, "target file"],
                               [PyTango.DevVoid, ""], {}],
                    'WriteBit': [[PyTango.DevVarShortArray,
                                  "idx, bitno, value"],
                                 [PyTango.DevVoid, ""],
                                 {'Display level':
                                  PyTango.DispLevel.EXPERT, }],
                    'WriteByte': [[PyTango.DevVarShortArray, "idx, value"],
                                  [PyTango.DevVoid, ""],
                                  {'Display level':
                                   PyTango.DispLevel.EXPERT, }],
                    'WriteShort': [[PyTango.DevVarShortArray, "idx, value"],
                                   [PyTango.DevVoid, ""],
                                   {'Display level':
                                    PyTango.DispLevel.EXPERT, }],
                    'WriteFloat': [[PyTango.DevVarFloatArray, "idx, value"],
                                   [PyTango.DevVoid, ""],
                                   {'Display level':
                                    PyTango.DispLevel.EXPERT}],
                    'ResetState': [[PyTango.DevVoid, ""],
                                   [PyTango.DevVoid, ""]],
                    'Update': [[PyTango.DevVoid, ""],
                               [PyTango.DevVoid, ""],
                               # { 'polling period' : 50 }
                               ],
                    'RestoreReadDB': [[PyTango.DevVoid, ""],
                                      [PyTango.DevVoid, ""],
                                      {'Display level':
                                           PyTango.DispLevel.EXPERT}],
                    }

        # Attribute definitions ---
        attr_list = {'EventsTime': [[PyTango.DevDouble,
                                     PyTango.SPECTRUM,
                                     PyTango.READ, 1800],
                                    {'Display level':
                                     PyTango.DispLevel.EXPERT}
                                    ],
                     'EventsTimeMin': [[PyTango.DevDouble,
                                        PyTango.SCALAR,
                                        PyTango.READ],
                                       {'Display level':
                                        PyTango.DispLevel.EXPERT}
                                       ],
                     'EventsTimeMax': [[PyTango.DevDouble,
                                        PyTango.SCALAR,
                                        PyTango.READ],
                                       {'Display level':
                                        PyTango.DispLevel.EXPERT}
                                       ],
                     'EventsTimeMean': [[PyTango.DevDouble,
                                        PyTango.SCALAR,
                                        PyTango.READ],
                                       {'Display level':
                                        PyTango.DispLevel.EXPERT}
                                       ],
                     'EventsTimeStd': [[PyTango.DevDouble,
                                        PyTango.SCALAR,
                                        PyTango.READ],
                                       {'Display level':
                                        PyTango.DispLevel.EXPERT}
                                       ],
                     'EventsNumber': [[PyTango.DevShort,
                                       PyTango.SPECTRUM,
                                       PyTango.READ, 1800],
                                      {'Display level':
                                       PyTango.DispLevel.EXPERT}
                                      ],
                     'EventsNumberMin': [[PyTango.DevUShort,
                                          PyTango.SCALAR,
                                          PyTango.READ],
                                         {'Display level':
                                          PyTango.DispLevel.EXPERT}
                                         ],
                     'EventsNumberMax': [[PyTango.DevUShort,
                                          PyTango.SCALAR,
                                          PyTango.READ],
                                         {'Display level':
                                          PyTango.DispLevel.EXPERT}
                                         ],
                     'EventsNumberMean': [[PyTango.DevDouble,
                                          PyTango.SCALAR,
                                          PyTango.READ],
                                         {'Display level':
                                          PyTango.DispLevel.EXPERT}
                                         ],
                     'EventsNumberStd': [[PyTango.DevDouble,
                                          PyTango.SCALAR,
                                          PyTango.READ],
                                         {'Display level':
                                          PyTango.DispLevel.EXPERT}
                                         ],
                     'IsTooFarEnable': [[PyTango.DevBoolean,
                                         PyTango.SCALAR,
                                         PyTango.READ_WRITE],
                                        {'label':
                                         "Is Too Far readback Feature "
                                         "Enabled?",
                                         'Display level':
                                         PyTango.DispLevel.EXPERT,
                                         'description':
                                         "This boolean is to enable or "
                                         "disable the feature to use the "
                                         "quality warning for readback "
                                         "attributes with setpoint too far",
                                         'Memorized': "true"
                                         }
                                        ],
                     'forceWriteDB': [[PyTango.DevString,
                                       PyTango.SCALAR,
                                       PyTango.READ],
                                      {'Display level':
                                           PyTango.DispLevel.EXPERT}
                                      ],
                     'cpu_percent': [[PyTango.DevDouble,
                                      PyTango.SCALAR,
                                      PyTango.READ],
                                     {'Display level':
                                          PyTango.DispLevel.EXPERT}
                                     ],
                     'mem_percent': [[PyTango.DevDouble,
                                      PyTango.SCALAR,
                                      PyTango.READ],
                                     {'Display level':
                                          PyTango.DispLevel.EXPERT}
                                     ],
                     'mem_rss': [[PyTango.DevULong,
                                  PyTango.SCALAR,
                                  PyTango.READ],
                                 {'Display level':
                                      PyTango.DispLevel.EXPERT,
                                  'unit': 'Bytes'}
                                 ],
                     'mem_swap': [[PyTango.DevULong,
                                   PyTango.SCALAR,
                                   PyTango.READ],
                                  {'Display level':
                                       PyTango.DispLevel.EXPERT,
                                  'unit': 'Bytes'}
                                  ],
                     }

if __name__ == '__main__':
        try:
            py = PyTango.Util(sys.argv)
            py.add_TgClass(LinacDataClass, LinacData, 'LinacData')
            U = PyTango.Util.instance()
            U.server_init()
            U.server_run()
        except PyTango.DevFailed as e:
            PyTango.Except.print_exception(e)
        except Exception as e:
            traceback.print_exc()
