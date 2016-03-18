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
#define CMD_STOP '\x01'
#define CMD_RESUME '\x02'
#define CMD_STATUS '\x03'
#define CMD_SUPERSTATUS '\x04'
#define CMD_CHUNK_PROCESSED '\x05'
#define STATUS_END '\x09'


// commands, handled in protocol.c
#define CMD_NONE 'A'
#define CMD_LINE 'B'
#define CMD_DWELL 'C'

#define CMD_REF_RELATIVE 'E' 
#define CMD_REF_ABSOLUTE 'F'

#define CMD_HOMING 'G'

#define CMD_SET_OFFSET_TABLE 'H'
#define CMD_SET_OFFSET_CUSTOM 'I'
#define CMD_SEL_OFFSET_TABLE 'J'
#define CMD_SEL_OFFSET_CUSTOM 'K'

#define CMD_AIR_ENABLE 'L'
#define CMD_AIR_DISABLE 'M'
#define CMD_AUX1_ENABLE 'N'
#define CMD_AUX1_DISABLE 'O'
#define CMD_AUX2_ENABLE 'P'
#define CMD_AUX2_DISABLE 'Q'


#define PARAM_TARGET_X 'x'
#define PARAM_TARGET_Y 'y' 
#define PARAM_TARGET_Z 'z' 
#define PARAM_FEEDRATE 'f'
#define PARAM_PULSE_FREQUENCY 'p'
#define PARAM_PULSE_DURATION 'd'
#define PARAM_RASTER_BYTES 'r'
#define PARAM_OFFTABLE_X 'h'
#define PARAM_OFFTABLE_Y 'i'
#define PARAM_OFFTABLE_Z 'j'
#define PARAM_OFFCUSTOM_X 'k'
#define PARAM_OFFCUSTOM_Y 'l'
#define PARAM_OFFCUSTOM_Z 'm'


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
#define STOPERROR_VALUE_OUT_OF_RANGE '('
#define STOPERROR_TRANSMISSION_ERROR '='
#define STOPERROR_USART_DATA_OVERRUN ','


// status: info markers
#define INFO_IDLE_YES 'A'
#define INFO_DOOR_OPEN 'B'
#define INFO_CHILLER_OFF 'C'

// status:  info params
#define INFO_POS_X 'x'
#define INFO_POS_Y 'y'
#define INFO_POS_Z 'z'
#define INFO_VERSION 'v'
#define INFO_BUFFER_UNDERRUN 'w'
#define INFO_STACK_CLEARANCE 'u'
#define INFO_DELAYED_MICROSTEPS 't'

#define INFO_HELLO '~'

// super status:
#define INFO_OFFCUSTOM_X 'a'
#define INFO_OFFCUSTOM_Y 'b'
#define INFO_OFFCUSTOM_Z 'c'
#define INFO_FEEDRATE 'g'
#define INFO_PULSE_FREQUENCY 'h'
#define INFO_PULSE_DURATION 'i'



// Initialize the parser.
void protocol_init();

// Main firmware loop.
// Processes serial rx buffer and queues commands for stepper interrupt.
void protocol_loop();

// Called to make protocol_idle report 
// (super)status the next time it runs.
void protocol_request_status();
void protocol_request_superstatus();

// called when rx serial buffer empty
void protocol_mark_underrun();

// called whenever protocol loop is waiting
void protocol_idle();


#endif
