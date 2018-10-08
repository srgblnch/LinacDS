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

from os import path
try:
    import tango
except:
    import PyTango as tango

__author__ = "Lothar Krause and Sergi Blanch-Torne"
__maintainer__ = "Sergi Blanch-Torne"
__copyright__ = "Copyright 2017, CELLS / ALBA Synchrotron"
__license__ = "GPLv3+"


dev = {}
sim = {}

for i in range(1,6):
    sim[i] = tango.DeviceProxy("li/ct/plc%d-sim"%i)

for i in range(1,6):
    dev[i] = tango.DeviceProxy("li/ct/plc%d"%i)

relocator = tango.DeviceProxy("li/ct/linacdatarelocator-01")


def dumpPlcAttrs():
    attrCtr = {}
    currentPath = path.realpath(__file__).rsplit('/',1)[0]
    print currentPath
    with open(currentPath+"/plcs.dump", 'w') as allplcs:
        for i in range(1,6):
            with open(currentPath+"/plc%d.dump" % (i), 'w') as singleplc:
                attrCtr[i] = [0, 0]
                allplcs.write(
                    "********** working with PLC{} **********\n".format(i))
                attrLst = eval(dev[i].Exec("self._plcAttrs.keys()"))
                attrLst.sort()
                for attrName in attrLst:
                    try:
                        attrStr = "{}\n".format(dev[i].Exec(
                            "self._plcAttrs['%s']" % attrName))
                        allplcs.write(attrStr)
                        singleplc.write(attrStr)
                    except Exception as e:
                        eStr = "{}\n".format(e)
                        allplcs.write(eStr)
                        singleplc.write(eStr)
                    try:
                        allplcs.write("{}\n".format(dev[i][attrName]))
                    except Exception as e:
                        allplcs.write("{}\n".format(e))
                    allplcs.write("----------\n")
                    attrCtr[i][0] += 1
                attrLst = eval(dev[i].Exec("self._internalAttrs.keys()"))
                attrLst.sort()
                for attrName in attrLst:
                    try:
                        attrStr = "{}\n".format(dev[i].Exec(
                            "self._internalAttrs['%s']" % attrName))
                        allplcs.write(attrStr)
                        singleplc.write(attrStr)
                    except Exception as e:
                        eStr = "{}\n".format(e)
                        allplcs.write(eStr)
                        singleplc.write(eStr)
                    try:
                        allplcs.write("{}\n".format(dev[i][attrName]))
                    except Exception as e:
                        allplcs.write("{}\n".format(e))
                    allplcs.write("----------\n")
                    attrCtr[i][1] += 1
    for i in attrCtr:
        print("plc%d\tplcAttrs: %3d\tinternalAttrs: %3d"
              % (i, attrCtr[i][0], attrCtr[i][1]))


def attrStruct(plc, name, suffix=None):
    return dev[plc].Exec("self._getAttrStruct('%s')%s"
                         % (name, "".join(suffix if suffix is not None else "")))

def simAttr(plc, name, suffix=None):
    return sim[plc].Exec("self._plc.attributes['%s']%s"
                         % (name, "".join(suffix
                                          if suffix is not None else "")))

def simAttrs(plc):
    return eval(sim[plc].Exec("self._plc.attributes.keys()"))

def simAttrIsUpdatable(plc, name):
    k = eval(sim[plc].Exec("self._plc.attributes['%s'].keys()" % (name)))
    if 'updatable' in k:
        return eval(sim[plc].Exec("self._plc.attributes['%s']['updatable']"
                                  % (name)))
    return None  # if the key is not present

def simAttrSetUpdatable(plc, name, value):
    if simAttrIsUpdatable(plc, name) is not None and value in [False, True]:
        sim[plc].Exec("self._plc.attributes['%s']['updatable'] = %s"
                      % (name, value))

def stopUpdatables(plc=None):
    if plc is None:
        for i in range(1,6):
            stopUpdatables(i)
    else:
        attrNames = simAttrs(plc)
        print("stopping updates on %d attributes of plc %d"
              % (len(attrNames), plc))
        for attrName in attrNames:
            simAttrSetUpdatable(plc, attrName, False)

def startUpdatables(plc=None):
    if plc is None:
        for i in range(1,6):
            startUpdatables(i)
    else:
        attrNames = simAttrs(plc)
        print("starting updates on %d attributes of plc %d"
              % (len(attrNames), plc))
        for attrName in attrNames:
            simAttrSetUpdatable(plc, attrName, True)

def restartAll():
    relocator.RestartAllInstance()


if __name__ == '__main__':
    dumpPlcAttrs()

