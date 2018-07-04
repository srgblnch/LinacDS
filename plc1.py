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

# R000 @EG_FVM ---
Attr('GUN_Filament_V',
     PyTango.DevFloat, 0,  # RO
     label='e-gun filament voltage monitor',
     format='%4.1f', minValue=0, maxValue=10, unit='V',
     events={THRESHOLD: 0.01},
     qualities={WARNING: {ABSOLUTE: {BELOW: 0.0}}},
     setpoint='GUN_Filament_V_setpoint',
     switch='GUN_LV_ONC')

# R004 @EG_FCM ---
Attr('GUN_Filament_I',
     PyTango.DevFloat, 4,  # RO
     label='e-gun filament current',
     format='%4.1f', minValue=0, maxValue=5, unit='A',
     events={THRESHOLD: 0.01},
     qualities={WARNING: {ABSOLUTE: {BELOW: 0.0}}})

# R008 @EG_KVM ---
Attr('GUN_Kathode_V',
     PyTango.DevFloat, 8,  # RO
     label='e-gun cathode voltage monitor',
     format='%4.1f', minValue=0, maxValue=50, unit='V',
     events={THRESHOLD: 0.01},
     qualities={WARNING: {ABSOLUTE: {BELOW: 0.0}}})

# R012 @EG_KTM ---
Attr('GUN_Kathode_T',
     PyTango.DevFloat, 12,  # RO
     label='e-gun cathode temperature',
     format='%4.1f', minValue=0, maxValue=50, unit='degC',
     events={THRESHOLD: 0.01},
     qualities={WARNING: {ABSOLUTE: {BELOW: 25.0,
                                     ABOVE: 41.0}}})

# R016 @AI_04: free ---
# R020 @AI_05: free ---
# R024 @AI_06: free ---
# R028 @AI_07: free ---

# R032 @HVS_VM ---
Attr('GUN_HV_V',
     PyTango.DevFloat, 32,  # RO
     label='HV PS Voltage',
     desc='high voltage PS voltage',
     format='%4.1f', minValue=-100, maxValue=0, unit='kV',
     events={THRESHOLD: 0.01},
     setpoint='GUN_HV_V_setpoint',
     switch='GUN_HV_ONC')

# R036 @HVS_CM ---
Attr('GUN_HV_I',
     PyTango.DevFloat, 36,  # RO
     label='High voltage PS current',
     desc='high voltage PS current (leakage current)',
     format='%4.1f', minValue=-600, maxValue=1, unit='μA',
     events={THRESHOLD: 0.01},
     qualities={WARNING: {ABSOLUTE: {ABOVE: 1.0,
                                     BELOW: -20.0}}},
     autoStop={BELOW: -20.0,
               INTEGRATIONTIME: 1,  # s
               SWITCHDESCRIPTOR: 'GUN_HV_ONC'},
     logLevel='warning')

# R040 @PHS1_PM ---
Attr('PHS1_Phase',
     PyTango.DevFloat, 40,  # RO
     label='Phase shifter 1 phase monitor',
     format='%4.1f', minValue=0, maxValue=160, unit='⁰',
     events={THRESHOLD: 0.01})

# R044 @Spare_1: CH3 spare ---

# R48 @SF6P1M ---
Attr('SF6_P1',
     PyTango.DevFloat, 48,  # RO
     label='SF6 pressure 1',
     format='%4.2f', minValue=-1, maxValue=5, unit='bar',
     events={THRESHOLD: 0.001},
     qualities={WARNING: {ABSOLUTE: {BELOW: 2.9,
                                     ABOVE: 3.05}}})

# R052 @SF6P2M ---
Attr('SF6_P2',
     PyTango.DevFloat, 52,  # RO
     label='SF6 pressure 2',
     format='%4.2f', minValue=-1, maxValue=5, unit='bar',
     events={THRESHOLD: 0.001},
     qualities={WARNING: {ABSOLUTE: {BELOW: 2.9,
                                     ABOVE: 3.05}}})

