/*
  sense_control.h - sensing and controlling inputs and outputs
  Part of LasaurGrbl

  Copyright (c) 2011 Stefan Hechenberger

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
#include <util/delay.h>
#include <math.h>
#include <stdlib.h>
#include "sense_control.h"
#include "stepper.h"
#include "planner.h"



void sense_init() {
  //// chiller, door, (power)
  SENSE_DDR &= ~(SENSE_MASK);  // set as input pins 
  // SENSE_PORT |= SENSE_MASK;    //activate pull-up resistors 
  
  //// x1_lmit, x2_limit, y1_limit, y2_limit, z1_limit, z2_limit
  LIMIT_DDR &= ~(LIMIT_MASK);  // set as input pins
  // LIMIT_PORT |= LIMIT_MASK;    //activate pull-up resistors   
}


void control_init() {
  //// air and aux assist control
  ASSIST_DDR |= (1 << AIR_ASSIST_BIT);   // set as output pin
  ASSIST_DDR |= (1 << AUX1_ASSIST_BIT);  // set as output pin
  control_air_assist(false);
  control_aux1_assist(false);
  ASSIST_DDR |= (1 << AUX2_ASSIST_BIT);  // set as output pin
  control_aux2_assist(false);  
}


void control_air_assist(bool enable) {
  if (enable) {
    ASSIST_PORT |= (1 << AIR_ASSIST_BIT);
  } else {
    ASSIST_PORT &= ~(1 << AIR_ASSIST_BIT);
  }
}

void control_aux1_assist(bool enable) {
  if (enable) {
    ASSIST_PORT |= (1 << AUX1_ASSIST_BIT);
  } else {
    ASSIST_PORT &= ~(1 << AUX1_ASSIST_BIT);
  }  
}

void control_aux2_assist(bool enable) {
  if (enable) {
    ASSIST_PORT |= (1 << AUX2_ASSIST_BIT);
  } else {
    ASSIST_PORT &= ~(1 << AUX2_ASSIST_BIT);
  }  
}
