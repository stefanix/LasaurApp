/*
  protocol.h - Lasersaur protocol parser.
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


/* 

The Lasersaur Protocol
======================

The protocol is a ascii/binary hybrid. Markers are printable
ascii values while binary data is transmitted in the extended 
ascii range [128,255].

A transmitted byte can either be a command, a parameter, or a
partial number (data). Four bytes encode a number. Parameters 
need to be set before sending the command that uses them.
Similarly the number needs to be set before sending the parameter
marker. This inverse transmission makes the parser super simple.

For example to send a line command:
<number>x<number>y<number>zB

Numbers are four bytes with values in the extended ascii range [128,255].
They are fixed-point floats with 3 decimals in the range of
[-134217.728, 134217.727]. For details how they are encoded see:
get_curent_value()


Flow Control
------------

The firmware has a serial rx buffer which receives the instructions
byte-by-byte. The client sends a maximum number of bytes that is equvalent
to the buffer size. Whenever the firmware processes bytes from the 
buffer it lets the client know it can send more bytes. Latter notification
does not happen for every byte but for a certain chunk of bytes.


Transmission Error Detection
----------------------------

To diagnose faulty serial connections this firmware uses a simple
error detection scheme. Every byte is transmitted twice and the redundant
byte is compared and discarded right in the serial interrupt handler. 
Computationally this is very efficient. It's also quite suitable since we 
have enough bandwidth. It beats checksums in our case.

*/


#include <string.h>
#include <math.h>
#include "errno.h"
#include <stdint.h>
#include <stdlib.h>
#include <avr/pgmspace.h>
#include "protocol.h"
#include "config.h"
#include "serial.h"
#include "planner.h"
#include "stepper.h"
#include "sense_control.h"



#define REF_RELATIVE 0
#define REF_ABSOLUTE 1

#define OFFSET_TABLE 0
#define OFFSET_CUSTOM 1

#define TABLEOFF_X 0
#define TABLEOFF_Y 1
#define TABLEOFF_Z 2
#define CUSTOMOFF_X 3
#define CUSTOMOFF_Y 4
#define CUSTOMOFF_Z 5

#define PARAM_MAX_DATA_LENGTH 4


typedef struct {
  uint8_t ref_mode;                // {REF_RELATIVE, REF_ABSOLUTE}
  double feedrate;                 // mm/min {F}
  double pulse_frequency;          // laser pulse frequency
  uint8_t pulse_duration;          // laser pulse duration
  uint8_t offselect;               // {OFFSET_TABLE, OFFSET_CUSTOM}
  double target[3];                // X,Y,Z params accumulated
  double offsets[6];               // coord system offsets [table_X,table_Y,table_Z, custom_X,custom_Y,custom_Z]
  uint8_t raster_bytes;            // number of bytes for next raster move
} state_t;
static state_t st;

typedef struct {
  uint8_t chars[PARAM_MAX_DATA_LENGTH];
  uint8_t count;
} data_t;
static data_t pdata;

static volatile bool status_requested;           // when set protocol_idle will write status to serial
static volatile bool superstatus_requested;      // extended status
static volatile uint16_t rx_buffer_underruns;     // when the rx serial buffer runs empty
static volatile bool rx_buffer_underruns_reported;

static void on_cmd(uint8_t command);
static void on_param(uint8_t parameter);
static double get_curent_value();
static uint16_t stack_clearance();


void protocol_init() {
  st.ref_mode = REF_ABSOLUTE;
  st.feedrate = CONFIG_FEEDRATE;
  clear_vector(st.target);
  st.pulse_frequency = 0.0;
  st.pulse_duration = 0.0;
  st.raster_bytes = 0;
  st.offselect = OFFSET_TABLE;
  // table offset, absolute
  st.offsets[X_AXIS] = CONFIG_X_ORIGIN_OFFSET;
  st.offsets[Y_AXIS] = CONFIG_Y_ORIGIN_OFFSET;
  st.offsets[Z_AXIS] = CONFIG_Z_ORIGIN_OFFSET;
  // custom offset, absolute
  st.offsets[3+X_AXIS] = CONFIG_X_ORIGIN_OFFSET;
  st.offsets[3+Y_AXIS] = CONFIG_Y_ORIGIN_OFFSET;
  st.offsets[3+Z_AXIS] = CONFIG_Z_ORIGIN_OFFSET;
  status_requested = true;
  superstatus_requested = true;
  rx_buffer_underruns = 0;
  rx_buffer_underruns_reported = true;
}


