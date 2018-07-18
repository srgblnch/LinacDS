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

# ## Read only attributes ---

# R000 @IP1_PM ---
# R004 @IP2_PM ---
# R008 @IP3_PM ---
# R012 @IP4_PM ---
# R016 @IP5_PM ---
# R020 @IP6_PM ---
# R024 @IP7_PM ---
# R028 @IP8_PM ---
# R032 @IP9_PM ---
for i in range(9):
    number = i+1
    Attr('IP%d_P' % (number),
         PyTango.DevFloat, 4*i,  # RO
         label='ion pump %d pressure monitor' % (number),
         format='%2.1e', minValue=1e-11, maxValue=1e0, unit='mbar',
         events={}, qualities={WARNING: {ABSOLUTE: {ABOVE: 1e-7}}})

# R036 @HG1_PM ---
# R040 @HG2_PM ---
# R044 @HG3_PM ---
# R048 @HG4_PM ---
# R052 @HG5_PM ---
for i in range(5):
    number = i+1
    Attr('HVG%d_P' % (number),
         PyTango.DevFloat, 36+4*i,  # RO
         label='high vacuum gauge %d pressure monitor' % (number),
         format='%2.1e', minValue=1e-11, maxValue=1, unit='mbar',
         events={}, qualities={WARNING: {ABSOLUTE: {ABOVE: 1e-7}}})

# R056 @CL1_TM ---
# R060 @CL2_TM ---
# R064 @CL3_TM ---
for i in range(3):
    number = i+1
    Attr('CL%d_T' % (number),
         PyTango.DevFloat, 56+4*i,  # RO
         label='cooling loop %d temperature monitor' % (number),
         format='%4.2f', minValue=0, maxValue=50, unit='⁰C',
         events={THRESHOLD: 0.001})

# R068 @CL1_PWDM ---
# R072 @CL2_PWDM ---
# R076 @CL3_PWDM ---
for i in range(3):
    number = i+1
    Attr('CL%d_PWD' % (number),
         PyTango.DevFloat, 68+4*i,  # RO
         label='cooling loop %d power drive monitor' % (number),
         format='%4.1f', minValue=0, maxValue=100, unit='%',
         events={THRESHOLD: 0.1}, qualities={WARNING: {ABSOLUTE: {BELOW: 15,
                                                                  ABOVE: 80}}})

# R080 @spare: was CL4_TM ---

# R084 @DI_0to7 ---
for i in range(8):
    number = i+1
    AttrBit('IP%d_ST' % (number),
            84, i,  # RO
            label='ion pump %d status' % (number),
            meanings={0: 'off', 1: 'on'},
            qualities={WARNING: [0]}, events={})

# R085 @DI_8to15 ---
AttrBit('IP9_ST',
        85, 0,  # RO
        label='ion pump 9 status',
        meanings={0: 'off', 1: 'on'},
        qualities={WARNING: [0]}, events={})

AttrBit('VC_OK',  # LI_VOK
        85, 1,  # RO
        label='linac vacuum okay',
        meanings={0: 'bad vacuum', 1: 'good vacuum'},
        qualities={WARNING: [0]}, events={})

for i in range(5):
    number = i+1
    AttrBit('HVG%d_IS' % (number),
            85, 2+i,  # RO
            label='high vacuum gauge %d interlock' % (number),
            desc='high vacuum gauge %d interlock; False:fault, True:ready'
                 % (number),
            meanings={0: 'fault', 1: 'ready'},
            qualities={WARNING: [0]}, events={})

AttrBit('IP1_IS',
        85, 7,  # RO
        label='ion pump 1 interlock',
        desc='ion pump 1 interlock; False:fault, True:ready',
        meanings={0: 'fault', 1: 'ready'},
        qualities={WARNING: [0]}, events={})

# R086 @DI_Spare ---
for i in range(8):
    number = i+2
    AttrBit('IP%d_IS' % (number),
            86, i,  # RO
            label='ion pump %d interlock' % (number),
            desc='ion pump %d interlock; False:fault, True:ready' % (number),
            meanings={0: 'fault', 1: 'ready'},
            qualities={WARNING: [0]}, events={})

