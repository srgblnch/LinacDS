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

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2015, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"

'''Schema of the attributes:
   Attr(name,            :Name of the dynamic attribute
        T,               :Tango type of the attribute
        read_addr,       :PLC register address for read operation
        write_addr=None, :PLC register address for write operation
        historyBuffer={} :Produce an auxiliar attribute with a buffer of values
        **kwargs)

   AttrBit(name,            :Name of the dynamic attribute
           read_addr,       :PLC register address for read operation
           read_bit,        :Bit of the read word representing this boolean
           write_addr=None, :PLC register address for write operation
           write_bit=None,  :Bit to the write in the word for this boolean
           **kwargs)

    AttrRampeable(name,               :Name of the dynamic attribute
                  T,                  :Tango type of the attribute
                  read_addr,          :PLC register address for read operation
                  write_addr=None     :PLC register address for write operation
                  rampDescriptor={}   :Structure to describe ramp behaviour
                  switchDescriptor={} :Power on and off related with the ramp
                  **kwargs)

    AttrLogic(name,           :Name of the dynamic attribute
              logic,          :Dictionary with the attributes as keys and items
                               are a list of values to evaluate as True
              operator='and', :two operations prepared 'and' for all evaluating
                               to True, or 'or' when any evaluates to True
              inverted=False, :Just to invert the result
              **kwargs)

    AttrEnumeration(name,          :Name of the dynamic attribute
                    prefix=None,   :String to start with the attribute name
                    suffixes=None, :String to end with the attribute name
                    **kwargs)

    GrpBit(name,         :Name of the resulting boolean attribute
           attrGroup=[], :List of attributes members of the group
           **kwargs)

   kwargs: l=None,        :label of the attribute
           d=None,        :description of the attribute
           minValue=None, :minimum value allowed
           maxValue=None, :maximum value allowed
           unit=None,     :attribute unit
           format=None    :In the number case (int/float) its precision
           events={}      :dictionary where its existence will set up attr
                           events and its content will configure their
                           behaviour
           qualities={}   :dictionary where the key represents the available
                           qualities and the items the conditions to set them.
                           Important: alarm > warning > changing
           meanings={v:n} :With state enumerations, a status companion comes
                           with the pair of the value and a human
                           understandable text.
           readback       :The RW attribute has another RO to monitor
           setpoint       :The RO attribute has another RW to monitor
           switch         :There is a switch attribute in relation
           autostop={}    :Structure to monitor a value and decide if something
                           has to be stopped based on certain rules
           logLevel=level :Specifically indicate the logging level of the attr.
           formula={}     :Conversion of the read (or write)

    events={}                 :Simply to indicate that the attribute
                               shall emit events
    events={THRESHOLD: value} :Changes below this threshold will not emit
                               events. But the comparison is with the last
                               value emitted to avoid smooth changes mask.

    qualities={WARNING|ALARM|CHANGING:  :Root block to specify which quality
               [values]                 :List of values that requires the
                                         root quality (state-like attrs)
               {ABSOLUTE: {BELOW|ABOVE: :When working with float or decimal
                           float,        values a comparison could be set up
                           UNDER: bool}  as absolute with bounds (use under to 
                                         define if out of or within the bounds), 
                RELATIVE: float          or relative when the attribute stores 
                                         a buffer.
               }}

    rampDescriptor={ASCENDING|DESCENDING: :Ramps can be deferent based on their
                                           direction
                    {STEP=value|          :steps (perhaps except the last)
                     STEPTIME=seconds|    :minimum time between steps
                     THRESHOLD=value|     :Value below or above which (depends
                                           on the direction) the ramp doesn't
                                           apply
                     SWITCH='name'        :Related switch attribute that the
                                           element related with the ramp has
                    }}

    switchDescriptor={ATTR2RAMP='name'        :cross reference to an attribute
                                               that has a ramp configured with
                                               a switch
                      WHENON|WHENOFF:         :When of the switch transition
                                               applies
                      {FROM|TO=value|'name'}  :fix value or attribute reference
                                               to where the transition has to
                                               work with.
                     }}

    logic={'name':                 :
           [values]                :
           {QUALITIES:[qualities]} :
           }

    autostop={BELOW|ABOVE=value
              INTEGRATIONTIME=seconds
              SWITCHDESCRIPTOR='name'
             }
             
    historyBuffer={'BASESET: [values]} :When the new value added is in the
                                        list, clean the buffer and start
                                        accumulating from scratch. This is
                                        useful to trace sequence of states in
                                        a trip, and clean the itlk are reset.

    formula={READ: 'rformula',          :Formula to mask or modify the reading
             WRITE: 'wformula',         :Formula to protect the modify action
             'write_not_allowed': 'msg' :if exist, raise a exception with the
                                         given message.
'''
