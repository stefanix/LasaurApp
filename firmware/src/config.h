/*
  config.h - compile time configuration
  Part of LasaurGrbl

  Copyright (c) 2009-2011 Simen Svale Skogsrud
  Copyright (c) 2011 Sungeun K. Jeon
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

#ifndef config_h
#define config_h

#include <inttypes.h>
#include <stdbool.h>

// Version number
// (must not contain capital letters)
#define LASAURGRBL_VERSION "14.01c"
// build for new driveboard hardware
//#define DRIVEBOARD
// build for 0.9 deg steppers
// #define NANOTEC_STEPPER_09
#define BAUD_RATE 57600
// #define DEBUG_IGNORE_SENSORS  // set for debugging


#define CONFIG_X_STEPS_PER_MM 80.00000000 //microsteps/mm MUST BE FORMAT (XX.XXXXXXXX)
#ifndef NANOTEC_STEPPER_09
  #define CONFIG_Y_STEPS_PER_MM 80.00000000 //microsteps/mm MUST BE FORMAT (XX.XXXXXXXX)
#else
  #define CONFIG_Y_STEPS_PER_MM 80.0000000 //microsteps/mm MUST BE FORMAT (XX.XXXXXXXX)
#endif
#define CONFIG_Z_STEPS_PER_MM 80.00000000 //microsteps/mm MUST BE FORMAT (XX.XXXXXXXX)
#define CONFIG_PULSE_MICROSECONDS 10
#define CONFIG_FEEDRATE 8000.0 // in millimeters per minute
#define CONFIG_SEEKRATE 8000.0
#define CONFIG_ACCELERATION 9000000.0 // mm/min^2, typically 1000000-8000000, divide by (60*60) to get mm/sec^2
#define CONFIG_JUNCTION_DEVIATION 0.006 // mm
#define CONFIG_X_ORIGIN_OFFSET 1.0  // mm, x-offset of table origin from physical home
#define CONFIG_Y_ORIGIN_OFFSET 1.0  // mm, y-offset of table origin from physical home
#define CONFIG_Z_ORIGIN_OFFSET 0.0   // mm, z-offset of table origin from physical home
#define CONFIG_INVERT_X_AXIS 1  // 0 is regular, 1 inverts the x direction
#ifndef NANOTEC_STEPPER_09
  #define CONFIG_INVERT_Y_AXIS 1  // 0 is regular, 1 inverts the y direction
#else
  #define CONFIG_INVERT_Y_AXIS 0  // 0 is regular, 1 inverts the y direction
#endif
#define CONFIG_INVERT_Z_AXIS 1  // 0 is regular, 1 inverts the y direction

// The laser Enable pin is a PWM controlled Pin. They use Arduino Uno digital pin 6 (PWM) look at the sense_control.c Not sure if I can directly drive my 40 watt chinese laser with this PWM signal since the Laser enable pin on my laser driver is hooked up directly to the Texas Instruments TL494CN PWM chip's DTC pin.  That pin is responsible for controlling maximum duty cycle.  Whether or not I can PWM the pin and achieve the same results is yet to be deduced.

#define SENSE_DDR               DDRD
#define SENSE_PORT              PORTD
#define SENSE_PIN               PIND
#ifndef DRIVEBOARD
  #define POWER_BIT             2 // DriverBoard stuff
#endif
#define CHILLER_BIT             3 // Arduino Uno digital pin 3 (PWM)
#define DOOR_BIT                2 // Arduino Uno digital pin 2

#ifdef DRIVEBOARD
  #define ASSIST_DDR            DDRD
  #define ASSIST_PORT           PORTD
  #define AIR_ASSIST_BIT        4 // DriverBoard stuff
  #define AUX1_ASSIST_BIT       7 // DriverBoard stuff
  #define AUX2_ASSIST_BIT       5 // DriverBoard stuff
#else
  #define LIMITS_OVERWRITE_DDR  DDRD 
  #define LIMITS_OVERWRITE_PORT PORTD
  #define LIMITS_OVERWRITE_BIT  7 // Arduino Uno digital pin 7
#endif
  
#define LIMIT_DDR               DDRC
#define LIMIT_PORT              PORTC
#define LIMIT_PIN               PINC
#define X1_LIMIT_BIT            0 // Arduino Uno analog pin 0
#define X2_LIMIT_BIT            1 // Arduino Uno analog pin 1
#define Y1_LIMIT_BIT            2 // Arduino Uno analog pin 2
#define Y2_LIMIT_BIT            3 // Arduino Uno analog pin 3
#ifdef DRIVEBOARD
  #define Z1_LIMIT_BIT          4 // DriverBoard stuff
  #define Z2_LIMIT_BIT          5 // DriverBoard stuff
#else
  #define ASSIST_DDR            DDRC
  #define ASSIST_PORT           PORTC
  #define AIR_ASSIST_BIT        4 // Arduino Uno analog pin 4
  #define AUX1_ASSIST_BIT       5 // Arduino Uno analog pin 5
#endif

#define STEPPING_DDR            DDRB
#define STEPPING_PORT           PORTB
#define X_STEP_BIT              0 // Arduino Uno digital pin 8
#define Y_STEP_BIT              1 // Arduino Uno digital pin 9 (PWM)
#define Z_STEP_BIT              2 // Arduino Uno digital pin 10 (PWM)
#define X_DIRECTION_BIT         3 // Arduino Uno digital pin 11 (PWM)
#define Y_DIRECTION_BIT         4 // Arduino Uno digital pin 12
#define Z_DIRECTION_BIT         5 // Arduino Uno digital pin 13



#ifdef DRIVEBOARD
  #define SENSE_MASK ((1<<CHILLER_BIT)|(1<<DOOR_BIT))
  #define LIMIT_MASK ((1<<X1_LIMIT_BIT)|(1<<X2_LIMIT_BIT)|(1<<Y1_LIMIT_BIT)|(1<<Y2_LIMIT_BIT)|(1<<Z1_LIMIT_BIT)|(1<<Z2_LIMIT_BIT))
#else
  #define SENSE_MASK ((1<<POWER_BIT)|(1<<CHILLER_BIT)|(1<<DOOR_BIT))
  #define LIMIT_MASK ((1<<X1_LIMIT_BIT)|(1<<X2_LIMIT_BIT)|(1<<Y1_LIMIT_BIT)|(1<<Y2_LIMIT_BIT))
#endif
#define STEPPING_MASK ((1<<X_STEP_BIT)|(1<<Y_STEP_BIT)|(1<<Z_STEP_BIT))
#define DIRECTION_MASK ((1<<X_DIRECTION_BIT)|(1<<Y_DIRECTION_BIT)|(1<<Z_DIRECTION_BIT))

// figure out INVERT_MASK
// careful! direction pins hardcoded here#if DRIVEBOARD
// (1<<X_DIRECTION_BIT) | (1<<Y_DIRECTION_BIT) | (1<<Y_DIRECTION_BIT)
#if CONFIG_INVERT_X_AXIS && CONFIG_INVERT_Y_AXIS && CONFIG_INVERT_Z_AXIS
  #define INVERT_MASK 56U
#elif CONFIG_INVERT_X_AXIS && CONFIG_INVERT_Y_AXIS
  #define INVERT_MASK 24U
#elif CONFIG_INVERT_Y_AXIS && CONFIG_INVERT_Z_AXIS
  #define INVERT_MASK 48U
#elif CONFIG_INVERT_X_AXIS && CONFIG_INVERT_Z_AXIS
  #define INVERT_MASK 40U
#elif CONFIG_INVERT_X_AXIS
  #define INVERT_MASK 8U
#elif CONFIG_INVERT_Y_AXIS
  #define INVERT_MASK 16U
#elif CONFIG_INVERT_Z_AXIS
  #define INVERT_MASK 32U
#else
  #define INVERT_MASK 0U
#endif



// The temporal resolution of the acceleration management subsystem. Higher number give smoother
// acceleration but may impact performance.
// NOTE: Increasing this parameter will help any resolution related issues, especially with machines 
// requiring very high accelerations and/or very fast feedrates. In general, this will reduce the 
// error between how the planner plans the motions and how the stepper program actually performs them.
// However, at some point, the resolution can be high enough, where the errors related to numerical 
// round-off can be great enough to cause problems and/or it's too fast for the Arduino. The correct
// value for this parameter is machine dependent, so it's advised to set this only as high as needed.
// Approximate successful values can range from 30L to 100L or more.
#define ACCELERATION_TICKS_PER_SECOND 300L

// Minimum planner junction speed. Sets the default minimum speed the planner plans for at the end
// of the buffer and all stops. This should not be much greater than zero and should only be changed
// if unwanted behavior is observed on a user's machine when running at very slow speeds.
#define ZERO_SPEED 0.1 // (mm/min)

// Minimum stepper rate. Sets the absolute minimum stepper rate in the stepper program and never runs
// slower than this value, except when sleeping. This parameter overrides the minimum planner speed.
// This is primarily used to guarantee that the end of a movement is always reached and not stop to
// never reach its target. This parameter should always be greater than zero.
#define MINIMUM_STEPS_PER_MINUTE 20000U // (steps/min) - Integer value only
// 1600 @ 32step_per_mm = 50mm/min
  

#define X_AXIS 0
#define Y_AXIS 1
#define Z_AXIS 2


#define clear_vector(a) memset(a, 0, sizeof(a))
#define clear_vector_double(a) memset(a, 0.0, sizeof(a))
#define max(a,b) (((a) > (b)) ? (a) : (b))
#define min(a,b) (((a) < (b)) ? (a) : (b))


#endif



// bit math
// see: http://www.arduino.cc/playground/Code/BitMath
// see: http://graphics.stanford.edu/~seander/bithacks.html
//
// y = (x >> n) & 1; // n=0..15. stores nth bit of x in y. y becomes 0 or 1.
//
// x &= ~(1 << n); // forces nth bit of x to be 0. all other bits left alone.
//
// x &= (1<<(n+1))-1; // leaves alone the lowest n bits of x; all higher bits set to 0.
//
// x |= (1 << n); // forces nth bit of x to be 1. all other bits left alone.
//
// x ^= (1 << n); // toggles nth bit of x. all other bits left alone.
//
// x = ~x; // toggles ALL the bits in x.