# R087 @CV_ST ---
VALVE_STATUS = {0: 'undefined',
                1: 'moving',
                2: 'opened',
                3: 'closed',
                4: 'fault'}
VALVE_QUALITIES = {ALARM: [0],
                   WARNING: [3, 4],
                   CHANGING: [1]}
Attr('VCV_ST',
     PyTango.DevUChar, 87,  # RO
     label='collimator valve state',
     desc='collimator valve state'+john(VALVE_STATUS),
     meanings=VALVE_STATUS, qualities=VALVE_QUALITIES, events={})

# R088 @VV1_ST ---
# R089 @VV2_ST ---
# R090 @VV3_ST ---
# R091 @VV4_ST ---
# R092 @VV5_ST ---
# R093 @VV6_ST ---
# R094 @VV7_ST ---
for i in range(7):
    number = i+1
    Attr('VV%d_ST' % (number),
         PyTango.DevUChar, 88+i,  # RO
         label='vacuum valve %d state' % (number),
         desc='vacuum valve %d state' % (number)+john(VALVE_STATUS),
         meanings=VALVE_STATUS, qualities=VALVE_QUALITIES, events={})

# R095 @Comm_ST #defined with the heardbeat at the end of this file ---

# R096 @CL1_ST ---
cl1_meaning = {0: 'primary underflow',
               1: 'off',
               2: 'fault',
               3: 'prebuncher 1 underflow',
               4: 'prebuncher 2 underflow',
               5: 'buncher underflow',
               6: 'running',
               7: 'cooling down (5 min)'}
cl1_qualities = {WARNING: [0, 1, 2, 3, 4, 5],
                 CHANGING: [5, 7]}

Attr('CL1_ST',
     PyTango.DevUChar, 96,  # RO
     label='cooling loop 1 status',
     desc='cooling loop 1 status' + john(cl1_meaning),
     meanings=cl1_meaning, qualities=cl1_qualities, events={},
     historyBuffer={BASESET: [1, 6]})

AttrLogic('cl1_ready',
          logic={'CL1_ST': [1, 6]},
          desc='cooling loop 1 ready',
          label='cooling loop 1 ready',
          events={})

# R097 @CL2_ST ---
cl2_meaning = {0: 'primary underflow',
               1: 'off',
               2: 'fault',
               3: 'accelerating section 1 underflow',
               4: 'running',
               5: 'cooling down (5 min)'}
cl2_qualities = {ALARM: [2],
                 WARNING: [0, 1, 3],
                 CHANGING: [5]}
Attr('CL2_ST',
     PyTango.DevUChar, 97,  # RO
     label='cooling loop 2 status',
     desc='cooling loop 2 status' + john(cl2_meaning),
     meanings=cl2_meaning, qualities=cl2_qualities, events={},
     historyBuffer={BASESET: [1, 4]})

AttrLogic('cl2_ready',
          logic={'CL2_ST': [1, 4]},
          desc='cooling loop 2 ready',
          label='cooling loop 2 ready',
          events={})

# R098 @CL3_ST ---
cl3_meaning = {0: 'primary underflow',
               1: 'off',
               2: 'fault',
               3: 'accelerating section 2 underflow',
               4: 'running',
               5: 'cooling down (5 minutes)'}
cl3_qualities = {ALARM: [2],
                 WARNING: [0, 1, 3],
                 CHANGING: [5]}

Attr('CL3_ST',
     PyTango.DevUChar, 98,  # RO
     label='cooling loop 3 status',
     desc='cooling loop 3 status' + john(cl3_meaning),
     meanings=cl3_meaning, qualities=cl3_qualities, events={},
     historyBuffer={BASESET: [1, 4]})

AttrLogic('cl3_ready',
          logic={'CL3_ST': [1, 4]},
          desc='cooling loop 3 ready',
          label='cooling loop 3 ready',
          events={})

