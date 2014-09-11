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


// commands, handled in serial.c
#define CMD_STOP '!'
#define CMD_RESUME '~'
#define CMD_STATUS '?'

#define CMD_RASTER_DATA_START '\x02'
#define CMD_RASTER_DATA_END '\x03'


// commands, handled in protocol.c
#define CMD_NONE 'A'
#define CMD_LINE 'B'
#define CMD_DWELL 'C'
#define CMD_RASTER 'D'

// #define CMD_SET_FEEDRATE 'E'
// #define CMD_SET_INTENSITY 'F'

#define CMD_REF_RELATIVE 'G' 
#define CMD_REF_ABSOLUTE 'H'

#define CMD_HOMING 'I'

#define CMD_SET_OFFSET_TABLE 'J'
#define CMD_SET_OFFSET_CUSTOM 'K'
#define CMD_DEF_OFFSET_TABLE 'L'
#define CMD_DEF_OFFSET_CUSTOM 'M'
#define CMD_SEL_OFFSET_TABLE 'N'
#define CMD_SEL_OFFSET_CUSTOM 'O'

#define CMD_AIR_ENABLE 'P'
#define CMD_AIR_DISABLE 'Q'
#define CMD_AUX1_ENABLE 'R'
#define CMD_AUX1_DISABLE 'S'
#define CMD_AUX2_ENABLE 'T'
#define CMD_AUX2_DISABLE 'U'


#define PARAM_TARGET_X 'x'
#define PARAM_TARGET_Y 'y' 
#define PARAM_TARGET_Z 'z' 
#define PARAM_FEEDRATE 'f'
#define PARAM_INTENSITY 's'
#define PARAM_DURATION 'd'
#define PARAM_PIXEL_WIDTH 'p'


// status: error markers
#define STOPERROR_OK ' '

#define STOPERROR_SERIAL_STOP_REQUEST '!'
#define STOPERROR_RX_BUFFER_OVERFLOW '"'

#define STOPERROR_LIMIT_HIT_X1 '$'
#define STOPERROR_LIMIT_HIT_X2 '%'
#define STOPERROR_LIMIT_HIT_Y1 '&'
#define STOPERROR_LIMIT_HIT_Y2 '*'
#define STOPERROR_LIMIT_HIT_Z1 '+'
#define STOPERROR_LIMIT_HIT_Z2 '-'

#define STOPERROR_INVALID_MARKER '#'
#define STOPERROR_INVALID_DATA ':'
#define STOPERROR_INVALID_COMMAND '<'
#define STOPERROR_INVALID_PARAMETER '>'
#define STOPERROR_TRANSMISSION_ERROR '='


// status: info markers
#define INFO_IDLE_YES 'A'
#define INFO_IDLE_NO 'B'
#define INFO_DOOR_OPEN 'C'
#define INFO_DOOR_CLOSED 'D'
#define INFO_CHILLER_OFF 'E'
#define INFO_CHILLER_ON 'F'
#define INFO_FEC_CORRECTION 'G'

// status:  info params
#define STATUS_POS_X 'x'
#define STATUS_POS_Y 'y'
#define STATUS_POS_Z 'z'
#define STATUS_VERSION 'v'

#define INFO_HELLO '~'

// status: debufgging
#define STATUS_TARGET_X 'a'
#define STATUS_TARGET_Y 'b'
#define STATUS_TARGET_Z 'c'
#define STATUS_FEEDRATE 'f'
#define STATUS_INTENSITY 's'
#define STATUS_DURATION 'd'
#define STATUS_PIXEL_WIDTH 'p'



// Initialize the parser.
void protocol_init();

// Main firmware loop.
// Processes serial rx buffer and queues commands for stepper interrupt.
void protocol_loop();

// Update to stepper position when steppers have been stopped.
// Called from the stepper code that executes the stop.
void protocol_request_position_update();

// Called to make protocol_idle report 
// status the next time it runs.
void protocol_request_status();

// called whenever no new serial data
void protocol_end_of_job_check();

// called whenever protocol loop is waiting
void protocol_idle();


#endif
