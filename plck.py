# -*- coding: utf-8 -*-
# plck.py
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

#def jin(*args):
#    return john(args)
#----TODO: This attrbute will 'Rampeable' above some given threashold.
#          That is from 0 to this threashold is set directly, and above to 
#          the maximum must follow some steps and some time on each step.
#          This two ramp parameters must be also dynattrs.
#AttrRampeable('HVPS_V_setpoint',
Attr('HVPS_V_setpoint',
     PyTango.DevFloat,46,0,#RW
     l='High voltage PS voltage setpoint',
     unit='kV',min=0,max=33,format='%4.2f',#switch='HVPS_ONC',
     events={'Threshold':0.01})
Attr('Heat_I',
     PyTango.DevFloat,4,
     l='Heating current monitor',
     unit='A',min=0,max=30,format='%4.1f',
     events={'Threshold':0.01})
Attr('Heat_V',
     PyTango.DevFloat,8,
     l='Heating voltage monitor',
     unit='V',min=0,max=30,format='%4.1f',
     events={'Threshold':0.01})
Attr('HVPS_V',
     PyTango.DevFloat,12,#RO
     l='High voltage PS voltage',
     unit='kV',min=0,max=40,format='%4.2f',
     events={'Threshold':0.001})
Attr('HVPS_I',
     PyTango.DevFloat,16,
     l='High voltage PS current',
     unit='mA',min=0,max=150,format='%4.1f',
     events={'Threshold':0.01})
Attr('Peak_I',
     PyTango.DevFloat,20,
     l='Peak current',
     unit='A',min=0,max=400,format='%4.1f',
     events={'Threshold':0.01})
Attr('Peak_V',
     PyTango.DevFloat,24,
     l='Peak voltage',
     d='peak voltage (calculated',unit='kV',min=0,max=400,format='%4.1f',
     events={'Threshold':0.01})
LV_J = {0:'off',
        1:'vacuum fault',
        2:'oil level fault',
        3:'fan circuit breakers fault',
        4:'23 C water inlet fault',
        5:'focusing magnet underflow',
        6:'focusing magnet overtemp',
        7:'klystron body underflow',
        8:'klystron body overtemp',
        9:'klystron collector underflow',
        10:'klystron collector overtemp',
        11:'cooling down (5 minutes)',
        12:'ready'}
LV_J_QUALITIES={'warning':[0,1,2,3,4,5,6,7,8,9,10],
                'changing':[11]}
Attr('LV_ST',
     PyTango.DevUChar,37,
     l='Low voltage status',
     d='low voltage status'+john(LV_J),
     meanings=LV_J,
     qualities=LV_J_QUALITIES,
     events={})
F_J = {0:'off',
       1:'decreasing',
       2:'low limit fault',
       3:'high limit fault',
       4:'heating',
       5:'ready'}
F_J_QUALITIES={'warning':[0,2,3],
               'changing':[1,4]}
Attr('Heat_ST',
     PyTango.DevUChar,38,
     l='Filament heating status',
     d='filament heating status'+john(F_J),
     meanings=F_J,
     qualities=F_J_QUALITIES,
     events={})
#modify the documented state meaning string to adapt to user meaning.
HV_J = {0:'Waiting for Low Voltage',#'heating...',
        1:'klystron tank covers',
        2:'PFN earth rod',
        3:'PFN doors',
        4:'dumping relay closed',
        5:'over current',
        6:'interlock',
        7:'fault',
        8:'off',
        9:'ready'}
HV_J_QUALITIES={'alarm':[7],
                'warning':[0,1,2,3,4,5,6,8]}
Attr('HVPS_ST',
     PyTango.DevUChar,39,
     l='High voltage PS heating status',
     d='high voltage PS heating status'+john(HV_J),
     meanings=HV_J,
     qualities=HV_J_QUALITIES,
     events={})
PL_J = {0:'off',
        1:'focusing B1 undercurrent',
        2:'focusing B2 undercurrent',
        3:'focusing B3 undercurrent',
        4:'DC reset undercurrent',
        5:'arc overcurrent',
        6:'RF reflected power',
        7:'off',
        8:'ready'}
PL_J_QUALITIES={'warning':[0,1,2,3,4,5,6,7]}
Attr('Pulse_ST',
     PyTango.DevUChar,40,
     l='Pulse status',
     d='pulse status'+john(PL_J),
     meanings=PL_J,
     qualities=PL_J_QUALITIES,
     events={})
Attr('LV_Time',
     PyTango.DevShort,42,
     l='Voltage slow down time',
     d='tempo stop low voltage (5 min)',unit='s',
     events={},
     qualities={'changing':{'abs':{'above':0,'below':300,'under':True}}},
     )
Attr('Heat_Time',
     PyTango.DevShort, 44,
     l='Heating time',
     d='heating tempo (20 min)',unit='m',
     events={},
     #FIXME: even documentation says this is seconds, its clear that it gives 
     # tenths of seconds. A formula is required to convert to minutes
     # (integer rounded)
     formula={'read':'VALUE / 6'},
     qualities={'changing':{'abs':{'above':0,'below':20,'under':True}}},
     )

AttrBit('LV_Interlock_RC',
        62, 0, 16,
        l='Low voltage reset',
        d='low voltage reset\nrising edge reset',
        events={},
        isRst=True)
AttrBit('LV_ONC',
        62, 1, 16,
        l='Low voltage on',
        d='low voltage on\nFalse:off\nTrue:on',
        events={},
        formula={'read':'VALUE and '\
                 'self._internalAttrs[\'lv_ready\'][\'read_value\'] == True'},
        )
AttrBit('HVPS_Interlock_RC',
        62, 2, 16,
        l='High voltage reset',
        d='high voltage reset\nrising edge reset',
        events={},
        isRst=True)
AttrBit('HVPS_ONC',
        62 ,3, 16,
        l='High voltage on',
        d='high voltage on\nFalse:off\nTrue:on',
        events={},
        #rampingAttr='HVPS_V_setpoint',
        formula={'read':'VALUE and '\
                       'self._plcAttrs[\'HVPS_ST\'][\'read_value\'] == 9 and '\
                       'self._plcAttrs[\'Pulse_ST\'][\'read_value\'] == 8',
                 'write':'VALUE and '\
                       'self._plcAttrs[\'HVPS_ST\'][\'read_value\'] == 8 and '\
                       'self._plcAttrs[\'Pulse_ST\'][\'read_value\'] == 7'
                },
        )

#AttrPLC(HeartBeat,Lock_ST,rLockingAddr,rLockingBit,wLockingAddr,wLockingBit)
AttrPLC(36,41,63,0,17,0)

AttrLogic('lv_ready',
          logic={'LV_ST':[0,11,12],
                 'Heat_ST':[0,4,5]},
          d='Klystron LV ready',
          l='Klystron LV ready',
          events={},
          )

AttrLogic('hvps_ready',
          logic={'HVPS_ST':[8,9],
                 'Pulse_ST':[0,7,8]},
          d='High voltage PS ready',
          l='High voltage PS ready',
          events={},
          )
