import PyTango
from time import sleep

relocator = PyTango.DeviceProxy("li/ct/linacdatarelocator-01")
plc = {}
dev = {}

for i in range(1, 6):
    plc[i] = PyTango.DeviceProxy("li/ct/plc%d-sim" % (i))
    dev[i] = PyTango.DeviceProxy("li/ct/plc%d" % (i))
    plcAttrs = int(dev[i].Exec("len(self._plcAttrs)"))
    plcAttrsEvents = int(dev[i].Exec("len([x for x in self._plcAttrs.keys() "
                                     "if self._plcAttrs[x].events])"))
    internalAttrs = int(dev[i].Exec("len(self._internalAttrs)"))
    internalAttrsEvents = int(dev[i].Exec("len([x for x in "
                                          "self._internalAttrs if "
                                          "self._internalAttrs[x].events])"))
    print("plc%d: %3d (%3d), %3d (%3d) -> %3d (%3d)"
          % (i, plcAttrs, plcAttrsEvents, internalAttrs, internalAttrsEvents,
             plcAttrs+internalAttrs, plcAttrsEvents+internalAttrsEvents))


def readSTDs(n):
    for attr in eval(plc[n].Exec("self._plc.attributes.keys()")):
        if eval(plc[n].Exec("'std' in self._plc.attributes['%s']" % attr)):
            print("%s: %g"
                  % (attr,float(plc[n].Exec("self._plc.attributes['%s']['std']"
                                            % (attr)))))


def multiplySTDs(n,x):
    for attr in eval(plc[n].Exec("self._plc.attributes.keys()")):
        if eval(plc[n].Exec("'std' in self._plc.attributes['%s']" % attr)):
            currentValue = \
                float(plc[n].Exec("self._plc.attributes['%s']['std']" % attr))
            plc[n].Exec("self._plc.attributes['%s']['std'] = %g"
                        % (attr,x*currentValue))


def foreach(value):
    for i in range(1, 6):
        multiplySTDs(i, value) 
        readSTDs(i)


def eventStatistics():
    for i in range(1, 6):
        n = dev[i]['EventsNumber'].value
        t = dev[i]['EventsTime'].value
        print("plc%d: %4.f (%4.f) [%4.f..%4.f] %6.3f (%6.3f) [%6.3f..%6.3f]"
              % (i, n.mean(), n.std(), n.min(), n.max(),
                 t.mean(), t.std(), t.min(), t.max()))


def readAll(n,t):
    attrWithException = []
    for attr in dev[n].get_attribute_list():
        try:
            print("%30s\t=\t%s" % (attr, dev[n][attr].value))
        except PyTango.DevFailed as e:
            print("%30s\t**\t**%s**" % (attr, e[0].desc))
            attrWithException.append(attr)
        except Exception as e:
            print("%30s\t**\t**%s**" % (attr, e))
            attrWithException.append(attr)
        sleep(t)
    if len(attrWithException) == 0:
        print("\nAll attributes readable")
    else:
        print("\nExceptions reading %s" % attrWithException)


def readLocking():
    for i in range(1,6):
        print dev[i].Exec("self._plcAttrs['Locking'].vtq")


def internalObjsDump():
    for i in range(1, 6):
        dev[i].set_timeout_millis(10000)
        attrNames = eval(dev[i].Exec("self._plcAttrs.keys()"))
        attrNames += eval(dev[i].Exec("self._internalAttrs.keys()"))
        attrNames.sort()
        attrReprs = dev[i].Exec("[self._getAttrStruct(attr) "
                               "for attr in %s]" % (attrNames))
        dev[i].set_timeout_millis(3000)
        with open('plc%d.dump' % (i), 'w') as f:
            f.write(attrReprs)
