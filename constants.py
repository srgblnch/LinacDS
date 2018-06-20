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

version = "3.0.0-alpha"
MAJOR_VERSION, MINOR_VERSION, BUILD_VERSION = [
    int(x.split('-')[0]) for x in "3.0.1-a".split('.')]

# attributes keys ---
READADDR = 'read_addr'
READBIT = 'read_bit'
READVALUE = 'read_value'
READTIME = 'read_t'
READTIMESTR = 'read_t_str'
WRITEADDR = 'write_addr'
WRITEBIT = 'write_bit'
WRITEVALUE = 'write_value'
TYPE = 'type'
FORMULA = 'formula'
LASTEVENTQUALITY = 'lastEventQuality'
ENABLE = 'Enable'
READBACK = 'readbackAttr'
SETPOINT = 'setpointAttr'
SWITCH = 'SwitchAttr'

# internal logic attrs ---
LOGIC = 'logic'
OPERATOR = 'operator'
INVERTED = 'inverted'

# resets ---
ISRESET = 'isRst'
RESETTIME = 'rst_t'
RESETACTIVE = 'activeRst_t'

# qualities and events ---
QUALITIES = 'qualities'
EVENTS = 'events'
CHANGING = 'changing'
WARNING = 'warning'
ALARM = 'alarm'
ABSOLUTE = 'abs'
RELATIVE = 'rel'
ABOVE = 'Above'
BELOW = 'Below'
UNDER = 'Under'
MEANINGS = 'meanings'
EVENTTIME = 'event_t'
EVENTTIMESTR = 'event_t_str'

# periods ---
EVENT_THREAD_PERIOD = 0.320  # s
ACTIVE_RESET_T = EVENT_THREAD_PERIOD*3  # s
PLC_MIN_UPDATE_PERIOD = EVENT_THREAD_PERIOD/2  # s
PLC_MAX_UPDATE_PERIOD = EVENT_THREAD_PERIOD*2  # s
PLC_STEP_UPDATE_PERIOD = EVENT_THREAD_PERIOD/10  # s
RE_EVENTS_PERIOD = EVENT_THREAD_PERIOD * 3 * 10
HISTORY_EVENT_BUFFER = 499

# ramping ---
RAMP = 'Ramp'
RAMPDEST = 'ramp_dest'
STEP = 'Step'
STEPTIME = 'Steptime'
THRESHOLD = 'Threshold'
RAMPENABLE = 'rampEnable'
ASCENDING = 'Ascending'
DESCENDING = 'Descending'
SWITCHDESCRIPTOR = 'switchDescriptor'
SWITCHDEST = 'switch_dest'
WHENON = 'whenOn'
SWITCHONSLEEP = 1  # s
WHENOFF = 'whenOff'
ATTR2RAMP = 'attr2ramp'
FROM = 'from'
TO = 'to'

# Historic buffer ---
BASESET = 'baseSet'
HISTORYLENGTH = 20

# conditional stopper ---
AUTOSTOP = 'AutoStop'
INTEGRATIONTIME = 'IntegrationTime'
MEAN = 'Mean'
STD = 'Std'
TRIGGERED = 'Triggered'

# Readback far from setpoint ---
# from PyTango import AttrQuality
CLOSE_ZERO = 0.1
REL_PERCENTAGE = 0.1
