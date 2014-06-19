# -*- coding: utf-8 -*-
# plc2.py
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
           formula={}    :dictionary with keys 'read' and 'write' were they 
                          contain an string that could be introduced in 
                          an eval() call with the keyword VALUE as the read or
                          write transformation.
'''

#----## Read only attributes

#---- R000 @IP1_PM
#---- R004 @IP2_PM
#---- R008 @IP3_PM
#---- R012 @IP4_PM
#---- R016 @IP5_PM
#---- R020 @IP6_PM
#---- R024 @IP7_PM
#---- R028 @IP8_PM
#---- R032 @IP9_PM
for i in range(9):
    number = i+1
    Attr('IP%d_P'%(number),
         PyTango.DevFloat,4*i,#RO
         l='ion pump %d pressure monitor'%(number),
         format='%2.1e',min=1e-11,max=1e0,unit='mbar',
         events={},
         qualities={'warning':{'abs':{'above':1e-7}}})

#---- R036 @HG1_PM
#---- R040 @HG2_PM
#---- R044 @HG3_PM
#---- R048 @HG4_PM
#---- R052 @HG5_PM
for i in range(5):
    number = i+1
    Attr('HVG%d_P'%(number),
         PyTango.DevFloat,36+4*i,#RO
         l='high vacuum gauge %d pressure monitor'%(number),
         format='%2.1e',min=1e-11,max=1,unit='mbar',
         events={},
         qualities={'warning':{'abs':{'above':1e-7}}})

#---- R056 @CL1_TM
#---- R060 @CL2_TM
#---- R064 @CL3_TM
for i in range(3):
    number = i+1
    Attr('CL%d_T'%(number),
         PyTango.DevFloat,56+4*i,
         l='cooling loop %d temperature monitor'%(number),
         format='%4.2f',min=0,max=50,unit='⁰C',
         events={'Threshold':0.001})

#---- R068 @CL1_PWDM
#---- R072 @CL2_PWDM
#---- R076 @CL3_PWDM
for i in range(3):
    number = i+1
    Attr('CL%d_PWD'%(number),
         PyTango.DevFloat,68+4*i,
         l='cooling loop %d power drive monitor'%(number),unit='%',
         format='%4.1f',min=0,max=100,
         events={'Threshold':0.1},
         qualities={'warning':{'abs':{'below':15,
                                      'above':80}}})

#---- R080 @spare: was CL4_TM

#---- R084 @DI_0to7
for i in range(8):
    number = i+1
    AttrBit('IP%d_ST'%(number),
            84,i,#RO
            l='ion pump %d status'%(number),
            meanings={0:'off',
                      1:'on'},
            qualities={'warning':[0]},
            events={})

#---- R085 @DI_8to15
AttrBit('IP9_ST',
        85,0,#RO
        l='ion pump 9 status',
        meanings={0:'off',
                  1:'on'},
        qualities={'warning':[0]},
        events={})
AttrBit('VC_OK',#LI_VOK
        85,1,#RO
        l='linac vacuum okay',
        meanings={0:'bad vacuum',
                  1:'good vacuum'},
        qualities={'warning':[0]},
        events={})
for i in range(5):
    number = i+1
    AttrBit('HVG%d_IS'%(number),
            85,2+i,#RO
            l='high vacuum gauge %d interlock'%(number),
            d='high vacuum gauge %d interlock; False:fault, True:ready'%(number),
            meanings={0:'fault',
                      1:'ready'},
            qualities={'warning':[0]},
            events={})
AttrBit('IP1_IS',
        85,7,#RO
        l='ion pump 1 interlock',
        d='ion pump 1 interlock; False:fault, True:ready',
        meanings={0:'fault',
                  1:'ready'},
        qualities={'warning':[0]},
        events={})

#---- R086 @DI_Spare
for i in range(8):
    number = i+2
    AttrBit('IP%d_IS'%(number),
            86,i,#RO
            l='ion pump %d interlock'%(number),
            d='ion pump %d interlock; False:fault, True:ready'%(number),
            meanings={0:'fault',
                      1:'ready'},
            qualities={'warning':[0]},
            events={})

#---- R087 @CV_ST
VALVE_STATUS = {0:'undefined',
                1:'moving',
                2:'opened',
                3:'closed',
                4:'fault'}
VALVE_QUALITIES={'alarm':[0],
                 'warning':[3,4],
                 'changing':[1]}
Attr('VCV_ST',
     PyTango.DevUChar,87,#RO
     l='collimator valve state',
     d='collimator valve state'+john(VALVE_STATUS),
     meanings=VALVE_STATUS,
     qualities=VALVE_QUALITIES,
     events={})

#---- R088 @VV1_ST
#---- R089 @VV2_ST
#---- R090 @VV3_ST
#---- R091 @VV4_ST
#---- R092 @VV5_ST
#---- R093 @VV6_ST
#---- R094 @VV7_ST
for i in range(7):
    number = i+1
    Attr('VV%d_ST'%number,
         PyTango.DevUChar,88+i,#RO
         l='vacuum valve %d state'%(number),
         d='vacuum valve %d state'%(number)+john(VALVE_STATUS),
         meanings=VALVE_STATUS,
         qualities=VALVE_QUALITIES,
         events={})

#---- R095 @Comm_ST #defined with the heardbeat at the end of this file

#---- R096 @CL1_ST
cl1_meaning = {0:'primary underflow',
               1:'off',
               2:'fault',
               3:'prebuncher 1 underflow',
               4:'prebuncher 2 underflow',
               5:'buncher underflow',
               6:'running',
               7:'cooling down (5 min)'}
cl1_qualities = {'warning':[0,1,2,3,4,5],
                 'changing':[5,7]}
Attr('CL1_ST',
     PyTango.DevUChar,96,#RO
     l='cooling loop 1 status',
     d='cooling loop 1 status' + john(cl1_meaning),
     meanings=cl1_meaning,
     qualities=cl1_qualities,
     events={})
AttrLogic('cl1_ready',
          logic={'CL1_ST':[1,6]},
          d='cooling loop 1 ready',
          l='cooling loop 1 ready',
          events={},
          )

#---- R097 @CL2_ST
cl2_meaning = {0:'primary underflow',
               1:'off',
               2:'fault',
               3:'accelerating section 1 underflow',
               4:'running',
               5:'cooling down (5 min)'}
cl2_qualities = {'alarm':[2],
                 'warning':[0,1,3],
                 'changing':[5]}
Attr('CL2_ST',
     PyTango.DevUChar,97,#RO
     l='cooling loop 2 status',
     d='cooling loop 2 status' + john(cl2_meaning),
     meanings=cl2_meaning,
     qualities=cl2_qualities,
     events={})
AttrLogic('cl2_ready',
          logic={'CL2_ST':[1,4]},
          d='cooling loop 2 ready',
          l='cooling loop 2 ready',
          events={},
          )

#---- R098 @CL3_ST
cl3_meaning = {0:'primary underflow',
               1:'off',
               2:'fault',
               3:'accelerating section 2 underflow',
               4:'running',
               5:'cooling down (5 minutes)'}
cl3_qualities = {'alarm':[2],
                 'warning':[0,1,3],
                 'changing':[5]}
Attr('CL3_ST',
     PyTango.DevUChar,98,#RO
     l='cooling loop 3 status',
     d='cooling loop 3 status' + john(cl3_meaning),
     meanings=cl3_meaning,
     qualities=cl3_qualities,
     events={})
AttrLogic('cl3_ready',
          logic={'CL3_ST':[1,4]},
          d='cooling loop 3 ready',
          l='cooling loop 3 ready',
          events={},
          )

#---- R099 @DI_Comm
#AttrBit('HeartBeat',#Heartbeat defined at the end together with lockers
#        99,0,#RO
#        d='PLC 2 heart beat')
AttrBit('AC_IS',
        99,1,
        l='compressed air interlock state',
        meanings={0:'fault',
                  1:'good'},
        qualities={'warning':[0]},
        events={})

#---- ## Read/Write attributes

#---- R100 W000 @CL1_TS
#---- R104 W004 @CL2_TS
#---- R108 W008 @CL3_TS
for i in range(3):
    number=i+1
    Attr('CL%d_T_setpoint'%(number),
         PyTango.DevFloat,100+4*i,4*i,
         l='cooling loop %d temperature setpoint'%(number),
         format='%4.2f',unit='⁰C',min=0,max=50,
         events={'Threshold':0.01},
         qualities={'changing':{'rel':0.5},
                    'warning':{'abs':{'above':40,'below':20}},
                    'alarm':{'abs':{'above':45,'below':15}}})

#---- R112 W012 @AO_03: spare

#---- R116 W016 @DO_0to7
AttrBit('VCV_ONC',
        116,0,16,
        l='collimator valve open',
        meanings={0:'close',
                  1:'open'},
        qualities={'warning':[0]},
        events={},
        formula={'read':'VALUE and '\
               'not self._plcAttrs[\'VCV_ST\'][\'read_value\'] == 4'}
        )
for i in range(7):
    number=i+1
    AttrBit('VV%d_OC'%(number),
            116,1+i,16,
            l='vacuum valve %d open'%(number),
            meanings={0:'close',
                       1:'open'},
            qualities={'warning':[0]},
            events={},
            formula={'read':'VALUE and '\
               'not self._plcAttrs[\'VV%d_ST\'][\'read_value\'] == 4'%(number)},
            )
    
GrpBit('VVall_OC',
       read_addr_bit_pairs=[(116,1),(116,2),(116,3),(116,4),(116,5),(116,6),(116,7)],
       write_addr_bit_pairs=[(16,1),(16,2),(16,3),(16,4),(16,5),(16,6),(16,7)],
       l='all vacuum valves open',
       meanings={0:'close',
                 1:'open'},
       qualities={'warning':[0]},
       events={},
       )

#---- R117 W017 @DO_8to15
AttrBit('Util_Interlock_RC',
        117,0,17,
        l='interlock reset',
        #---- FIXME: reset bits are special because their meaning is 'rising edge'
        d='utilities interlock reset command',
        events={},
        isRst=True)
AttrBit('VC_Interlock_RC',
        117,1,17,
        l='vacuum reset',
        #---- FIXME: reset bits are special because their meaning is 'rising edge'
        d='vacuum reset command',
        events={},
        isRst=True,
        activeRst_t = 3.200)
for i in range(3):
    number=i+1
    AttrBit('CL%d_ONC'%(number),
            117,i+2,17,
            l='cooling loop %d on'%(number),
            meanings={0:'off',
                      1:'on'},
            qualities={'warning':[0]},
            events={},
            formula={'read':'VALUE and '\
                     'self._internalAttrs[\'cl%d_ready\'][\'read_value\'] '\
                     '== True'%(number)}
            )

#---- R118 W018 @DO_16to23: free
#---- R119 W019 @DO_24to31: free

#---- R120 W020 @Local_Lock

#AttrPLC(HeartBeat,Lock_ST,rLockingAddr,rLockingBit,wLockingAddr,wLockingBit)
AttrPLC(99, 95,120,0,20,0)
