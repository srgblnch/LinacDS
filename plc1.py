# -*- coding: utf-8 -*-
# plc1.py
# This file is part of tango-ds (http://sourceforge.net/projects/tango-ds/)
#
# tango-ds is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# tango-ds is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with tango-ds.  If not, see <http://www.gnu.org/licenses/>.

'''Schema of the attributes:
   Attr(name,             :Name of the dynamic attribute
        T,                :Tango type of the attribute
        read_addr=None,   :PLC register address for read operation
        write_addr=None,  :PLC register address for write operation
        isa=None,         :??TODO
        **kwargs          :

   AttrBit(name,            :Name of the dynamic attribute
           read_addr=None,  :PLC register address for read operation
           bitno=0,         :Bit of the read word representing this boolean
           write_addr=None, :PLC register address for write operation
           write_bit=None,  :Bit to the write in the word for this boolean
           **kwargs         :
   
   kwargs: l=None,       :label of the attribute
           d=None,       :description of the attribute
           min=None,     :minimum value allowed
           max=None,     :maximum value allowed
           unit=None,    :attribute unit
           format=None   :In the number case (int/float) its precision
           events={}     :dictionary where its existence will set up attr events
                          and its content will configure their behaviour
           qualities={}  :dictionary where the key represents the available 
                          qualities and the items the conditions to set them.
                          Important: alarm > warning > changing
'''

#----## Read only attributes

#---- R000 @EG_FVM
Attr('GUN_Filament_V',
     PyTango.DevFloat,0,#RO
     l='e-gun filament voltage monitor',
     format='%4.1f',min=0,max=10,unit='V',
     events={THRESHOLD:0.01},
     qualities={WARNING:{ABSOLUTE:{BELOW:0.0}}})

#---- R004 @EG_FCM
Attr('GUN_Filament_I',
     PyTango.DevFloat,4,#RO
     l='e-gun filament current',
     format='%4.1f',min=0,max=5,unit='A',
     events={THRESHOLD:0.01},
     qualities={WARNING:{ABSOLUTE:{BELOW:0.0}}})

#---- R008 @EG_KVM
Attr('GUN_Kathode_V',
     PyTango.DevFloat,8,#RO
     l='e-gun cathode voltage monitor',
     format='%4.1f',min=0,max=50,unit='V',
     events={THRESHOLD:0.01},
     qualities={WARNING:{ABSOLUTE:{BELOW:0.0}}})

#---- R012 @EG_KTM
Attr('GUN_Kathode_T',
     PyTango.DevFloat,12,#RO
     l='e-gun cathode temperature',
     format='%4.1f',min=0,max=50,unit='⁰C',
     events={THRESHOLD:0.01},
     qualities={WARNING:{ABSOLUTE:{BELOW:25.0,
                                  ABOVE:32.0}}})

#---- R016 @AI_04: free
#---- R020 @AI_05: free
#---- R024 @AI_06: free
#---- R028 @AI_07: free

#---- R032 @HVS_VM
Attr('GUN_HV_V',
     PyTango.DevFloat,32,#RO
     l='HV PS Voltage',
     d='high voltage PS voltage',
     format='%4.1f',min=-100,max=0,unit='kV',
     events={THRESHOLD:0.01})

#---- R036 @HVS_CM
Attr('GUN_HV_I',
     PyTango.DevFloat,36,#RO
     l='High voltage PS current',
     d='high voltage PS current (leakage current)',
     format='%4.1f',min=-600,max=1,unit='μA',
     events={THRESHOLD:0.01},
     qualities={WARNING:{ABSOLUTE:{ABOVE:1.0,
                                   BELOW:-20.0}}},
     autoStop={BELOW:-20,
               INTEGRATIONTIME:1,#s
               SWITCHDESCRIPTOR:'GUN_HV_ONC'})

#---- R040 @PHS1_PM
Attr('PHS1_Phase',
     PyTango.DevFloat,40,#RO
     l='Phase shifter 1 phase monitor',
     format='%4.1f',min=0,max=160,unit='⁰',
     events={THRESHOLD:0.01})

#---- R044 @Spare_1: CH3 spare

#---- R48 @SF6P1M
Attr('SF6_P1',
     PyTango.DevFloat,48,#RO
     l='SF6 pressure 1',
     format='%4.2f',min=-1,max=5,unit='bar',
     events={THRESHOLD:0.001},
     qualities={WARNING:{ABSOLUTE:{BELOW:2.9,
                                  ABOVE:3.0}}})

