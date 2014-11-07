# -*- coding: utf-8 -*-
# plc3.py
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

############################

HV = ( 'horizontal', 'vertical')
F = ( 'focussing', )

FOCUS_STATUS = {0:'undefined',
                1:'off',
                2:'bad current',
                3:'underflow',
                4:'overtemp',
                5:'ready'}
FOCUS_QUALITIES={ALARM:[0],
                 WARNING:[1,2,3,4]}
HV_STATUS = {0:'undefined',
             1:'off',
             2:'bad current',
             3:'undefined',
             4:'undefined',
             5:'ready'}
HV_QUALITIES={ALARM:[0,3,4],
              WARNING:[1,2]}

# used by PS
Iread_addr = 0
Iref_addr = 0
Status_addr  = 128

def PS(name, types, rng):
    global Iread_addr
    global Status_addr
    global Iref_addr
    global HV,F
    global FOCUS_STATUS,HV_STATUS
    global FOCUS_QUALITIES,HV_QUALITIES
    for T in types:
        M = T[0].upper()
        desc = name+' current'
        Attr(name+M+'_I',
             PyTango.DevFloat,Iread_addr,
             d=desc+' monitor',unit='A',**rng)
        Attr(name+M+'_I_setpoint',
             PyTango.DevFloat,Iread_addr+161,Iref_addr,
             d=desc+' setpoint',unit='A',**rng)
        Iread_addr += 4
        Iref_addr += 4
        desc_st = '%s %s status'%(name, T)
        if T in HV:
            meanings=HV_STATUS
            qualities=HV_QUALITIES
        elif T in F:
            meanings=FOCUS_STATUS
            qualities=FOCUS_QUALITIES
        else:
            meanings=None
        Attr('%s%s_ST'%(name,M),
             PyTango.DevUChar,Status_addr,
             d=desc_st+john(meanings),
             meanings=meanings,
             qualities=qualities,
             events={})
        Status_addr += 1


PS('SL1',F, {'min':  0.0,'max':  1.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL2',F, {'min':  0.0,'max':  1.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL3',F, {'min':  0.0,'max':  1.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL4',F, {'min':  0.0,'max':  1.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('BC1',F, {'min':  0.0,'max':200.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('BC2',F, {'min':  0.0,'max':200.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('GL', F, {'min':  0.0,'max':130.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('QT1',F, {'min':  0.0,'max':  6.0,'format':'%4.3f',EVENTS:{THRESHOLD:0.0001},QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('QT2',F, {'min':  0.0,'max':  6.0,'format':'%4.3f',EVENTS:{THRESHOLD:0.0001},QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL1',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL2',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL3',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('SL4',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('BC1',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('BC2',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('GL', HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('AS1',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('QT1',HV,{'min':-16.0,'max': 16.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})
PS('AS2',HV,{'min': -2.0,'max':  2.0,'format':'%4.2f',EVENTS:{THRESHOLD:0.001 },QUALITIES:{CHANGING:{RELATIVE:0.1}}})

onc_desc = lambda x: x+' on/off\nFalse:off\nTrue:on'
AttrBit('MA_Interlock_RC',  289, 0, 128, d='magnets interlock reset, rising edge:reset',events={},isRst=True)
AttrBit('SL1_ONC',          289, 1, 128, d=onc_desc('SL1'),events={})
AttrBit('SL2_ONC',          289, 2, 128, d=onc_desc('SL2'),events={})
AttrBit('SL3_ONC',          289, 3, 128, d=onc_desc('SL3'),events={})
AttrBit('SL4_ONC',          289, 4, 128, d=onc_desc('SL4'),events={})
AttrBit('BC1_ONC',          289, 5, 128, d=onc_desc('BC1'),events={})
AttrBit('BC2_ONC',          289, 6, 128, d=onc_desc('BC2'),events={})
AttrBit('GL_ONC',           289, 7, 128, d=onc_desc('GL'),events={})
AttrBit('AS1_ONC',          290, 0, 129, d=onc_desc('AS1'),events={})
AttrBit('QT_ONC',           290, 1, 129, d=onc_desc('QT'),events={})
AttrBit('AS2_ONC',          290, 2, 129, d=onc_desc('AS2'),events={})

GrpBit('all_onc',
       read_addr_bit_pairs=[(289,1),(289,2),(289,3),(289,4),(289,5),(289,6),
                            (289,7),(290,0),(290,1),(290,2)],
       write_addr_bit_pairs=[(128,1),(128,2),(128,3),(128,4),(128,5),(128,6),
                             (128,7),(129,0),(129,1),(129,2)],
       l='all magnet on',
       meanings={0:'close',
                 1:'open'},
       qualities={WARNING:[0]},
       events={},
       )

for magnet in ['SL1','SL2','SL3','SL4','BC1','BC2','GL']:
    AttrLogic('%s_cooling'%(magnet),
              logic={'%sF_ST'%(magnet):[3,4]},
              d='%s cooling loop state'%(magnet),
              l='%s cooling loop state'%(magnet),
              events={},
              inverted=True)

    AttrLogic('%s_current_ok'%(magnet),
              logic={'%sF_ST'%(magnet):[0,1,2],
                     '%sH_ST'%(magnet):[0,1,2],
                     '%sV_ST'%(magnet):[0,1,2]},
              d='%s current state'%(magnet),
              l='%s current state'%(magnet),
              events={},
              operator='or',
              inverted=True)

for magnet in ['AS1','AS2']:
    AttrLogic('%s_cooling'%(magnet),
              logic={'%sH_ST'%(magnet):[3,4],
                     '%sV_ST'%(magnet):[3,4]},
              d='%s cooling loop state'%(magnet),
              l='%s cooling loop state'%(magnet),
              events={},
              inverted=True)

    AttrLogic('%s_current_ok'%(magnet),
              logic={'%sH_ST'%(magnet):[0,1,2],
                     '%sV_ST'%(magnet):[0,1,2]},
              d='%s current state'%(magnet),
              l='%s current state'%(magnet),
              events={},
              operator='or',
              inverted=True)

AttrLogic('QT_cooling',
          logic={'QT1F_ST':[3,4],'QT2F_ST':[3,4]},
          d='QT cooling loop state',
          l='QT cooling loop state',
          events={},
          inverted=True)

AttrLogic('QT_current_ok',
          logic={'QT1F_ST':[0,1,2],
                 'QT2F_ST':[0,1,2],
                 'QT1H_ST':[0,1,2],
                 'QT1V_ST':[0,1,2]},
          d='QT current state',
          l='QT current state',
          events={},
          operator='or',
          inverted=True)

#AttrPLC(HeartBeat,Lock_ST,rLockingAddr,rLockingBit,wLockingAddr,wLockingBit)
AttrPLC(160,159,291,0,130,0)#----FIXME the locking was 291 but documentation say 292
