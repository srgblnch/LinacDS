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

# import plchelp  # there is the help about how to follow this builder

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

# def jin(*args):
#     return john(args)

Attr('Heat_I',
     PyTango.DevFloat, read_addr=4,  # RO
     label='Heating current monitor',
     unit='A', minValue=0, maxValue=30, format='%4.1f',
     events={THRESHOLD: 0.01},  # qualities={CHANGING: {'rel': 0.1}}
     )

Attr('Heat_V',
     PyTango.DevFloat, read_addr=8,  # RO
     label='Heating voltage monitor',
     unit='V', minValue=0, maxValue=30, format='%4.1f',
     events={THRESHOLD: 0.01},  # qualities={CHANGING: {'rel': 0.1}}
     )

Attr('HVPS_V',
     PyTango.DevFloat, read_addr=12,  # RO
     label='High voltage PS voltage',
     unit='kV', minValue=0, maxValue=40, format='%4.2f',
     events={THRESHOLD: 0.001},
     # qualities={CHANGING: {'rel': 0.1}}
     )

Attr('HVPS_I',
     PyTango.DevFloat, read_addr=16,  # RO
     label='High voltage PS current',
     unit='mA', minValue=0, maxValue=150, format='%4.1f',
     events={THRESHOLD: 0.01},
     # qualities={CHANGING: {'rel': 0.1}}
     )

Attr('Peak_I',
     PyTango.DevFloat, read_addr=20,  # RO
     label='Peak current',
     unit='A', minValue=0, maxValue=400, format='%4.1f',
     events={THRESHOLD: 0.01},  # qualities={CHANGING: {'rel': 0.1}}
     )

Attr('Peak_V',
     PyTango.DevFloat, read_addr=24,  # RO
     label='Peak voltage',
     desc='peak voltage (calculated',
     unit='kV', minValue=0, maxValue=400, format='%4.1f',
     events={THRESHOLD: 0.01},  # qualities={CHANGING: {'rel': 0.1}}
     )

LV_J = {0: 'off',
        1: 'vacuum fault',
        2: 'oil level fault',
        3: 'fan circuit breakers fault',
        4: '23 C water inlet fault',
        5: 'focusing magnet underflow',
        6: 'focusing magnet overtemp',
        7: 'klystron body underflow',
        8: 'klystron body overtemp',
        9: 'klystron collector underflow',
        10: 'klystron collector overtemp',
        11: 'cooling down (5 minutes)',
        12: 'ready'}

LV_J_QUALITIES = {WARNING: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                  CHANGING: [11]}

Attr('LV_ST',
     PyTango.DevUChar, read_addr=37,  # RO
     label='Low voltage status',
     desc='low voltage status'+john(LV_J),
     meanings=LV_J, qualities=LV_J_QUALITIES, events={})

F_J = {0: 'off',
       1: 'decreasing',
       2: 'low limit fault',
       3: 'high limit fault',
       4: 'heating',
       5: 'ready'}

F_J_QUALITIES = {WARNING: [0, 2, 3],
                 CHANGING: [1, 4]}

Attr('Heat_ST',
     PyTango.DevUChar, read_addr=38,  # RO
     label='Filament heating status',
     desc='filament heating status'+john(F_J),
     meanings=F_J, qualities=F_J_QUALITIES, events={})

# modify the documented state meaning string to adapt to user meaning.
HV_J = {0: 'Waiting for Low Voltage',  # 'heating...',
        1: 'klystron tank covers',
        2: 'PFN earth rod',
        3: 'PFN doors',
        4: 'dumping relay closed',
        5: 'over current',
        6: 'interlock',
        7: 'fault',
        8: 'off',
        9: 'ready'}

HV_J_QUALITIES = {ALARM: [7],
                  WARNING: [0, 1, 2, 3, 4, 5, 6, 8]}

Attr('HVPS_ST',
     PyTango.DevUChar, read_addr=39,  # RO
     label='High voltage PS heating status',
     desc='high voltage PS heating status'+john(HV_J),
     meanings=HV_J, qualities=HV_J_QUALITIES, events={})

PL_J = {0: 'off',
        1: 'focusing B1 undercurrent',
        2: 'focusing B2 undercurrent',
        3: 'focusing B3 undercurrent',
        4: 'DC reset undercurrent',
        5: 'arc overcurrent',
        6: 'RF reflected power',
        7: 'off',
        8: 'ready'}

PL_J_QUALITIES = {WARNING: [0, 1, 2, 3, 4, 5, 6, 7]}

Attr('Pulse_ST',
     PyTango.DevUChar, read_addr=40,  # RO
     label='Pulse status',
     desc='pulse status'+john(PL_J),
     meanings=PL_J, qualities=PL_J_QUALITIES, events={})