void protocol_loop() {
  uint8_t chr;
  while(true) {
    chr = serial_protocol_read();  // blocks until there is data
    if (stepper_stop_requested()) {
      // when stop, ignore serial chars
      // NOTE: A stop can happen any time during the protocol loop
      //       because both stepper and serial rx interrupt my trigger it.
      protocol_idle();
    } else {
      if(chr < 128) {  /////////////////////////////// marker
        if(chr > 64 && chr < 91) {  ///////// command
          // chr is in [A-Z]
          on_cmd(chr);
        } else if(chr > 96 && chr < 123) {  //parameter
          // chr is in [a-z]
          on_param(chr);
        } else {
          stepper_request_stop(STOPERROR_INVALID_MARKER);
        }
        pdata.count = 0;
      } else {  //////////////////////////////////////// data
        // chr is in [128,255]
        if(pdata.count < PARAM_MAX_DATA_LENGTH) {
          pdata.chars[pdata.count++] = chr;
        } else {
          stepper_request_stop(STOPERROR_INVALID_DATA);
        }
      }
      protocol_idle();
    }
  }
}



void on_cmd(uint8_t command) {
  uint8_t cs;
  switch(command) {
    case CMD_NONE:
      break;
    case CMD_LINE:
      planner_line( st.target[X_AXIS], st.target[Y_AXIS], st.target[Z_AXIS], st.feedrate,
                    st.pulse_frequency, st.pulse_duration, st.raster_bytes);
      break;
    case CMD_DWELL:
      //planner_dwell(st.dwell_duration, st.intensity);
      break;
    case CMD_REF_RELATIVE:
      st.ref_mode = REF_RELATIVE;
      break;
    case CMD_REF_ABSOLUTE:
      st.ref_mode = REF_ABSOLUTE;
      break;
    case CMD_HOMING:
      while(stepper_processing()) { 
        // sleep_mode();
        protocol_idle();
      }
      stepper_homing_cycle();
      // now that we are at the physical home
      // zero all the position vectors
      clear_vector(st.target);
      planner_set_position(0.0, 0.0, 0.0);
      // move head to table offset
      st.offselect = OFFSET_TABLE;
      st.target[X_AXIS] = st.offsets[TABLEOFF_X];
      st.target[Y_AXIS] = st.offsets[TABLEOFF_Y];
      st.target[Z_AXIS] = st.offsets[TABLEOFF_Z];         
      planner_line( st.target[X_AXIS], st.target[Y_AXIS], st.target[Z_AXIS], 
                    st.feedrate, 0, 0, 0 );
      break;
    case CMD_SET_OFFSET_TABLE: case CMD_SET_OFFSET_CUSTOM:
      while(stepper_processing()) { 
        // sleep_mode();
        protocol_idle();
      }
      // set offset to current position
      if(command == CMD_SET_OFFSET_CUSTOM) {
        cs = OFFSET_CUSTOM;
      } else {
        cs = OFFSET_TABLE;
      }
      st.offsets[3*cs+X_AXIS] = stepper_get_position_x();
      st.offsets[3*cs+Y_AXIS] = stepper_get_position_y();
      st.offsets[3*cs+Z_AXIS] = stepper_get_position_z();
      break;
    case CMD_SEL_OFFSET_TABLE:
      st.offselect = OFFSET_TABLE;
      break;
    case CMD_SEL_OFFSET_CUSTOM:
      st.offselect = OFFSET_CUSTOM;
      break;
    case CMD_AIR_ENABLE:
      planner_control_air_assist_enable();
      break;
    case CMD_AIR_DISABLE:
      planner_control_air_assist_disable();
      break;
    case CMD_AUX1_ENABLE:
      planner_control_aux1_assist_enable();
      break;
    case CMD_AUX1_DISABLE:
      planner_control_aux1_assist_disable();
      break;
    case CMD_AUX2_ENABLE:
      planner_control_aux2_assist_enable();
      break;
    case CMD_AUX2_DISABLE:
      planner_control_aux2_assist_disable();
      break;   
    default:
      stepper_request_stop(STOPERROR_INVALID_COMMAND);
  }

}



