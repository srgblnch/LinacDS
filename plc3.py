# -*- coding: utf-8 -*-
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

import plchelp  # there is the help about how to follow this builder

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

############################

HV = ('horizontal', 'vertical')
F = ('focussing',)

FOCUS_STATUS = {0: 'undefined',
                1: 'off',
                2: 'bad current',
                3: 'underflow',
                4: 'overtemp',
                5: 'ready'}

FOCUS_QUALITIES = {ALARM: [0],
                   WARNING: [1, 2, 3, 4]}

HV_STATUS = {0: 'undefined',
             1: 'off',
             2: 'bad current',
             3: 'undefined',
             4: 'undefined',
             5: 'ready'}

HV_QUALITIES = {ALARM: [0, 3, 4],
                WARNING: [1, 2]}

# used by PS
Iread_addr = 0
Iref_addr = 0
Status_addr = 128
CURRENT = "I"
SETPOINT = "setpoint"


def PS(name, types, rng):
    global Iread_addr
    global Status_addr
    global Iref_addr
    global HV, F
    global FOCUS_STATUS, HV_STATUS
    global FOCUS_QUALITIES, HV_QUALITIES
    global CURRENT, SETPOINT
    for T in types:
        M = T[0].upper()
        desc = name+' current'
        readbackName = name+M+'_'+CURRENT
        setpointName = name+M+'_'+CURRENT+'_'+SETPOINT
        Attr(readbackName,
             PyTango.DevFloat, Iread_addr,  # RO
             desc=desc+' monitor', unit='A',
             setpoint=setpointName, **rng)
        Attr(setpointName,
             PyTango.DevFloat, Iread_addr+161, Iref_addr,  # RW
             desc=desc+' setpoint', unit='A',
             readback=readbackName, **rng)
        Iread_addr += 4
        Iref_addr += 4
        desc_st = '%s %s status' % (name, T)
        if T in HV:
            meanings = HV_STATUS
            qualities = HV_QUALITIES
        elif T in F:
            meanings = FOCUS_STATUS
            qualities = FOCUS_QUALITIES
        else:
            meanings = None
        Attr('%s%s_ST' % (name, M),
             PyTango.DevUChar, Status_addr,  # RO
             desc=desc_st+john(meanings),
             meanings=meanings, qualities=qualities, events={},
             IamChecker=['\x01', '\x02', '\x03', '\x04', '\x05'])
        Status_addr += 1