Attr('LV_Time',
     PyTango.DevShort, read_addr=42,  # RO
     label='Voltage slow down time',
     desc='tempo stop low voltage (5 min)',
     unit='s', events={},
     qualities={CHANGING: {ABSOLUTE: {ABOVE: 0, BELOW: 300, UNDER: True}}},
     )

Attr('Heat_Time',
     PyTango.DevShort, read_addr=44,  # RO
     label='Heating time',
     desc='heating tempo (20 min)',
     unit='m', events={},
     # FIXME: ---
     # even documentation says this is seconds, its clear that it gives
     # tenths of seconds. A formula is required to convert to minutes
     # (integer rounded)
     formula={'read': 'VALUE / 6'},
     qualities={CHANGING: {ABSOLUTE: {ABOVE: 0, BELOW: 20, UNDER: True}}},
     )

# TODO: ---
# This attrbute will 'Rampeable' above some given threashold.
# That is from 0 to this threashold is set directly, and above to
# the maximum must follow some steps and some time on each step.
# This two ramp parameters must be also dynattrs.
Attr('HVPS_V_setpoint',  # AttrRampeable('HVPS_V_setpoint',
     PyTango.DevFloat,
     # read_addr=46,
     write_addr=0,  # RW
     label='High voltage PS voltage setpoint',
     unit='kV', minValue=0, maxValue=33, format='%4.2f',
     events={THRESHOLD: 0.005},
     qualities={CHANGING: {'rel': 0.1}},
     # rampsDescriptor={ASCENDING: {STEP: 0.5,  # kV
     #                              STEPTIME: 1,  # s
     #                              THRESHOLD: 20,  # kV
     #                              SWITCH: 'HVPS_ONC'}},
     readback='HVPS_V')

AttrBit('LV_Interlock_RC',
        # read_addr=62,
        read_bit=0, write_addr=16,  # RW
        label='Low voltage reset',
        desc='low voltage reset\nrising edge reset',
        events={}, isRst=True)

AttrBit('LV_ONC',
        # read_addr=62,
        read_bit=1, write_addr=16,  # RW
        label='Low voltage on',
        desc='low voltage on\nFalse:off\nTrue:on',
        events={},
        formula={'read': 'VALUE and Attr[lv_ready].rvalue == True'},
        )

AttrBit('HVPS_Interlock_RC',
        # read_addr=62,
        read_bit=2, write_addr=16,  # RW
        label='High voltage reset',
        desc='high voltage reset\nrising edge reset',
        events={}, isRst=True)

AttrBit('HVPS_ONC',
        # read_addr=62,
        read_bit=3, write_addr=16,  # RW
        label='High voltage on',
        desc='high voltage on\nFalse:off\nTrue:on',
        events={},
        # rampingAttr='HVPS_V_setpoint',
        formula={'read':
                 'VALUE and Attr[HVPS_ST].rvalue == 9 and '
                 'Attr[Pulse_ST].rvalue == 8',
                 'write':
                 'VALUE and Attr[HVPS_ST].rvalue in [8,9] and '
                 'Attr[Pulse_ST].rvalue in [7,8]'
                 },
        # switchDescriptor={ATTR2RAMP: 'HVPS_V_setpoint',
        #                   WHENON: {FROM:
        #                            'HVPS_V_setpoint_Ascending_Threshold'},
        #                   # WHENOFF: {TO: 0}
        #                   # from where the WRITEVALUE say
        #                   }
        )

# AttrPLC(HeartBeat, Lock_ST, rLockingAddr, rLockingBit, wLockingAddr,
#         wLockingBit)
AttrPLC(36, 41, 63, 0, 17, 0)

AttrLogic('lv_ready',
          logic={'LV_ST': [12], 'Heat_ST': [5]},
          desc='Klystron LV ready',
          label='Klystron LV ready',
          events={})

AttrLogic('hvps_ready',
          logic={'HVPS_ST': [8, 9], 'Pulse_ST': [0, 7, 8]},
          desc='High voltage PS ready',
          label='High voltage PS ready',
          events={})

AttrEnumeration('tube_u', prefix='KA')
AttrEnumeration('thyratron_u', prefix='KA')
AttrEnumeration('3GHz_RFampli_u', prefix='KA')
AttrEnumeration('DCps_thyratron_u', prefix='KA')
AttrEnumeration('HVps_u', prefix='KA')
AttrEnumeration('IP_controller', prefix='KA')
AttrEnumeration('fcoil1_u', prefix='KA')
AttrEnumeration('fcoil2_u', prefix='KA')
AttrEnumeration('fcoil3_u', prefix='KA')