#---- R052 @SF6P2M
Attr('SF6_P2',
     PyTango.DevFloat,52,#RO
     l='SF6 pressure 2',
     format='%4.2f',min=-1,max=5,unit='bar',
     events={THRESHOLD:0.001},
     qualities={WARNING:{ABSOLUTE:{BELOW:2.9,
                                  ABOVE:3.0}}})

#---- R056 @PHS2_PM
Attr('PHS2_Phase',
     PyTango.DevFloat,56,#RO
     l='Phase shifter 2 phase monitor',
     format='%4.1f',min=0,max=380,unit='⁰',
     events={THRESHOLD:0.01})

#---- R060 @ATT2_PM
Attr('ATT2_P',
     PyTango.DevFloat,60,#RO
     l='Attenuator 2 monitor',
     d='Attenuator 2 monitor attenuation (PB2)',
     format='%4.1f',min=-10,max=10,unit='dB',
     events={THRESHOLD:0.01})

#---- R064 @AI_15: free

#---- R068 @DI_0to7
AttrBit('TB_ST',
        68,0,#RO
        l='Timer Status State',
        meanings={0:'off',
                  1:'ready'},
        qualities={WARNING:[0]},
        events={})
AttrBit('A0_ST',
        68,4,#RO
        l='500MHz amplifier status',
        meanings={0:'off',
                  1:'ready'},
        qualities={WARNING:[0]},
        events={})
AttrBit('RFS_ST',
        68,5,#RO
        l='RF source Status',
        meanings={0:'off',
                  1:'ready'},
        qualities={WARNING:[0]},
        events={})

#---- R069 @DI_8to15

#---- R070 @DI_16to23
AttrBit('EG_ENB',
        70,0,#RO
        l='Electron gun enabled (PSS)',
        meanings={0:'disabled',
                  1:'enabled'},
        qualities={WARNING:[0]},
        events={})
AttrBit('KA_ENB',
        70,1,#RO
        l='Klystron amplifier enabled (PSS)',
        meanings={0:'disabled',
                  1:'enabled'},
        qualities={WARNING:[0]},
        events={})
AttrBit('TL_VOK',
        70,2,#RO
        l='Transfer line vacuum OK (PSS)',
        meanings={0:'bad vacuum',
                  1:'good vacuum'},
        qualities={WARNING:[0]},
        events={})
