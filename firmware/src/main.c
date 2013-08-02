/*
  main.c - An embedded CNC Controller with rs274/ngc (g-code) support
  Part of LasaurGrbl

  Copyright (c) 2009-2011 Simen Svale Skogsrud

  LasaurGrbl is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  LasaurGrbl is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
*/

#include <avr/io.h>
#include <avr/sleep.h>
#include <avr/interrupt.h>
#include <util/delay.h>
#include "config.h"
#include "planner.h"
#include "stepper.h"
#include "sense_control.h"
#include "gcode.h"
#include "serial.h"


int main() {
  sei();  //enable interrupts
  serial_init();
  gcode_init();
  planner_init();      
  stepper_init();
  sense_init();
  control_init();
  
  while(true) {
    gcode_process_line();
  }
}