void on_param(uint8_t parameter) {
  double val;
  if(pdata.count == 4) {
    switch(parameter) {
      // def target in absolute coord, val is relative to current offset
      case PARAM_TARGET_X:
        if(st.ref_mode == REF_ABSOLUTE) {
          st.target[X_AXIS] = get_curent_value()+st.offsets[3*st.offselect+X_AXIS];
        } else {
          st.target[X_AXIS] += get_curent_value();
        }
        break;
      case PARAM_TARGET_Y:
        if(st.ref_mode == REF_ABSOLUTE) {
          st.target[Y_AXIS] = get_curent_value()+st.offsets[3*st.offselect+Y_AXIS];
        } else {
          st.target[Y_AXIS] += get_curent_value();
        }
        break;
      case PARAM_TARGET_Z:
        if(st.ref_mode == REF_ABSOLUTE) {
          st.target[Z_AXIS] = get_curent_value()+st.offsets[3*st.offselect+Z_AXIS];
        } else {
          st.target[Z_AXIS] += get_curent_value();
        }
        break;

      case PARAM_FEEDRATE:
        st.feedrate = get_curent_value();
        break;
      case PARAM_PULSE_FREQUENCY:
        st.pulse_frequency = get_curent_value();
        break;
      case PARAM_PULSE_DURATION:
        st.pulse_duration = get_curent_value();
        break;
      case PARAM_RASTER_BYTES:
        st.raster_bytes = get_curent_value();
        break;

      // def table offset, val is absolute
      case PARAM_OFFTABLE_X:
        val = get_curent_value();
        st.offsets[TABLEOFF_X] = val;
        break;
      case PARAM_OFFTABLE_Y:
        val = get_curent_value();
        st.offsets[TABLEOFF_Y] = val;
        break;
      case PARAM_OFFTABLE_Z:
        val = get_curent_value();
        st.offsets[TABLEOFF_Z] = val;
        break;

      // def custom offset, val is relative to table offset
      case PARAM_OFFCUSTOM_X:
        val = get_curent_value();
        st.offsets[CUSTOMOFF_X] = val+st.offsets[TABLEOFF_X];
        break;
      case PARAM_OFFCUSTOM_Y:
        val = get_curent_value();
        st.offsets[CUSTOMOFF_Y] = val+st.offsets[TABLEOFF_Y];
        break;
      case PARAM_OFFCUSTOM_Z:
        val = get_curent_value();
        st.offsets[CUSTOMOFF_Z] = val+st.offsets[TABLEOFF_Z];
        break;

      default:
        stepper_request_stop(STOPERROR_INVALID_PARAMETER);
    }
  } else {
    stepper_request_stop(STOPERROR_INVALID_DATA);
  }
}


void protocol_request_status() {
  status_requested = true;
}

void protocol_request_superstatus() {
  superstatus_requested = true;
}


void protocol_mark_underrun() {
  rx_buffer_underruns += 1;
  rx_buffer_underruns_reported = false;
}


