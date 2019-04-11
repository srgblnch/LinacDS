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

Apart there is also a *DataBlock* class for the objecte that will take care of the communiction with the assigned plc.