# R056 @PHS2_PM ---
Attr('PHS2_Phase',
     PyTango.DevFloat, 56,  # RO
     label='Phase shifter 2 phase monitor',
     format='%4.1f', minValue=0, maxValue=380, unit='⁰',
     events={THRESHOLD: 0.01})

# R060 @ATT2_PM ---
Attr('ATT2_P',
     PyTango.DevFloat, 60,  # RO
     label='Attenuator 2 monitor',
     desc='Attenuator 2 monitor attenuation (PB2)',
     format='%4.1f', minValue=-10, maxValue=10, unit='dB',
     events={THRESHOLD: 0.01})

# R064 @AI_15: free ---

# R068 @DI_0to7 ---
AttrBit('TB_ST',
        68, 0,  # RO
        label='Timer Status State',
        meanings={0: 'off',
                  1: 'ready'},
        qualities={WARNING: [0]},
        events={})
AttrBit('A0_ST',
        68, 4,  # RO
        label='500MHz amplifier status',
        meanings={0: 'off',
                  1: 'ready'},
        qualities={WARNING: [0]},
        events={})
AttrBit('RFS_ST',
        68, 5,  # RO
        label='RF source Status',
        meanings={0: 'off',
                  1: 'ready'},
        qualities={WARNING: [0]},
        events={})

# R069 @DI_8to15 ---

# R070 @DI_16to23 ---
AttrBit('EG_ENB',
        70, 0,  # RO
        label='Electron gun enabled (PSS)',
        meanings={0: 'disabled',
                  1: 'enabled'},
        qualities={WARNING: [0]},
        events={})
AttrBit('KA_ENB',
        70, 1,  # RO
        label='Klystron amplifier enabled (PSS)',
        meanings={0: 'disabled',
                  1: 'enabled'},
        qualities={WARNING: [0]},
        events={})
AttrBit('TL_VOK',
        70, 2,  # RO
        label='Transfer line vacuum OK (PSS)',
        meanings={0: 'bad vacuum',
                  1: 'good vacuum'},
        qualities={WARNING: [0]},
        events={})