void protocol_idle() {
  // Continuously called in protocol_loop
  // Also called when the protocol loop is blocked by
  // one of the following conditions:
  // - serial reading
  //   - in raster mode
  //   - serial rx buffer empty
  // - serial writing
  //   - serial tx buffer full
  // - planing actions (line, command)
  //   - block buffer full
  // - synchonizing
  //   - while waiting for all blocks to process
  //
  // NOTE: Beware of recursively calling this function.
  //       For example calling it during serial write waits
  //       may cause a recursive regression.


  // if (planner_blocks_available()) {
  //   // DEBUG: turn on
  //   ASSIST_PORT |= (1 << AIR_ASSIST_BIT);
  // } else {
  //   // DEBUG: turn off
  //   ASSIST_PORT &= ~(1 << AIR_ASSIST_BIT);
  // }

  if (stepper_stop_requested()) {
    // TODO: make sure from the time triggered to time handled in protocol loop nothing weird happens
    // WARN: this is contioously call during a stop condition
    // TODO: reset serial rx buffer
    planner_reset_block_buffer();
    planner_set_position(stepper_get_position_x(), stepper_get_position_y(), stepper_get_position_z());      
    pdata.count = 0;
  }

  
  if (status_requested || superstatus_requested) {
    status_requested = false;
    // idle flag
    if (!planner_blocks_available() && !serial_data_available()) {
      serial_write(INFO_IDLE_YES);
      sleep_mode();  // sleep a bit
    }

    if (SENSE_DOOR_OPEN) {
      serial_write(INFO_DOOR_OPEN);
    }
    if (SENSE_CHILLER_OFF) {
      serial_write(INFO_CHILLER_OFF);
    }

    // Handle STOPERROR conditions
    uint8_t stop_code = stepper_stop_status();
    if (stop_code != STOPERROR_OK) {
      // report a stop error
      serial_write(stop_code);
    }

#ifndef DEBUG_IGNORE_SENSORS
    // always report limits
    if (SENSE_X1_LIMIT && stop_code != STOPERROR_LIMIT_HIT_X1) {
      serial_write(STOPERROR_LIMIT_HIT_X1);
    }
    if (SENSE_X2_LIMIT && stop_code != STOPERROR_LIMIT_HIT_X2) {
      serial_write(STOPERROR_LIMIT_HIT_X2);
    }
    if (SENSE_Y1_LIMIT && stop_code != STOPERROR_LIMIT_HIT_Y1) {
      serial_write(STOPERROR_LIMIT_HIT_Y1);
    }
    if (SENSE_Y2_LIMIT && stop_code != STOPERROR_LIMIT_HIT_Y2) {
      serial_write(STOPERROR_LIMIT_HIT_Y2);
    }
    if (SENSE_Z1_LIMIT && stop_code != STOPERROR_LIMIT_HIT_Z1) {
      serial_write(STOPERROR_LIMIT_HIT_Z1);
    }
    if (SENSE_Z2_LIMIT && stop_code != STOPERROR_LIMIT_HIT_Z2) {
      serial_write(STOPERROR_LIMIT_HIT_Z2);
    }
#endif

    // position, an absolute coord, report relative to current offset
    serial_write_param(INFO_POS_X, stepper_get_position_x()-st.offsets[3*st.offselect+X_AXIS]);
    serial_write_param(INFO_POS_Y, stepper_get_position_y()-st.offsets[3*st.offselect+Y_AXIS]);
    serial_write_param(INFO_POS_Z, stepper_get_position_z()-st.offsets[3*st.offselect+Z_AXIS]);

    if (!rx_buffer_underruns_reported) {
      serial_write_param(INFO_BUFFER_UNDERRUN, rx_buffer_underruns);
      rx_buffer_underruns_reported = true;
    }

    serial_write_param(INFO_STACK_CLEARANCE, stack_clearance());
    serial_write_param(INFO_DELAYED_MICROSTEPS, stepper_get_delayed_microsteps());

    if (superstatus_requested) {
      superstatus_requested = false;
      // version
      serial_write_param(INFO_VERSION, VERSION);

      // custom offset, an absolute coord, report relative to table offset
      serial_write_param(INFO_OFFCUSTOM_X, st.offsets[CUSTOMOFF_X]-st.offsets[TABLEOFF_X]);
      serial_write_param(INFO_OFFCUSTOM_Y, st.offsets[CUSTOMOFF_Y]-st.offsets[TABLEOFF_Y]);
      serial_write_param(INFO_OFFCUSTOM_Z, st.offsets[CUSTOMOFF_Z]-st.offsets[TABLEOFF_Z]);      

      serial_write_param(INFO_FEEDRATE, st.feedrate);
      serial_write_param(INFO_PULSE_FREQUENCY, st.pulse_frequency);
      serial_write_param(INFO_PULSE_DURATION, st.pulse_duration);
    }

    serial_write(STATUS_END);
  }
}