# R099 @DI_Comm ---
# AttrBit('HeartBeat',  # Heartbeat defined at the end together with lockers
#        99, 0,  # RO
#        desc='PLC 2 heart beat')
AttrBit('AC_IS',
        99, 1,
        label='compressed air interlock state',
        meanings={0: 'fault', 1: 'good'},
        qualities={WARNING: [0]}, events={})

# ## Read/Write attributes ---

# R100 W000 @CL1_TS ---
# R104 W004 @CL2_TS ---
# R108 W008 @CL3_TS ---
for i in range(3):
    number = i+1
    Attr('CL%d_T_setpoint' % (number),
         PyTango.DevFloat, 100+4*i, 4*i,  # RW
         label='cooling loop %d temperature setpoint' % (number),
         format='%4.2f', unit='⁰C', minValue=0, maxValue=50,
         events={THRESHOLD: 0.01},
         qualities={CHANGING: {RELATIVE: 0.5},
                    WARNING: {ABSOLUTE: {ABOVE: 40, BELOW: 20}},
                    ALARM: {ABSOLUTE: {ABOVE: 45, BELOW: 15}}})

# R112 W012 @AO_03: spare ---

# R116 W016 @DO_0to7 ---
AttrBit('VCV_ONC',
        116, 0, 16,
        label='collimator valve open',
        meanings={0: 'close', 1: 'open'},
        qualities={WARNING: [0]}, events={},
        formula={'read': 'VALUE and not Attr[VCV_ST].rvalue == 4'}
        )

for i in range(7):
    number = i+1
    AttrBit('VV%d_OC' % (number),
            116, 1+i, 16,
            label='vacuum valve %d open' % (number),
            meanings={0: 'close', 1: 'open'},
            qualities={WARNING: [0]}, events={},
            formula={'read': 'VALUE and not Attr[VV%d_ST].rvalue == 4'
                             % (number)})

GrpBit('VVall_OC',
       attrGroup=['VV%s_OC' % i for i in range(1,8)],
       label='all vacuum valves open', meanings={0: 'close', 1: 'open'},
       qualities={WARNING: [0]}, events={})

# R117 W017 @DO_8to15 ---
AttrBit('Util_Interlock_RC',
        117, 0, 17,
        label='interlock reset',
        # FIXME: ---
        # reset bits are special because their meaning is 'rising edge'
        desc='utilities interlock reset command', events={}, isRst=True)

AttrBit('VC_Interlock_RC',
        117, 1, 17,
        label='vacuum reset',
        # FIXME: ---
        # reset bits are special because their meaning is 'rising edge'
        desc='vacuum reset command', events={}, isRst=True, activeRst_t=3.200)
for i in range(3):
    number = i+1
    AttrBit('CL%d_ONC' % (number),
            117, i+2, 17,
            label='cooling loop %d on' % (number),
            meanings={0: 'off', 1: 'on'},
            qualities={WARNING: [0]}, events={},
            formula={'read': 'VALUE and Attr[cl%d_ready].rvalue == True'
                             % (number)})

# R118 W018 @DO_16to23: free ---
# R119 W019 @DO_24to31: free ---

# R120 W020 @Local_Lock ---

# AttrPLC(HeartBeat, Lock_ST, rLockingAddr, rLockingBit, wLockingAddr,
#         wLockingBit)
AttrPLC(99, 95, 120, 0, 20, 0)

AttrEnumeration('IP1_u')
AttrEnumeration('IP2_u')
AttrEnumeration('IP3_u')
AttrEnumeration('IP4_u')
AttrEnumeration('IP5_u')
AttrEnumeration('IP6_u')
AttrEnumeration('IP7_u')
AttrEnumeration('IP8_u')
AttrEnumeration('IP9_u')
AttrEnumeration('HVG1_u')
AttrEnumeration('HVG2_u')
AttrEnumeration('HVG3_u')
AttrEnumeration('HVG4_u')
AttrEnumeration('HVG5_u')
AttrEnumeration('IPC1_u')
AttrEnumeration('IPC2_u')
AttrEnumeration('IPC3_u')
AttrEnumeration('IPC4_u')
AttrEnumeration('IPC5_u')
