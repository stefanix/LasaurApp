
Lasersaur Firmware - Open Source Laser cutter
=============================================

This is the firmware of the [Lasersaur](http://www.lasersaur.com). It originated from Grbl and has become a laser-cutter specific firmware with source simplicity as a central goal. Typically it runs on the Atmega of the Lasersaur's Driveboard but it is also compatible with any Arduino Uno.

For more information see the [Lasersaur Manual](http://www.lasersaur.com/manual/lasaurapp).

**DISCLAIMER:** Please be aware that operating a DIY laser cutter can be dangerous and requires full awareness of the risks involved. You build the machine and you will have to make sure it is safe. The instructions of the Lasersaur project and related software come without any warranty or guarantees whatsoever. All information is provided as-is and without claims to mechanical or electrical fitness, safety, or usefulness. You are fully responsible for doing your own evaluations and making sure your system does not burn, blind, or electrocute people.



General Control Flow
====================

The main processing loop is the **protocol_loop()**. It is launched from main.c after all the initialization. 


protocol_loop()
---------------
The main task is to read one character from the serial buffer and process it. Once it makes sense of the input it assembles commands and delegates them to the **planner** (e.g. planner_line).


The protocol loop can get interrupted by four interrupt handlers: 

- stepper interrupt
- stepper reset interrupt
- serial rx interrupt
- serial tx interrupt.

It can also blocked by five conditions:

- serial rx buffer empty
- serial tx buffer full
- raster transmission in progress
- block buffer full
- synchonizing, waiting for all blocks to be processed

While being blocked (and every time a character is received) the **protocol_idle()** function is called. This means the protocol loop can always write a status report. The only exception is during a full serial tx buffer. In this case it prevents a recursive regression by simply waiting for the buffer to open up first.


planner
-------
The planner takes commands, optimizes them, and puts them in the **block_buffer**. From there they get consumed by the stepper interrupt.


stepper interrupt
-----------------
The stepper interrupt is a timed interrupt that gets activated as soon as items are placed into the **block_buffer**. It processes and pulses the output hardware (stepper motors, I/O) accordingly, block by block. This interrupt controls its own invocation interval according to the timing it needs to properly control the motors.

The periodic interrupt calls stop when all the blocks in the buffer have been consumed. It also stops when a stop condition occures. Stop conditions are exclusively invoked by **stepper_request_stop(...)** so the interrupt can terminate itself. On the next invocation the interrupt will then purge the block buffer and disable the interrupt. The stop flag stays set until the stepper_stop_resume() is called (by serial command). 

Stop requests are invoked by:

- stepper interrupt
- serial rx interrupt
- protocol loop

The first effect of a stop is the periodic stepper interrupt deactivates itself. Any other effects are handled by the protocol loop. Specifically it needs to:

- ignore incoming serial data
- reset serial buffer
- reset block buffer
- update planner pos from current stepper pos
