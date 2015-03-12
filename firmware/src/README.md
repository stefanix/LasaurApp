
Lasersaur - Open Source Laser cutter
-------------------------------------

This is the firmware we use for the Lasersaur. It's a slightly modified version of grbl. It's what runs on an Arduino Uno and takes g-code files to controls the stepper motors accordingly.

How to get this firmware onto an Arduino Uno? There is a python script that will do the trick. Edit the "flash.py" and follow the instruction in it. You will need a USB cable and the Arduino IDE.

For more information see the [Lasersaur Software Setup Guide](http://www.lasersaur.com/manual/software_setup).

**DISCLAIMER:** Please be aware that operating a DIY laser cutter can be dangerous and requires full awareness of the risks involved. You build the machine and you will have to make sure it is safe. The instructions of the Lasersaur project and related software come without any warranty or guarantees whatsoever. All information is provided as-is and without claims to mechanical or electrical fitness, safety, or usefulness. You are fully responsible for doing your own evaluations and making sure your system does not burn, blind, or electrocute people.


Grbl - An embedded g-code interpreter and motion-controller for the Arduino/AVR328 microcontroller
--------------

For more information [on Grbl](https://github.com/simen/grbl)


TODO
------
- g55 wrong offset
- homing cycle cannot recover out of bounds when limit already triggering

mbed merger notes
------------------
- removed
  - inverse mode
  - plane selection, G17, G18, G19
  - arc support, G2, G3
  - M112, use M2 instead

- laser intensity, 255 or 1.0
- trunc() function in gcode parser
- NEXT_ACTION_STOP, newer code
- direction_bits to be uint8_t
- nominal_laser_intensity to be uint8_t
- rate_delta to be int32
- SystemCoreClock/4 to be F_CPU
- out_bits to be uint8_t
- static volatile int busy; no need
- stepper_init
- stepper_synchronize
- stepper_wake_up
- stepper_go_idle
- bit masking

TODO: dwell, cancel, coordinate systems
      proportional laser intensity
      check for: limits, door, power (vrel), chiller


Coordinate Systems
------------------

- use G10 L20 P1 to make the current position the origin in the G54 coordinate system, P2 for the G55 coord system
- select coord system with G54, G55, G56
- usage scenario:
  - use G10 L20 P1 in homing cycle to set the physical home position, associated with G54
  - use G10 L2 P2 X10 Y10 to set a standard offset from the home, associated with the G55 coords
  - use G10 L20 P3 (or G10 L2 P3 X__ Y1__) to set a temporary origin, associated with G56

stop, pause, resume
--------------------
stop on: power, chiller, limit, \03 control char
stop resume on: \02 control char
pause on: door, resume on door close
