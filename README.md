LinacDS
=======

This project is an implementation to control the [Alba](https://www.cells.es)'s Linac ([Linear accelerator](https://en.wikipedia.org/wiki/Linear_particle_accelerator)) using the [Tango](https://www.tango-controls.org) Distributed Controls System (aka [DCS](https://en.wikipedia.org/wiki/Distributed_control_system)). 

![license GPLv3+](https://img.shields.io/badge/license-GPLv3+-green.svg)
![](https://img.shields.io/badge/python-2.6-orange.svg)

Design
------

The hardware is controled by some [PLCs](https://en.wikipedia.org/wiki/Programmable_logic_controller) and each of them has an agent in the distributed system in charge of it. This agent is a Tango Device Server that provides as Tango attributes the different registers provided as DataBlocks from the read and write operations of the PLCs.

Those attributes from the hardware have their behaviour defined by a [builder](https://en.wikipedia.org/wiki/Builder_pattern) [design pattern](https://en.wikipedia.org/wiki/Design_Patterns), as well as other auxiliar attributes, aka *internals*, that helps to provide the behaviour required by the user.

![Refactoring Design class diagram](/doc/RefactoringDesign_ClassDiagram.png)

All the classes defined inherits from object and there are several Abstract superclasses to encapsulate functionalities:
* AbstractAttrLog: to define all the necessary stuff to have logging of the object
  * _AbstractFeatureLog: to save the differences but show the same interface when it is a Feature.
* AbstractAttrDict: to define a common access to the attribute contents as if it is a dictionary
* AbstractAttrTango: to define tango related behaviour
* LinacAttrBase: to define what all the attributes in this system must have.
* LinacAttr: Separation to avoid cyclic import with features
  * _LinacFeature: to define what all the features of the attributes must have.
  * LinacFeatureAttr: when a feature has also an internal attribute to setup the behaviour.

Then the attributes themselves fits in one of the next categories:

* PLCAttr: Attribute that is directly related with information provided by the plc.
* InternalAttr: Attribute over the information provided by the plc  
  * GroupAttr: Attribute that depends or affect a set of attributes
  * LogicAttr: Attribute that summarises a set of attributes by evaluating them
* MeaningAttr: Those PLCs provides some states by enumerations, this links the number with a human understandable meaning.
* HistoryAttr: Store state changes to know the sequence of events while decaying to fault.
* EnumerationAttr: User information to save information about hardware replacements they may do.
* AutoStopAttr: Expert system to interact with a set of values and take automatic decisions.
  * AutoStopParameter: Attributes that are adjustments of a given expert system.
  
The features implemented for the attributes are:

* Events: Many of the attributes have the feature of emit tango events
  * EventCtr: This is a singleton were all the events accumulates emittions to then know how many has been emitted during each update period.
* QualityInterpreter: All the tango attributes have a quality. There is a complex configuration to have all the cases implemented.
  * _QualitiesDescription: Contains auxiliar information to help the interpreter.
    * _Quality4States, _Quality4Floats: Special descriptions based on certain data types of attributes
  * _QualitiesObject: Superclass for the quality description   
    * _AbsoluteThreshold, _RelativeThreshold: Two current auxiliars to encapsulate types of comparisons when there are changes in the values.  
* Memorised: Feature that a Tango device may have to have persistent information for the device that may provide a start up write.
* InterlockReset: The booleans for reset are not automatically clean by the plcs. Too early clean doesn't work, too long bypasses protections. This feature adjust the time until 
* GroupMember: There a "meta-attributes" shown to the user that internally interacts with an specific set of attributes of the device
* Formula: This feature transforms the value received by the plc, as well as it could translates also the write. 
* CircularBuffer: Initially necessary to store recent past values for the changing quality, but also used to provide memory of recent past.
  * HistoryBuffer: Specialization for the HistoryAttr. 
* TooFarCondition: Also necessary for the qualities to alert the user that certain readback values are too far from the setpoint. 
* ChangeReporter: Many attributes have depencencies between them, there are things to be reevaluated based on other attributes, this feature was made to stablish this relations.

Apart there is also a *DataBlock* class for the objecte that will take care of the communication with the assigned plc.

Useful debug information
------------------------

Once one has the devices up and running, using the python binding for Tango one can dump de content read from the plc:  

```python
devProxy.HexDump()
  0:  00 00 00 00    3f c0 00 00
  4:  be 7d b9 71    00 00 00 00
  8:  bc d2 54 e7    00 00 00 00
 12:  be 50 d8 da    00 00 00 00
 16:  bd bb bb e8    02 01
 20:  3f a1 11 62    
 24:  3e bd 0f 08    
 28:  00 00 00 00    
 32:  00 00 00 00    
 36:  01 0c 05 09    
 40:  08 01 00 0a    
 44:  00 0a 3f c0    
 48:  00 00 00 00    
 52:  00 00 00 00    
 56:  00 00 00 00    
 60:  00 00 02 01 
```

This is an example, using the [simulation of the linac plc](https://github.com/srgblnch/LinacDS-simulator) of what would be received from a plc control of a klystron. This first block is composed by two parts: the reading and the writing block. The second set on the right is only the write block as it is being send to the plc to command write operations.

Also any of those registers can be read as it is any of the supported types:

```python
dev.GetBit([46,3])
 True

dev.GetByte(46)
 63

dev.GetShort(46)
 16320

dev.GetFloat(46)
 1.5
```

To write in the same way, there are also tango commands:

```python
dev.GetShort(46)
 16321
dev.WriteShort([0,16320])
dev.GetShort(46)
 16320
 
dev.GetFloat(46)
 1.5
dev.WriteFloat([0,1.1])
dev.GetFloat(46)
 1.100000023841858
```

There are even more internal access possibilities provided by the "Exec()" command. This is a very *expert* command (that also makes insecure it) that allows even [monkey patching](https://en.wikipedia.org/wiki/Monkey_patch) in run time.

One may like to know which are the plc attributes or the internal ones:

```python
dev.Exec("self._plcAttrs.keys()")
 "['Lock_ST',\n 'Heat_Time',\n 'LV_ST',\n 'HVPS_ONC',\n 'Locking',\n 'Pulse_Status',\n 'HVPS_ST',\n 'HVPS_V',\n 'Heat_Status',\n 'Lock_Status',\n 'HVPS_I',\n 'LV_Time',\n 'Pulse_ST',\n 'LV_ONC',\n 'HVPS_V_setpoint',\n 'LV_Status',\n 'HVPS_Status',\n 'Heat_V',\n 'Peak_I',\n 'LV_Interlock_RC',\n 'Peak_V',\n 'Heat_I',\n 'HeartBeat',\n 'HVPS_Interlock_RC',\n 'Heat_ST']"
dev[5].Exec("self._internalAttrs.keys()")
 "['KA_3GHz_RFampli_u',\n 'KA_DCps_thyratron_u',\n 'KA_HVps_u',\n 'KA_fcoil1_u',\n 'lv_ready',\n 'hvps_ready',\n 'KA_fcoil3_u',\n 'KA_IP_controller',\n 'KA_thyratron_u',\n 'KA_tube_u',\n 'KA_fcoil2_u']"
```

This is a case sensitive access to a python dictionary. If one knows the name and like to access the structure, it can do:

```python
print dev.Exec("self._getAttrStruct('hvps_v')")
HVPS_V (PLCAttr):
        device: LinacData(li/ct/plc5)
        events: Emit when changes bigger than 0.001 'Thu Apr 11 12:57:57 2019' ATTR_VALID
        format: %4.2f
        isRst: False
        label: High voltage PS voltage
        logLevel: warning
        maxValue: 40
        name: HVPS_V
        noneValue: nan
        quality: ATTR_VALID
        read_addr: 12
        read_t: 1554980277.94
        read_t_str: Thu Apr 11 12:57:57 2019
        read_value: 0.309809863567
        rvalue: 0.309809863567
        timestamp: 1554980277.94
        type: ('f', 4)
        
print dev.Exec("self._getAttrStruct('hvps_v_setpoint')")
HVPS_V_setpoint (PLCAttr):
        device: LinacData(li/ct/plc5)
        events: Emit when changes bigger than 0.005 'Thu Apr 11 12:44:25 2019' ATTR_CHANGING
        format: %4.2f
        isRst: False
        label: High voltage PS voltage setpoint
        logLevel: warning
        maxValue: 33
        name: HVPS_V_setpoint
        noneValue: nan
        qualities: {changing: {relative: 0.1}}
        quality: ATTR_VALID
        read_addr: 46
        read_t: 1554980314.81
        read_t_str: Thu Apr 11 12:58:34 2019
        read_value: [ 1.10000002  1.10000002  1.10000002  1.10000002  1.10000002  1.10000002
  1.10000002  1.10000002  1.10000002  1.10000002]
        readbackAttr: HVPS_V
        rvalue: 1.10000002384
        timestamp: 1554980314.81
        type: ('f', 4)
        write_addr: 0
        write_value: 1.10000002384
        wvalue: 1.1

```

Many of the features of this attibute can be modified then. Like it can be the loglevel:

```python
dev[5].Exec("self._getAttrStruct('hvps_v').logLevel = 'debug'")
```

First impression of this command is to see when events of this attribute are being emitted.