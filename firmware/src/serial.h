/*
  serial.c - Low level functions for sending and recieving bytes via the serial port.
  Part of LasaurGrbl

  Copyright (c) 2009-2011 Simen Svale Skogsrud
  Copyright (c) 2011 Sungeun K. Jeon
  Copyright (c) 2011 Stefan Hechenberger

  Inspired by the wiring_serial module by David A. Mellis which
  used to be a part of the Arduino project.
   
  LasaurGrbl is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  LasaurGrbl is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
*/

#ifndef serial_h
#define serial_h

void serial_init();
void serial_write(uint8_t data);
uint8_t serial_read();
uint8_t serial_available();


void printString(const char *s);
void printPgmString(const char *s);
void printInteger(long n);
void printIntegerInBase(unsigned long n, unsigned long base);
void printFloat(double n);

#endif
