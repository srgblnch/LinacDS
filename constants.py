# -*- coding: utf-8 -*-
# constants.py
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

MAJOR_VERSION = 2
MINOR_VERSION = 2
BUILD_VERSION = 7

#---- attributes keys
READADDR = 'read_addr'
READBIT = 'read_bit'
READVALUE = 'read_value'
READTIME = 'read_t'
WRITEADDR = 'write_addr'
WRITEBIT = 'write_bit'
WRITEVALUE = 'write_value'
TYPE = 'type'
FORMULA = 'formula'
LASTEVENTQUALITY = 'lastEventQuality'

#---- internal logic attrs
LOGIC = 'logic'
OPERATOR = 'operator'
INVERTED = 'inverted'

#---- resets
ISRESET = 'isRst'
RESETTIME = 'rst_t'
RESETACTIVE = 'activeRst_t'

#---- qualities and events
QUALITIES = 'qualities'
EVENTS = 'events'
CHANGING = 'changing'
WARNING = 'warning'
ALARM = 'alarm'
ABSOLUTE = 'abs'
RELATIVE = 'rel'
ABOVE = 'above'
BELOW = 'below'
UNDER = 'under'
MEANINGS = 'meanings'

#---- periods
EVENT_THREAD_PERIOD = 0.320#s
ACTIVE_RESET_T = EVENT_THREAD_PERIOD*3#s
PLC_MIN_UPDATE_PERIOD = EVENT_THREAD_PERIOD/2#s
PLC_MAX_UPDATE_PERIOD = EVENT_THREAD_PERIOD*2#s
PLC_STEP_UPDATE_PERIOD = EVENT_THREAD_PERIOD/10#s
EXPECTED_UPDATE_TIME = PLC_MAX_UPDATE_PERIOD#s or less

#---- ramping
RAMP = 'ramp'
RAMPDEST = 'ramp_dest'
STEP = 'step'
STEPTIME = 'steptime'
THRESHOLD = 'threshold'
RAMPENABLE = 'rampEnable'
ASCENDING = 'ascending'
DESCENDING = 'descending'
SWITCH = 'switch'
SWITCHDESCRIPTOR = 'switchDescriptor'
SWITCHDEST = 'switch_dest'
WHENON = 'whenOn'
SWITCHONSLEEP = 1#s
WHENOFF = 'whenOff'
ATTR2RAMP = 'attr2ramp'
FROM = 'from'
TO = 'to'

