/*
  protocol.c - Lasersaur protocol parser.
  Part of LasaurApp

  Copyright (c) 2014 Stefan Hechenberger

  LasaurApp is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version. <http://www.gnu.org/licenses/>

  LasaurApp is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
*/


#ifndef protocol_h
#define protocol_h


// Initialize the parser.
void protocol_init();

// Main firmware loop.
// Processes serial rx buffer and queues commands for stepper interrupt.
void protocol_loop();

// Update to stepper position when steppers have been stopped.
// Called from the stepper code that executes the stop.
void protocol_request_position_update();

#endif