AttrBit('IU_RDY',
        70, 5,  # RO
        label='Interlock unit ready',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('W1_UF',
        70, 6,  # RO
        label='Window 1 underflow state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('W2_UF',
        70, 7,  # RO
        label='Window 2 underflow state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})

# R71 @DI_24to31 ---
AttrBit('W3_UF',
        71, 0,  # RO
        label='Window 3 underflow state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('RL1_UF',
        71, 1,  # RO
        label='Resistor load 1 underflow state',
        meanings={0: 'underflow',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('RL2_UF',
        71, 2,  # RO
        label='Resistor load 2 underflow state',
        meanings={0: 'underflow',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('RL3_UF',
        71, 3,  # RO
        label='Resistor load 3 underflow state',
        meanings={0: 'underflow',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('UT_IS',
        71, 4,  # RO
        label='Utilities Interlock state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('MG_IS',
        71, 5,  # RO
        label='Magnet Interlock state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('GM_DI',
        71, 6,  # RO
        label='Gun Modulator door interlock',
        meanings={0: 'door open',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('LI_VOK',
        71, 7,  # RO
        label='Linac Vacuum OK',
        meanings={0: 'bad vacuum',
                  1: 'good vacuum'},
        qualities={WARNING: [0]},
        events={})

# R072 @DI_Comm ---
# AttrBit('HeartBeat',#Heartbeat defined at the end together with lockers
#         72,0,#RO
#        desc='PLC 1 heart beat')
AttrBit('PLC1_PR',
        72, 2,  # RO
        label='PLC1 profibus receive status',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('PLC1_PS',
        72, 4,  # RO
        label='PLC1 profibus send status',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})

# R073 @DI_ITLK_K ---
AttrBit('SF6_P1_ST',
        73, 0,  # RO
        label='SF6 pressure 1 state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('SF6_P2_ST',
        73, 1,  # RO
        label='SF6 pressure 2 state',
        meanings={0: 'fault',
                  1: 'normal'},
        qualities={WARNING: [0]},
        events={})
AttrBit('KA1_OK',  # KA1_EN
        73, 2,  # RO
        label='klystron 1 ready',
        events={})
AttrBit('KA2_OK',  # KA2_EN
        73, 3,  # RO
        label='klystron 2 ready',
        events={})
AttrBit('LI_OK',  # LI_RDY
        73, 4,  # RO
        label='Linac system ready',
        events={})
AttrBit('RF_OK',  # RF_ENB
        73, 5,  # RO
        label='RF ready',
        events={})

# R074 @HV_PS_ST ---
Attr('Gun_HV_ST',
     PyTango.DevUChar, 74,  # RO
     label='High voltage PS status',
     desc='high voltage PS status: '
          '0:undefined, 1:off, 2:locked, 3: fault, 4:ready, 5: unlocked',
     meanings={0: 'undefined',
               1: 'off',
               2: 'locked',
               3: 'fault',
               4: 'ready',
               5: 'unlocked'},
     qualities={ALARM: [0, 3, 5],
                WARNING: [1, 2, 5]},
     events={})

# R075 @E_GUN_ST ---
Attr('Gun_ST',
     PyTango.DevUChar, 75,  # RO
     label='e-gun low voltage status',
     desc='e-gun low voltage status: '
          '0:undefined, 1:off, 2:bad vacuum, 3:cathode voltage fault, '
          '4:filament current fault, 5:heating running, '
          '6:filament voltage fault, 7:cathode over temperature, 8:ready',
     # modification in the meaning because documentation looks wrong
     meanings={0: 'undefined',
               1: 'off',
               2: 'bad vacuum',
               3: 'cathode voltage fault',
               4: 'Heating',  # 'filament current fault',
               5: 'filament current fault',  # 'heating running',
               6: 'filament voltage fault',
               7: 'cathode over temperature',
               8: 'ready'},
     qualities={ALARM: [0],
                WARNING: [1, 2, 3, 5, 6, 7],
                CHANGING: [4]},
     events={})

AttrLogic('Gun_ready',
          logic={'Gun_ST': [1, 8]},
          desc='e-gun low voltage ready',
          label='e-gun low voltage ready',
          events={},
          )

AttrLogic('Gun_HV_ready',
          logic={'GM_DI': [True],
                 'GUN_HV_I_AutoStop_Triggered': [False]},
          desc='e-gun high voltage ready',
          label='e-gun high voltage ready',
          events={})

# R076 @SCM_1_ST ---
Attr('SCM1_ST',
     PyTango.DevUChar, 76,  # RO
     label='fs 1 status',
     desc='screen monitor 1 status: '
          '0:undefined, 1:moving, 2:up, 3:down, 4:fault',
     meanings={0: 'undefined',
               1: 'moving',
               2: 'up',
               3: 'down',
               4: 'fault'},
     qualities={ALARM: [0],
                WARNING: [3, 4],
                CHANGING: [1]},
     events={})

AttrLogic('SCM1_alert',
          logic={'SCM1_ST': [3, 4]},
          desc='screen monitor 1 alert',
          label='screen monitor 1 alerts',
          events={},
          )


# R077 @SCM_2_ST ---
Attr('SCM2_ST',
     PyTango.DevUChar, 77,  # RO
     label='fs 2 status',
     desc='screen monitor 2 status: '
          '0:undefined, 1:moving, 2:up, 3:down, 4:fault',
     meanings={0: 'undefined',
               1: 'moving',
               2: 'up',
               3: 'down',
               4: 'fault'},
     qualities={ALARM: [0],
                WARNING: [3, 4],
                CHANGING: [1]},
     events={})

AttrLogic('SCM2_alert',
          logic={'SCM2_ST': [3, 4]},
          desc='screen monitor 2 alert',
          label='screen monitor 2 alerts',
          events={},
          )

# R078 @SCM_3_ST ---
Attr('SCM3_ST',
     PyTango.DevUChar, 78,  # RO
     label='fs 3 status',
     desc='screen monitor 3 status: '
          '0:undefined, 1:moving, 2:up, 3:down, 4:fault',
     meanings={0: 'undefined',
               1: 'moving',
               2: 'up',
               3: 'down',
               4: 'fault'},
     qualities={ALARM: [0],
                WARNING: [3, 4],
                CHANGING: [1]},
     events={})

AttrLogic('SCM3_alert',
          logic={'SCM3_ST': [3, 4]},
          desc='screen monitor 3 alert',
          label='screen monitor 3 alerts',
          events={},
          )

# R079 @PHS1_ST ---
Attr('PHS1_ST',
     PyTango.DevUChar, 79,  # RO
     label='phase shifter 1 status',
     desc='phase shifter 1 status: '
          '0:undefined, 1:unset, 2:ready, 3:in limit fault, '
          '4:out limit fault, 5:timeout fault',
     meanings={0: 'undefined',
               1: 'unset',
               2: 'ready',
               3: 'in limit fault',
               4: 'out limit fault',
               5: 'timeout fault'},
     qualities={ALARM: [0],
                WARNING: [1, 3, 4, 5]},
     events={})

AttrLogic('phs1_ready',
          logic={'PHS1_ST': [2]},
          desc='phase shifter 1 ready',
          label='phase shifter 1 ready',
          events={},
          )

# R080 @PHS2_ST ---
Attr('PHS2_ST',
     PyTango.DevUChar, 80,  # RO
     label='phase shifter 2 status',
     desc='phase shifter 2 status: 0:undefined, '
          '1:unset, 2:ready, 3:in limit fault, 4:out limit fault, '
          '5:timeout fault',
     meanings={0: 'undefined',
               1: 'unset',
               2: 'ready',
               3: 'in limit fault',
               4: 'out limit fault',
               5: 'timeout fault'},
     qualities={ALARM: [0],
                WARNING: [1, 3, 4, 5]},
     events={})

AttrLogic('phs2_ready',
          logic={'PHS2_ST': [2]},
          desc='phase shifter 2 ready',
          label='phase shifter 2 ready',
          events={},
          )

# R081 @ATT2_ST ---
Attr('ATT2_ST',
     PyTango.DevUChar, 81,  # RO
     label='attenuator 2 status',
     desc='attenuator 2 status: 0:undefined, '
          '1:unset, 2:ready, 3:in limit fault, 4:out limit fault, '
          '5:timeout fault',
     meanings={0: 'undefined',
               1: 'unset',
               2: 'ready',
               3: 'in limit fault',
               4: 'out limit fault',
               5: 'timeout fault'},
     qualities={ALARM: [0],
                WARNING: [1, 3, 4, 5]},
     events={})

AttrLogic('att2_ready',
          logic={'ATT2_ST': [2]},
          desc='Attenuator 2 ready',
          label='Attenuator 2 ready',
          events={},
          )

# R082 @Comm_ST #defined with the heardbeat at the end of this file ---

# R083 @?? ---

# ## Read/Write attributes ---

# R084 W000 @EG_FVS ---
AttrRampeable('GUN_Filament_V_setpoint',
              PyTango.DevFloat, 84, 0,  # RW
              label='e-gun filament voltage setpoint',
              format='%4.1f', minValue=0, maxValue=10, unit='V',
              events={THRESHOLD: 0.01},
              qualities={WARNING: {ABSOLUTE: {BELOW: 0}}},
              rampsDescriptor={DESCENDING: {STEP: 1,  # V
                                            STEPTIME: 1,  # s
                                            THRESHOLD: 10,  # V
                                            SWITCH: 'GUN_LV_ONC'},
                               ASCENDING: {STEP: 1,  # V
                                           STEPTIME: 1,  # s
                                           THRESHOLD: 0,  # V
                                           SWITCH: 'GUN_LV_ONC'}},
              readback='GUN_Filament_V',
              switch='GUN_LV_ONC')

# R088 W004 @EG_KVS ---
Attr('GUN_Kathode_V_setpoint',
     PyTango.DevFloat, 88, 4,  # RW
     label='e-gun cathode voltage setpoint',
     format='%4.1f', minValue=0, maxValue=50, unit='V',
     events={THRESHOLD: 0.01},
     qualities={WARNING: {ABSOLUTE: {BELOW: 0}}})

# R092 W008 #AO_02: free ---
# R096 W012 #AO_03: free ---

# R100 W016 @HVS_VS ---
AttrRampeable('GUN_HV_V_setpoint',  # voltage (set) is 90 kV fixed
              PyTango.DevFloat, 100, 16,  # RW
              label='HV PS Voltage Setpoint',
              desc='high voltage PS voltage',
              format='%4.1f', minValue=-90, maxValue=0, unit='kV',
              events={THRESHOLD: 0.01},
              rampsDescriptor={DESCENDING: {STEP: 1,  # kV
                                            STEPTIME: 1,  # s
                                            THRESHOLD: -50,  # kV
                                            SWITCH: 'GUN_HV_ONC'},
                               # ASCENDING: {STEP: 5,  # kV
                               #             STEPTIME: 0.5,  # s
                               #             THRESHOLD: -90,  # kV
                               #             SWITCH: 'GUN_HV_ONC'}
                               },
              readback='GUN_HV_V',
              switch='GUN_HV_ONC')
              # User request (back) to limit the device setpoint to avoid
              # below -90kV.

# R104 W020 @TB_GPA ---
Attr('TB_GPA',
     PyTango.DevFloat, 104, 20,  # RW
     label='timer gun pulses attenuation',
     format='%4.1f', minValue=-40, maxValue=0, unit='dB',
     events={THRESHOLD: 0.005})

# R108 W024 @PHS1_PS ---
Attr('PHS1_Phase_setpoint',
     PyTango.DevFloat, 108, 24,  # RW
     label='Phase shifter 1 phase setpoint',
     format='%3.0f', minValue=0, maxValue=160, unit='⁰',
     events={THRESHOLD: 0.01})

# R112 W028 @A0_OP ---
Attr('A0_OP',
     PyTango.DevFloat, 112, 28,  # RW
     label='A0 output power',
     format='%3.0f', minValue=75, maxValue=760, unit='W',
     # specs say maxValue=840, user explicitly reduces it
     events={THRESHOLD: 0.01})

# R116 W032 @TPS0_P ---
# R120 W036 @TPS1_P ---
# R124 W040 @TPS2_P ---
# R128 W044 @TPSX_P ---
for idx, x in enumerate((0, 1, 2, 'X')):
    if x == 0:  # weird exception
        format = '%3.1f'
    else:
        format = '%3.0f'
    Attr('TPS%s_Phase' % (x),
         PyTango.DevFloat,
         116+4*idx, 32+4*idx,  # RW
         label='time phase shifter %s phase' % (x),
         format=format, minValue=0, maxValue=380, unit='⁰',
         events={THRESHOLD: 0.01})

# R132 W048 @AO_12 ---
# R136 W052 @AO_13 ---

# R140 W056 @PHS2_PS ---
Attr('PHS2_Phase_setpoint',
     PyTango.DevFloat, 140, 56,  # RW
     label='Phase shifter 2 phase setpoint',
     format='%3.0f', minValue=0, maxValue=380, unit='⁰',
     events={THRESHOLD: 0.01})

# R144 W060 @ATT2_PS ---
Attr('ATT2_P_setpoint',
     PyTango.DevFloat, 144, 60,  # RW
     label='Attenuator 2',
     desc='Attenuator 2 attenuation (PB2)',
     format='%3.1f', minValue=-10, maxValue=0, unit='dB',
     events={THRESHOLD: 0.01})

# R148 W064 @TB_KAD1 ---
Attr('TB_KA1_Delay',
     PyTango.DevShort, 148, 64,  # RW
     label='timer klystron amplifier 1 delay',
     minValue=1, maxValue=56, unit='ns', events={}, format="%2d")

# R150 W066 @TB_KAD2 ---
Attr('TB_KA2_Delay',
     PyTango.DevShort, 150, 66,  # RW
     label='timer klystron amplifier 2 delay',
     desc='timer klystron amplifier 2 delay (step 32 ns)',
     minValue=544, maxValue=4096, unit='ns', events={}, format="%4d")

# R152 W068 @TB_RF2D ---
Attr('TB_RF2_Delay',
     PyTango.DevShort, 152, 68,  # RW
     label='timer RF2 delay',
     desc='timer RF2 delay (step 8 ns)',
     minValue=512, maxValue=1920, unit='ns', events={}, format="%4d")

# R154 W070 @TB_EGD ---
Attr('TB_Gun_Delay',
     PyTango.DevShort, 154, 70,  # RW
     label='timer e-gun delay',
     desc='timer e-gun delay (step 32 ns)',
     minValue=32, maxValue=4096, unit='ns', events={}, format="%4d")

# R156 W072 @TB_GPI ---
Attr('TB_GPI',
     PyTango.DevShort, 156, 72,  # RW
     label='timer e-gun pulse',
     desc='timer e-gun pulse interval (SBM) / width (MBM)',
     minValue=6, maxValue=1054, unit='ns', events={}, format="%4d")

# R158 W074 @TB_GPN ---
Attr('TB_GPN',
     PyTango.DevShort, 158, 74,  # RW
     label='number of pulses',
     desc='number of pulses in SBM (not use in MBM)',
     minValue=1, maxValue=16, events={}, format="%2d")

# R160 W076 @TB_GPM ---
Attr('TB_GPM',
     PyTango.DevShort, 160, 76,  # RW
     label='timer gated pulse mode',
     desc='timer gated pulse mode: 0:beam on, 1:mix, 2:beam off',
     minValue=0, maxValue=2,
     meanings={0: "beam on",
               1: "mix",
               2: "beam off"},
     events={}, format="%1d")

# R162 W078 @DO_0to7 ---
AttrBit('TB_MBM',
        162, 0, 78,  # RW
        label='timer multi bunch mode',
        desc='timer multi bunch mode enabled; False:SBM, True:MBM',
        meanings={0: 'SBM',
                  1: 'MBM'},
        qualities={0: PyTango.AttrQuality.ATTR_WARNING},
        events={})

AttrBit('GUN_HV_ONC',  # HVS_OC
        162, 2, 78,  # RW
        label='High voltage PS',
        desc='high voltage PS; False:OFF, True:ON',
        meanings={0: 'off',
                  1: 'on'},
        qualities={0: PyTango.AttrQuality.ATTR_WARNING,
                   1: PyTango.AttrQuality.ATTR_VALID},
        events={},
        formula={'read': 'VALUE and Attr[Gun_HV_ST].rvalue == 4'},
        switchDescriptor={ATTR2RAMP: 'GUN_HV_V_setpoint',
                          WHENON:
                          {FROM: 'GUN_HV_V_setpoint_Descending_Threshold'},
                          # from where the WRITEVALUE say
                          # WHENOFF: {TO: 0},  # to where the WRITEVALUE say
                          AUTOSTOP: 'GUN_HV_I_'+AUTOSTOP,
                          # to know where it has the autostop feature
                          },
        readback='GUN_HV_V',
        setpoint='GUN_HV_V_setpoint')

AttrBit('Interlock_RC',  # IU_RST
        162, 3, 78,  # RW
        label='Reset interlocks',
        events={},
        isRst=True
        # reset bits are special because their meaning is 'rising edge'
        )
AttrBit('GUN_LV_ONC',
        162, 5, 78,  # RW
        label='Gun low voltage',
        desc='gun low voltage: False:OFF, True:ON',
        meanings={0: 'off',
                  1: 'on'},
        qualities={WARNING: [0]},
        events={},
        formula={'read':
                 'VALUE and Attr[Gun_ST].rvalue in [1,4,7,8]',
                 'write':
                 'VALUE ^ Attr[GUN_HV_ONC].rvalue',
                 'write_not_allowed':
                     'Filament voltage cannot be switch ON/OFF '
                     'with e-Gun HV ON.'},
        switchDescriptor={ATTR2RAMP: 'GUN_Filament_V_setpoint',
                          WHENON: {FROM: 0},
                          WHENOFF: {TO: 0}},
        readback='GUN_Filament_V',
        setpoint='GUN_Filament_V_setpoint')
        # formula['write'] condition: avoid LV on/off when HV is on
        # that is: allow to turn LV off when HV is off => 0 xor 0: 0
        #          avoid to turn LV off when HV is on  => 0 xor 1: 1
        #          allow to turn LV on  when HV is off => 1 xor 0: 1
        #          avoid to turn LV on  when HV is on  => 1 xor 1: 0

# R163 W079 @DO_8to15 ---
scm_dc_desc = 'screen monitor %d; 0:up, 1:down'
scm_dc_meanings = {0: 'up', 1: 'down'}
AttrBit('SCM1_DC',
        163, 0, 79,  # RW
        label='fs 1 valve',
        desc=scm_dc_desc % 1,
        meanings=scm_dc_meanings,
        events={})
AttrBit('SCM2_DC',
        163, 1, 79,  # RW
        label='fs 2 valve',
        desc=scm_dc_desc % 2,
        meanings=scm_dc_meanings,
        events={})
AttrBit('SCM3_DC',
        163, 2, 79,  # RW
        label='fs 3 valve',
        desc=scm_dc_desc % 3,
        meanings=scm_dc_meanings,
        events={})
scm_lc_desc = 'screen light %d 0:off, 1:on'
scm_lc_meanings = {0: 'off', 1: 'on'}
AttrBit('SCM1_LC',
        163, 3, 79,  # RW
        label='fs 1 light',
        desc=scm_lc_desc % 1,
        meanings=scm_lc_meanings,
        events={})
AttrBit('SCM2_LC',
        163, 4, 79,  # RW
        label='fs 2 light',
        desc=scm_lc_desc % 2,
        meanings=scm_lc_meanings,
        events={})
AttrBit('SCM3_LC',
        163, 5, 79,  # RW
        label='fs 3 light',
        desc=scm_lc_desc % 3,
        meanings=scm_lc_meanings,
        events={})

# R164 W080 @Local_Lock ---

# AttrPLC(HeartBeat, Lock_ST, rLockingAddr, rLockingBit, wLockingAddr,
#         wLockingBit)
AttrPLC(72, 82, 164, 0, 80, 0)

AttrLogic('ka1_ic',
          logic={'SF6_P1_ST': [1], 'W1_UF': [1], 'W2_UF': [1],
                 'RL1_UF': [1], 'RL2_UF': [1]},
          desc='Klystron 1 interlock',
          label='Klystron 1 interlock',
          events={},
          )

AttrLogic('ka2_ic',
          logic={'SF6_P2_ST': [1], 'W3_UF': [1], 'RL3_UF': [1]},
          desc='Klystron 2 interlock',
          label='Klystron 2 interlock',
          events={},
          )

# AttrLogic('any_interlock',
#           logic={'IU_RDY': [True],
#                  'KA_ENB': [True],
#                  'ka2_ic': [True],
#                  'MG_IS': [True],
#                  'ka1_ic': [True],
#                  'UT_IS': [True],
#                  #'AC_IS': [True],  # It's in PLC2
#                  'TL_VOK': [True],
#                  #'VC_OK': [True],  # It's in PLC2
#                  'EG_ENB': [True],
#                  'GM_DI': [True],
#                  'KA2_OK': [True],
#                  'KA1_OK': [True],
#                  'LI_OK': [True]},
#           desc='any interlock is set',
#           label='any interlock is set',
#           events={},
#           )

AttrEnumeration('ATT2_u')
AttrEnumeration('GUN_Cathode_u')
AttrEnumeration('GUN_CDB_u')
AttrEnumeration('GUN_HVps_u')
AttrEnumeration('TU_u')
AttrEnumeration('A0_u')
AttrEnumeration('LLRF_u')
