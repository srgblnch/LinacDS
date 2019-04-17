# Alba's Linac Control Tango Device Server

This project has been made to provide control access to the linac in the Alba facility.

![Small draw of the physical vision linked with some logical view of the elements](/doc/VerySchematicDrawing.png "Very Schematic Drawing View")

The Linac's control has been developed centering the view in the 5 PLCs that gives control of this instrument. The Linac itself is composed by some smaller instruments and its view not always corresponds with information provided by one single PLC.

The idea is to provide one Device server where each PLC is represented by its Device. A Device class for PLC where each is specialized on the specific PLC to control.

But, above that PLC representation, the logical view of the system should represent the instruments composing this Linac. And this without the limitation of know the PLC that controls this instrument, or which parts of the instruments are controlled by different PLCs.

