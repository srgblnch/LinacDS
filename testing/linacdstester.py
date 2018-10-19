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


devNamePattern = "li/ct/plc%d"


class LinacTester(object):
    _dev = None
    _sim = None
    _relocator = None

    def __init__(self):
        super(LinacTester, self).__init__()
        self._dev = {}
        self._sim = {}
        for i in range(1, 6):
            devName = devNamePattern % i
            self._dev[i] = tango.DeviceProxy(devName)
            print("Build proxy to plc%d device" % (i))
            try:
                self._sim[i] = tango.DeviceProxy(devName+"-sim")
                print("Build proxy to plc%d simulator" % (i))
            except:
                pass
        self._relocator = tango.DeviceProxy("li/ct/linacdatarelocator-01")
        nSimulatorDevices = len(self._sim.keys())
        if nSimulatorDevices not in [0, 5]:
            raise EnvironmentError("Not all the simulation proxies "
                                   "were build")
        if nSimulatorDevices in [0]:
            self._sim = None

    def dumpPlcAttrs(self):
        """
        Dump to the current directory a file with the representation of all the
        attributes in the plcs devices.
        :return:
        """
        attrCtr = {}
        currentPath = path.realpath(__file__).rsplit('/',1)[0]
        print currentPath
        with open(currentPath+"/plcs.dump", 'w') as allplcs:
            for i in range(1,6):
                with open(currentPath+"/plc%d.dump" % (i), 'w') as singleplc:
                    attrCtr[i] = [0, 0]
                    allplcs.write(
                        "********** working with PLC{} **********\n".format(i))
                    attrLst = eval(self._dev[i].Exec("self._plcAttrs.keys()"))
                    attrLst.sort()
                    for attrName in attrLst:
                        try:
                            attrStr = "{}\n".format(self._dev[i].Exec(
                                "self._plcAttrs['%s']" % attrName))
                            allplcs.write(attrStr)
                            singleplc.write(attrStr)
                        except Exception as e:
                            eStr = "{}\n".format(e)
                            allplcs.write(eStr)
                            singleplc.write(eStr)
                        try:
                            allplcs.write(
                                "{}\n".format(self._dev[i][attrName]))
                        except Exception as e:
                            allplcs.write("{}\n".format(e))
                        allplcs.write("----------\n")
                        attrCtr[i][0] += 1
                    attrLst = eval(
                        self._dev[i].Exec("self._internalAttrs.keys()"))
                    attrLst.sort()
                    for attrName in attrLst:
                        try:
                            attrStr = "{}\n".format(self._dev[i].Exec(
                                "self._internalAttrs['%s']" % attrName))
                            allplcs.write(attrStr)
                            singleplc.write(attrStr)
                        except Exception as e:
                            eStr = "{}\n".format(e)
                            allplcs.write(eStr)
                            singleplc.write(eStr)
                        try:
                            allplcs.write(
                                "{}\n".format(self._dev[i][attrName]))
                        except Exception as e:
                            allplcs.write("{}\n".format(e))
                        allplcs.write("----------\n")
                        attrCtr[i][1] += 1
        for i in attrCtr:
            print("plc%d\tplcAttrs: %3d\tinternalAttrs: %3d"
                  % (i, attrCtr[i][0], attrCtr[i][1]))


    def attrStruct(self, plc, name, suffix=None):
        """
        Given the plc number and an attribute name print in the strout the
        representation of the internal object.
        Optionally, one can use a suffix that, starting with a dot, access the
        parameters of the object. This is a expert way to read and modify
        internally the objects. Be carefull!
        :param plc:
        :param name:
        :param suffix:
        :return:
        """
        print(self._dev[plc].Exec(
            "self._getAttrStruct('%s')%s"
            % (name, "".join(suffix if suffix is not None else ""))))

    def plcAttrs(self, plc):
        """
        Given the plc number, return a list with the names of attributes
        :param plc
        """
        lst = \
            eval(self._dev[3].Exec("self._plcAttrs.keys()")) + \
            eval(self._dev[3].Exec("self._internalAttrs.keys()"))
        lst.sort()
        return lst


    def simAttr(self, plc, name, suffix=None):
        """
        When there are simulation devices, this works similarly to
        attrStruct(...) but for the simulators.
        It can be used to access the internal structures of the simulation,
        as well as to modify the behaviour of the simulation.
        :param plc
        :param name:
        :param suffix:
        :return:
        """
        if self._sim is not None:
            print(self._sim[plc].Exec(
                "self._plc.attributes['%s']%s"
                % (name, "".join(suffix if suffix is not None else ""))))

    def simAttrs(self, plc):
        """
        Given the plc number, and if there is a simulation device, return a
        list with the names of internal registers
        :param plc:
        :return:
        """
        if self._sim is not None:
            lst = eval(self._sim[plc].Exec("self._plc.attributes.keys()"))
            lst.sort()
            return lst

    def simAttrIsUpdatable(self, plc, name):
        """
        Given a plc number and a register name, report if the attribute is
        uipdatable or not.
        :param plc:
        :param name:
        :return:
        """
        if self._sim is not None:
            k = eval(self._sim[plc].Exec(
                "self._plc.attributes['%s'].keys()" % (name)))
            if 'updatable' in k:
                return eval(self._sim[plc].Exec(
                    "self._plc.attributes['%s']['updatable']" % (name)))
        return None  # if the key is not present

    def simAttrSetUpdatable(self, plc, name, value):
        """
        Given a plc number and a register name turn on or off the updatable
        characteristic if it has it.
        :param plc:
        :param name:
        :param value:
        :return:
        """
        if self.simAttrIsUpdatable(plc, name) is not None:
            if value in [False, True]:
                self._sim[plc].Exec(
                    "self._plc.attributes['%s']['updatable'] = %s"
                    % (name, value))

    def stopUpdatables(self, plc=None):
        """
        If there are simulation devices, stop the updater flags.
        Only to the simulator indicated in the parameter or to all of them if
        the parameter is not used
        :param plc:
        :return:
        """
        if plc is None:
            for i in range(1,6):
                self.stopUpdatables(i)
        else:
            attrNames = self.simAttrs(plc)
            print("stopping updates on %d attributes of plc %d"
                  % (len(attrNames), plc))
            for attrName in attrNames:
                self.simAttrSetUpdatable(plc, attrName, False)

    def startUpdatables(self, plc=None):
        """
        If there are simulation devices, start the updater flags.
        Only to the simulator indicated in the parameter or to all of them if
        the parameter is not used
        :param plc:
        :return:
        """
        if plc is None:
            for i in range(1,6):
                self.startUpdatables(i)
        else:
            attrNames = self.simAttrs(plc)
            print("starting updates on %d attributes of plc %d"
                  % (len(attrNames), plc))
            for attrName in attrNames:
                self.simAttrSetUpdatable(plc, attrName, True)

    def restartAll(self):
        self._relocator.RestartAllInstance()


if __name__ == '__main__':
    LinacTester().dumpPlcAttrs()