PS('SL1', F, {'minValue': 0.0, 'maxValue': 1.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL2', F, {'minValue': 0.0, 'maxValue': 1.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL3', F, {'minValue': 0.0, 'maxValue': 1.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL4', F, {'minValue': 0.0, 'maxValue': 1.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('BC1', F, {'minValue': 0.0, 'maxValue': 200.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('BC2', F, {'minValue': 0.0, 'maxValue': 200.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('GL',  F, {'minValue': 0.0, 'maxValue': 130.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('QT1', F, {'minValue': 0.0, 'maxValue': 6.0, 'format': '%4.3f',
              EVENTS: {THRESHOLD: 0.0001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('QT2', F, {'minValue': 0.0, 'maxValue': 6.0, 'format': '%4.3f',
              EVENTS: {THRESHOLD: 0.0001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL1', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL2', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL3', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('SL4', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('BC1', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('BC2', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('GL', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
              EVENTS: {THRESHOLD: 0.001},
              QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('AS1', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('QT1', HV, {'minValue': -16.0, 'maxValue': 16.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})
PS('AS2', HV, {'minValue': -2.0, 'maxValue': 2.0, 'format': '%4.2f',
               EVENTS: {THRESHOLD: 0.001},
               QUALITIES: {CHANGING: {RELATIVE: 0.1}}})

onc_desc = lambda x: x+' on/off\nFalse:off\nTrue:on'
AttrBit('MA_Interlock_RC', 289, 0, 128,
        desc='magnets interlock reset, rising edge:reset', events={},
        isRst=True)
AttrBit('SL1_ONC', 289, 1, 128, desc=onc_desc('SL1'), events={})
AttrBit('SL2_ONC', 289, 2, 128, desc=onc_desc('SL2'), events={})
AttrBit('SL3_ONC', 289, 3, 128, desc=onc_desc('SL3'), events={})
AttrBit('SL4_ONC', 289, 4, 128, desc=onc_desc('SL4'), events={})
AttrBit('BC1_ONC', 289, 5, 128, desc=onc_desc('BC1'), events={})
AttrBit('BC2_ONC', 289, 6, 128, desc=onc_desc('BC2'), events={})
AttrBit('GL_ONC', 289, 7, 128, desc=onc_desc('GL'), events={})
AttrBit('AS1_ONC', 290, 0, 129, desc=onc_desc('AS1'), events={})
AttrBit('QT_ONC', 290, 1, 129, desc=onc_desc('QT'), events={})
AttrBit('AS2_ONC', 290, 2, 129, desc=onc_desc('AS2'), events={})

GrpBit('all_onc',
       attrGroup=['%s_ONC' % m for m in ['SL1', 'SL2', 'SL3', 'SL4','BC1',
                                         'BC2', 'GL', 'AS1', 'QT', 'AS2']],
       label='all magnet on', meanings={0: 'close', 1: 'open'},
       qualities={WARNING: [0]}, events={})

for magnet in ['SL1', 'SL2', 'SL3', 'SL4', 'BC1', 'BC2', 'GL']:
    AttrLogic('%s_cooling' % (magnet),
              logic={'%sF_ST' % (magnet): [3, 4]},
              desc='%s cooling loop state' % (magnet),
              label='%s cooling loop state' % (magnet),
              events={}, inverted=True)

    AttrLogic('%s_current_ok' % (magnet),
              logic={'%sF_ST' % (magnet): [0, 1, 2],
                     '%sF_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]},
                     '%sH_ST' % (magnet): [0, 1, 2],
                     '%sH_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]},
                     '%sV_ST' % (magnet): [0, 1, 2],
                     '%sV_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]}},
              desc='%s current state' % (magnet),
              label='%s current state' % (magnet),
              events={}, operator='or', inverted=True)

for magnet in ['AS1', 'AS2']:
    AttrLogic('%s_cooling' % (magnet),
              logic={'%sH_ST' % (magnet): [3, 4],
                     '%sH_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]},
                     '%sV_ST' % (magnet): [3, 4],
                     '%sV_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]}},
              desc='%s cooling loop state' % (magnet),
              label='%s cooling loop state' % (magnet),
              events={}, inverted=True)

    AttrLogic('%s_current_ok' % (magnet),
              logic={'%sH_ST' % (magnet): [0, 1, 2],
                     '%sH_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]},
                     '%sV_ST' % (magnet): [0, 1, 2],
                     '%sV_I' % (magnet): {QUALITIES:
                                          [AttrQuality.ATTR_WARNING]}},
              desc='%s current state' % (magnet),
              label='%s current state' % (magnet),
              events={}, operator='or', inverted=True)

AttrLogic('QT_cooling',
          logic={'QT1F_ST': [3, 4], 'QT2F_ST': [3, 4]},
          desc='QT cooling loop state',
          label='QT cooling loop state',
          events={}, inverted=True)

AttrLogic('QT_current_ok',
          logic={'QT1F_ST': [0, 1, 2],
                 'QT1F_I': {QUALITIES: [AttrQuality.ATTR_WARNING]},
                 'QT2F_ST': [0, 1, 2],
                 'QT2F_I': {QUALITIES: [AttrQuality.ATTR_WARNING]},
                 'QT1H_ST': [0, 1, 2],
                 'QT1H_I': {QUALITIES: [AttrQuality.ATTR_WARNING]},
                 'QT1V_ST': [0, 1, 2],
                 'QT1V_I': {QUALITIES: [AttrQuality.ATTR_WARNING]}},
          desc='QT current state',
          label='QT current state',
          events={}, operator='or', inverted=True)

# AttrPLC(HeartBeat, Lock_ST, rLockingAddr, rLockingBit, wLockingAddr,
#         wLockingBit)
AttrPLC(160, 159, 291, 0, 130, 0)  # FIXME ---
# the locking was 291 but documentation say 292

AttrEnumeration('BC1F_u')
AttrEnumeration('BC2F_u')
AttrEnumeration('GL_u')
AttrEnumeration('SL1F_u')
AttrEnumeration('SL2F_u')
AttrEnumeration('SL3F_u')
AttrEnumeration('SL4F_u')
AttrEnumeration('QT1F_u')
AttrEnumeration('QT2F_u')
AttrEnumeration('QT1H_u')
AttrEnumeration('QT2V_u')