AttrBit('IU_RDY',
        70,5,#RO
        l='Interlock unit ready',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('W1_UF',
        70,6,#RO
        l='Window 1 underflow state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('W2_UF',
        70,7,#RO
        l='Window 2 underflow state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})

#---- R71 @DI_24to31
AttrBit('W3_UF',
        71,0,#RO
        l='Window 3 underflow state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('RL1_UF',
        71,1,#RO
        l='Resistor load 1 underflow state',
        meanings={0:'underflow',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('RL2_UF',
        71,2,#RO
        l='Resistor load 2 underflow state',
        meanings={0:'underflow',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('RL3_UF',
        71,3,#RO
        l='Resistor load 3 underflow state',
        meanings={0:'underflow',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('UT_IS',
        71,4,#RO
        l='Utilities Interlock state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('MG_IS',
        71,5,#RO
        l='Magnet Interlock state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('GM_DI',
        71,6,#RO
        l='Gun Modulator door interlock',
        meanings={0:'door open',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('LI_VOK',
        71,7,#RO
        l='Linac Vacuum OK',
        meanings={0:'bad vacuum',
                  1:'good vacuum'},
        qualities={WARNING:[0]},
        events={})

#---- R072 @DI_Comm
#AttrBit('HeartBeat',#Heartbeat defined at the end together with lockers
#        72,0,#RO
#        d='PLC 1 heart beat')
AttrBit('PLC1_PR',
        72,2,#RO
        l='PLC1 profibus receive status',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('PLC1_PS',
        72,4,#RO
        l='PLC1 profibus send status',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})

#---- R073 @DI_ITLK_K
AttrBit('SF6_P1_ST',
        73,0,#RO
        l='SF6 pressure 1 state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('SF6_P2_ST',
        73,1,#RO
        l='SF6 pressure 2 state',
        meanings={0:'fault',
                  1:'normal'},
        qualities={WARNING:[0]},
        events={})
AttrBit('KA1_OK',#KA1_EN
        73,2,#RO
        l='klystron 1 ready',
        events={})
AttrBit('KA2_OK',#KA2_EN
        73,3,#RO
        l='klystron 2 ready',
        events={})
AttrBit('LI_OK',#LI_RDY
        73,4,#RO
        l='Linac system ready',
        events={})
AttrBit('RF_OK',#RF_ENB
        73,5,#RO
        l='RF ready',
        events={})

#---- R074 @HV_PS_ST
Attr('Gun_HV_ST',
     PyTango.DevUChar,74,#RO
     l='High voltage PS status',
     d='high voltage PS status: 0:undefined, '\
                               '1:off, '\
                               '2:locked, '\
                               '3: fault, '\
                               '4:ready, '\
                               '5: unlocked',
     meanings={0:'undefined',
               1:'off',
               2:'locked',
               3:'fault',
               4:'ready',
               5:'unlocked'},
     qualities={ALARM:[0,3,5],
                WARNING:[1,2,5]},
     events={})

#---- R075 @E_GUN_ST
Attr('Gun_ST',
     PyTango.DevUChar,75,#RO
     l='e-gun low voltage status',
     d='e-gun low voltage status: 0:undefined, '\
                                 '1:off'\
                                 '2:bad vacuum'\
                                 '3:cathode voltage fault'\
                                 '4:filament current fault'\
                                 '5:heating running'\
                                 '6:filament voltage fault'\
                                 '7:cathode over temperature'\
                                 '8:ready',
     #modification in the meaning because documentation looks wrong
     meanings={0:'undefined',
               1:'off',
               2:'bad vacuum',
               3:'cathode voltage fault',
               4:'Heating',#'filament current fault',
               5:'filament current fault',#'heating running',
               6:'filament voltage fault',
               7:'cathode over temperature',
               8:'ready'},
     qualities={ALARM:[0],
                WARNING:[1,2,3,5,6,7],
                CHANGING:[4]},
     events={})

AttrLogic('Gun_ready',
          logic={'Gun_ST':[1,8]},
          d='e-gun low voltage ready',
          l='e-gun low voltage ready',
          events={},
          )

#---- R076 @SCM_1_ST
Attr('SCM1_ST',
     PyTango.DevUChar,76,#RO
     l='fs 1 status',
     d='screen monitor 1 status: 0:undefined'\
                                '1:moving'\
                                '2:up'\
                                '3:down'\
                                '4:fault',
     meanings={0:'undefined',
               1:'moving',
               2:'up',
               3:'down',
               4:'fault'},
     qualities={ALARM:[0],
                WARNING:[3,4],
                CHANGING:[1]},
     events={})

AttrLogic('SCM1_alert',
          logic={'SCM1_ST':[3,4]},
          d='screen monitor 1 alert',
          l='screen monitor 1 alerts',
          events={},
          )


#---- R077 @SCM_2_ST
Attr('SCM2_ST',
     PyTango.DevUChar,77,#RO
     l='fs 2 status',
     d='screen monitor 2 status: 0:undefined'\
                                '1:moving'\
                                '2:up'\
                                '3:down'\
                                '4:fault',
     meanings={0:'undefined',
               1:'moving',
               2:'up',
               3:'down',
               4:'fault'},
     qualities={ALARM:[0],
                WARNING:[3,4],
                CHANGING:[1]},
     events={})

AttrLogic('SCM2_alert',
          logic={'SCM2_ST':[3,4]},
          d='screen monitor 2 alert',
          l='screen monitor 2 alerts',
          events={},
          )

#---- R078 @SCM_3_ST
Attr('SCM3_ST',
     PyTango.DevUChar,78,#RO
     l='fs 3 status',
     d='screen monitor 3 status: 0:undefined'\
                                '1:moving'\
                                '2:up'\
                                '3:down'\
                                '4:fault',
     meanings={0:'undefined',
               1:'moving',
               2:'up',
               3:'down',
               4:'fault'},
     qualities={ALARM:[0],
                WARNING:[3,4],
                CHANGING:[1]},
     events={})

AttrLogic('SCM3_alert',
          logic={'SCM3_ST':[3,4]},
          d='screen monitor 3 alert',
          l='screen monitor 3 alerts',
          events={},
          )

#---- R079 @PHS1_ST
Attr('PHS1_ST',
     PyTango.DevUChar,79,#RO
     l='phase shifter 1 status',
     d='phase shifter 1 status: 0:undefined'\
                               '1:unset'\
                               '2:ready'\
                               '3:in limit fault'\
                               '4:out limit fault'\
                               '5:timeout fault',
     meanings={0:'undefined',
               1:'unset',
               2:'ready',
               3:'in limit fault',
               4:'out limit fault',
               5:'timeout fault'},
     qualities={ALARM:[0],
                WARNING:[1,3,4,5]},
     events={})

AttrLogic('phs1_ready',
          logic={'PHS1_ST':[2]},
          d='phase shifter 1 ready',
          l='phase shifter 1 ready',
          events={},
          )

#---- R080 @PHS2_ST
Attr('PHS2_ST',
     PyTango.DevUChar,80,#RO
     l='phase shifter 2 status',
     d='phase shifter 2 status: 0:undefined'\
                               '1:unset'\
                               '2:ready'\
                               '3:in limit fault'\
                               '4:out limit fault'\
                               '5:timeout fault',
     meanings={0:'undefined',
               1:'unset',
               2:'ready',
               3:'in limit fault',
               4:'out limit fault',
               5:'timeout fault'},
     qualities={ALARM:[0],
                WARNING:[1,3,4,5]},
     events={})

AttrLogic('phs2_ready',
          logic={'PHS2_ST':[2]},
          d='phase shifter 2 ready',
          l='phase shifter 2 ready',
          events={},
          )

#---- R081 @ATT2_ST
Attr('ATT2_ST',
     PyTango.DevUChar,81,#RO
     l='attenuator 2 status',
     d='attenuator 2 status: 0:undefined'\
                            '1:unset'\
                            '2:ready'\
                            '3:in limit fault'\
                            '4:out limit fault'\
                            '5:timeout fault',
     meanings={0:'undefined',
                1:'unset',
                2:'ready',
                3:'in limit fault',
                4:'out limit fault',
                5:'timeout fault'},
     qualities={ALARM:[0],
                WARNING:[1,3,4,5]},
     events={})

AttrLogic('att2_ready',
          logic={'ATT2_ST':[2]},
          d='Attenuator 2 ready',
          l='Attenuator 2 ready',
          events={},
          )

#---- R082 @Comm_ST #defined with the heardbeat at the end of this file

#---- R083 @??

#---- ## Read/Write attributes

#---- R084 W000 @EG_FVS
AttrRampeable('GUN_Filament_V_setpoint',
              PyTango.DevFloat,84,0,#RW
              l='e-gun filament voltage setpoint',
              format='%4.1f',min=0,max=10,unit='V',
              events={THRESHOLD:0.01},
              qualities={WARNING:{ABSOLUTE:{BELOW:0}}},
              rampsDescriptor = {DESCENDING:{STEP:1,#V
                                             STEPTIME:1,#s
                                             THRESHOLD:10,#V
                                             SWITCH:'GUN_LV_ONC'},
                                 ASCENDING:{STEP:1,#V
                                            STEPTIME:1,#s
                                            THRESHOLD:0,#V
                                            SWITCH:'GUN_LV_ONC'}})

#---- R088 W004 @EG_KVS
Attr('GUN_Kathode_V_setpoint',
     PyTango.DevFloat,88,4,#RW
     l='e-gun cathode voltage setpoint',
     format='%4.1f',min=0,max=50,unit='V',
     events={THRESHOLD:0.01},
     qualities={WARNING:{ABSOLUTE:{BELOW:0}}})

#---- R092 W008 #AO_02: free
#---- R096 W012 #AO_03: free

#---- R100 W016 @HVS_VS
AttrRampeable('GUN_HV_V_setpoint',# voltage (set) is 90 kV fixed
              PyTango.DevFloat,100,16,#RW
              l='HV PS Voltage Setpoint',
              d='high voltage PS voltage',
              format='%4.1f',min=-90,max=0,unit='kV',
              events={THRESHOLD:0.01},
              rampsDescriptor = {DESCENDING:{STEP:1,#kV
                                             STEPTIME:1,#s
                                             THRESHOLD:-50,#kV
                                             SWITCH:'GUN_HV_ONC'},
                                 ASCENDING:{STEP:5,#kV
                                            STEPTIME:0.5,#s
                                            THRESHOLD:-90,#kV
                                            SWITCH:'GUN_HV_ONC'}})
     #User request (back) to limit the device setpoint to avoid below -90kV.

#---- R104 W020 @TB_GPA
Attr('TB_GPA',
     PyTango.DevFloat,104,20,#RW
     l='timer gun pulses attenuation',
     format='%4.1f',min=-40,max=0,unit='dB',
     events={THRESHOLD:0.01})

#---- R108 W024 @PHS1_PS
Attr('PHS1_Phase_setpoint',
     PyTango.DevFloat,108,24,#RW
     l='Phase shifter 1 phase setpoint',
     format='%3.0f',min=0,max=160,unit='⁰',
     events={THRESHOLD:0.01})

#---- R112 W028 @A0_OP
Attr('A0_OP',
     PyTango.DevFloat,112,28,#RW
     l='A0 output power',
     format='%3.0f',min=75,max=760,unit='W',
     #specs say max=840, user explicitly reduces it
     events={THRESHOLD:0.01})

#---- R116 W032 @TPS0_P
#---- R120 W036 @TPS1_P
#---- R124 W040 @TPS2_P
#---- R128 W044 @TPSX_P
for idx,x in enumerate((0,1,2,'X')):
    if x == 0:#weird exception
        format = '%3.1f'
    else:
        format = '%3.0f'
    Attr('TPS%s_Phase'%(x),
         PyTango.DevFloat,
         116+4*idx,32+4*idx,#RW
         l='time phase shifter %s phase'%(x),
         format=format,min=0,max=380,unit='⁰',
         events={THRESHOLD:0.01})

#---- R132 W048 @AO_12
#---- R136 W052 @AO_13

#---- R140 W056 @PHS2_PS
Attr('PHS2_Phase_setpoint',
     PyTango.DevFloat,140,56,#RW
     l='Phase shifter 2 phase setpoint',
     format='%3.0f',min=0,max=380,unit='⁰',
     events={THRESHOLD:0.01})

#--- R144 W060 @ATT2_PS
Attr('ATT2_P_setpoint',
     PyTango.DevFloat,144,60,#RW
     l='Attenuator 2',
     d='Attenuator 2 attenuation (PB2)',
     format='%3.1f',min=-10,max=0,unit='dB',
     events={THRESHOLD:0.01})

#---- R148 W064 @TB_KAD1
Attr('TB_KA1_Delay',
     PyTango.DevShort,148,64,#RW
     l='timer klystron amplifier 1 delay',
     min=1,max=56,unit='μs',
     events={})

#---- R150 W066 @TB_KAD2
Attr('TB_KA2_Delay',
     PyTango.DevShort,150,66,#RW
     l='timer klystron amplifier 2 delay',
     d='timer klystron amplifier 2 delay (step 32 ns)',
     min=544,max=4096,unit='ns',
     events={})

#---- R152 W068 @TB_RF2D
Attr('TB_RF2_Delay',
     PyTango.DevShort,152,68,#RW
     l='timer RF2 delay',
     d='timer RF2 delay (step 8 ns)',
     min=512,max=1920,unit='ns',
     events={})

#---- R154 W070 @TB_EGD
Attr('TB_Gun_Delay',
     PyTango.DevShort,154,70,#RW
     l='timer e-gun delay',
     d='timer e-gun delay (step 32 ns)',
     min=32,max=4096,unit='ns',
     events={})

#---- R156 W072 @TB_GPI
Attr('TB_GPI',
     PyTango.DevShort,156,72,#RW
     l='timer e-gun pulse',
     d='timer e-gun pulse interval (SBM) / width (MBM)',
     min=6,max=1054,unit='ns',
     events={})

#---- R158 W074 @TB_GPN
Attr('TB_GPN',
     PyTango.DevShort,158,74,#RW
     l='number of pulses',
     d='number of pulses in SBM (not use in MBM)',
     min=1,max=16,
     events={})

#---- R160 W076 @TB_GPM
Attr('TB_GPM',
     PyTango.DevShort,160,76,#RW
     l='timer gated pulse mode',
     d='timer gated pulse mode: 0:beam on, 1:mix, 2:beam off',
     min=0,max=2,
     meanings={0:"beam on",
               1:"mix",
               2:"beam off"},
     events={})

#---- R162 W078 @DO_0to7
AttrBit('TB_MBM',
        162,0,78,#RW
        l='timer multi bunch mode',
        d='timer multi bunch mode enabled; False:SBM, True:MBM',
        meanings={0:'SBM',
                  1:'MBM'},
        qualities={0:PyTango.AttrQuality.ATTR_WARNING},
        events={})
AttrBit('GUN_HV_ONC',#HVS_OC
        162,2,78,#RW
        l='High voltage PS',
        d='high voltage PS; False:OFF, True:ON',
        meanings={0:'off',
                  1:'on'},
        qualities={0:PyTango.AttrQuality.ATTR_WARNING,
                   1:PyTango.AttrQuality.ATTR_VALID},
        events={},
        formula={'read':'VALUE and '\
                 'self._plcAttrs[\'Gun_HV_ST\'][\'read_value\'] == 4'},
        switchDescriptor={ATTR2RAMP:'GUN_HV_V_setpoint',
                          WHENON:{FROM:0},#to where the WRITEVALUE say
                          WHENOFF:{TO:0}}#from where the WRITEVALUE say
        )
AttrBit('Interlock_RC',#IU_RST
        162,3,78,#RW
        l='Reset interlocks',
        events={},
        isRst=True)#reset bits are special because their meaning is 'rising edge'
AttrBit('GUN_LV_ONC',
        162,5,78,#RW
        l='Gun low voltage',
        d='gun low voltage: False:OFF, True:ON',
        meanings={0:'off',
                  1:'on'},
        qualities={WARNING:[0]},
        events={},
        formula={'read':
                  'VALUE and '\
                  'self._plcAttrs[\'Gun_ST\'][\'read_value\'] in [1,4,7,8]',
                 'write':
                  'VALUE ^ self._plcAttrs[\'GUN_HV_ONC\'][\'read_value\']',
                 'write_not_allowed':'Filament voltage cannot be switch '\
                                                   'ON/OFF with e-Gun HV ON.'},
        switchDescriptor={ATTR2RAMP:'GUN_Filament_V_setpoint',
                          WHENON:{FROM:0},
                          WHENOFF:{TO:0}}
        )
        #formula['write'] condition: avoid LV on/off when HV is on
        #that is: allow to turn LV off when HV is off => 0 xor 0: 0
        #         avoid to turn LV off when HV is on  => 0 xor 1: 1
        #         allow to turn LV on  when HV is off => 1 xor 0: 1
        #         avoid to turn LV on  when HV is on  => 1 xor 1: 0

#---- R163 W079 @DO_8to15
scm_dc_desc = 'screen monitor %d; 0:up, 1:down'
scm_dc_meanings = {0:'up',1:'down'}
AttrBit('SCM1_DC',
        163,0,79,#RW
        l='fs 1 valve',
        d=scm_dc_desc % 1,
        meanings=scm_dc_meanings,
        events={})
AttrBit('SCM2_DC',
        163,1,79,#RW
        l='fs 2 valve',
        d=scm_dc_desc % 2,
        meanings=scm_dc_meanings,
        events={})
AttrBit('SCM3_DC',
        163,2,79,#RW
        l='fs 3 valve',
        d=scm_dc_desc % 3,
        meanings=scm_dc_meanings,
        events={})
scm_lc_desc = 'screen light %d 0:off, 1:on'
scm_lc_meanings = {0:'off',1:'on'}
AttrBit('SCM1_LC',
        163,3,79,#RW
        l='fs 1 light',
        d=scm_lc_desc % 1,
        meanings=scm_lc_meanings,
        events={})
AttrBit('SCM2_LC',
        163,4,79,#RW
        l='fs 2 light',
        d=scm_lc_desc % 2,
        meanings=scm_lc_meanings,
        events={})
AttrBit('SCM3_LC',
        163,5,79,#RW
        l='fs 3 light',
        d=scm_lc_desc % 3,
        meanings=scm_lc_meanings,
        events={})

#---- R164 W080 @Local_Lock

#AttrPLC(HeartBeat,Lock_ST,rLockingAddr,rLockingBit,wLockingAddr,wLockingBit)
AttrPLC(72, 82,164,0,80,0)

AttrLogic('ka1_ic',
          logic={'SF6_P1_ST':[1],
                 'W1_UF':[1],'W2_UF':[1],
                 'RL1_UF':[1],'RL2_UF':[1]},
          d='Klystron 1 interlock',
          l='Klystron 1 interlock',
          events={},
          )

AttrLogic('ka2_ic',
          logic={'SF6_P2_ST':[1],'W3_UF':[1],'RL3_UF':[1]},
          d='Klystron 2 interlock',
          l='Klystron 2 interlock',
          events={},
          )