double get_curent_value() {
  // returns a number based on the current data chars
  // chars expected to be extended ascii [128,255]
  // 28bit total, three decimals are restored
  // number is in [-134217.728, 134217.727] 
  //
  // The encoding in Python works like this:
  //// num = int(round( (num*1000) + (2**27)))
  //// char0 = (num&127)+128
  //// char1 = ((num&(127<<7))>>7)+128
  //// char2 = ((num&(127<<14))>>14)+128
  //// char3 = ((num&(127<<21))>>21)+128
  return ((((pdata.chars[3]-128L)*2097152L +  // 2097152 = 128*128*128
            (pdata.chars[2]-128L)*16384L +   //   16384 = 128*128
            (pdata.chars[1]-128L)*128L + 
            (pdata.chars[0]-128L))-134217728L ) / 1000.0);  // 134217728 = 2**27
}



// track stack clearance///////////////////////////////////////////////////////
// from discussion on AVR Freaks. web search "AVRGCC Monitoring Stack Usage"
extern uint8_t _end;
extern uint8_t __stack;
void paint_stack() __attribute__ ((naked)) __attribute__ ((section (".init1")));
void paint_stack() {
  // paint stack sram with 0xc5 so we can detect 
  // how much sram gets used by stack spikes.
  // This gets called before main() by the ".init1" line.
  __asm volatile ("    ldi r30,lo8(_end)\n"
                  "    ldi r31,hi8(_end)\n"
                  "    ldi r24,lo8(0xc5)\n" /* STACK_CANARY = 0xc5 */
                  "    ldi r25,hi8(__stack)\n"
                  "    rjmp .cmp\n"
                  ".loop:\n"
                  "    st Z+,r24\n"
                  ".cmp:\n"
                  "    cpi r30,lo8(__stack)\n"
                  "    cpc r31,r25\n"
                  "    brlo .loop\n"
                  "    breq .loop"::);
}

static uint16_t stack_clearance() {
  // Return num of bytes of sram that have never been used
  // by stack. This only makes sense when not using heap.
  const uint8_t *p = &_end;
  uint16_t c = 0;
  while(*p == 0xc5 && p <= &__stack) {
    p++;
    c++;
  }
  return c;
}
///////////////////////////////////////////////////////////////////////////////





// double num_from_chars(uint8_t char0, uint8_t char1, uint8_t char2, uint8_t char3) {
//   // chars expected to be extended ascii [128,255]
//   // 28bit total, three decimals are restored
//   // number is in [-134217.728, 134217.727] 
//   return ((((char3-128)*2097152+(char2-128)*16384+(char1-128)*128+(char0-128))-134217728)/1000.0);
// }

// void chars_from_num(num, uint8_t* char0, uint8_t* char1, uint8_t* char2, uint8_t* char3) {
//   // num to be [-134217.728, 134217.727]
//   // three decimals are retained
//   uint32_t num = lround(num*1000 + 134217728);
//   char0 = (num&127)+128
//   char1 = ((num&(127<<7))>>7)+128
//   char2 = ((num&(127<<14))>>14)+128
//   char3 = ((num&(127<<21))>>21)+128
//   return char3, char2, char1, char0
// }

// IN PYTHON
// def double_from_chars_4(char3, char2, char1, char0):
//     # chars expected to be extended ascii [128,255]
//     return ((((char3-128)*128*128*128 + (char2-128)*128*128 + (char1-128)*128 + (char0-128) )- 2**27)/1000.0)
//
// def chars4_from_double(num):
//     # num to be [-134217.728, 134217.727]
//     # three decimals are retained
//     num = int(round( (num*1000) + (2**27)))
//     char0 = (num&127)+128
//     char1 = ((num&(127<<7))>>7)+128
//     char2 = ((num&(127<<14))>>14)+128
//     char3 = ((num&(127<<21))>>21)+128
//     return char3, char2, char1, char0
//
// def check(val):
//     char3, char2, char1, char0 = chars4_from_double(val)
//     val2 = double_from_chars_4(char3, char2, char1, char0)
//     print "assert %s == %s" % (val, val2)
//     # assert val == val2
//
// check(13925.2443)



// int freeRam () {
//   extern int __heap_start, *__brkval;
//   int v;
//   return (int) &v - (__brkval == 0 ? (int) &__heap_start : (int) __brkval);
// }
