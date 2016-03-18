/*
  laser.h - laser control
  Part of LasaurGrbl

  Copyright (c) 2015 Martin Renold

  LasaurGrbl is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  LasaurGrbl is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
*/

#ifndef laser_h
#define laser_h

#include <stdbool.h>
#include "config.h"

void laser_init();

#define LASER_IRQ_CYCLES 510 // CPU clock cycles

void laser_set_pulse_duration(uint8_t new_pulse_duration);
void laser_set_pulse_frequency(uint16_t new_pulse_frequency);
void laser_start_raster(uint8_t * data, uint8_t length);


#endif
