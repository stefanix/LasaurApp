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

#include <avr/interrupt.h>
#include <util/atomic.h>
#include <avr/sleep.h>
#include <math.h>
#include "serial.h"
#include "config.h"
#include "stepper.h"
#include "gcode.h"

#define CHAR_STOP '!'
#define CHAR_RESUME '~'

/** ring buffer **********************************
* [_][h][e][l][l][o][_][_][_] -> wrap around     *
*     |              |                           *
*    tail           head                         *
*    (read)        (write)                       *
*                                                *
* buffer empty condition: head == tail           *
* buffer full condition:  (head+1)%size == tail  *
* buffer write: if(!full) {buf[head] = item}     *
* buffer read:  if(!empty) {return buf[tail]}    *
*************************************************/
#define RX_BUFFER_SIZE 255
#define TX_BUFFER_SIZE 128
uint8_t rx_buffer[RX_BUFFER_SIZE];
volatile uint8_t rx_buffer_head = 0;
volatile uint8_t rx_buffer_tail = 0;
volatile uint8_t rx_buffer_open_slots = RX_BUFFER_SIZE - 1;

uint8_t tx_buffer[TX_BUFFER_SIZE];
volatile uint8_t tx_buffer_head = 0;
volatile uint8_t tx_buffer_tail = 0;

/** protocol *************************************
* The sending app initiates any stream by        *
* requesting a ready byte. This serial code then *
* sends one as soon as there are RX_CHUNK_SIZE   *
* slots available in the rx buffer. The sending  *
* app can then send this amount of bytes.        *
* Thereafter it can again request a ready byte   *
* and apon receiving it send the next chunk.     *
*************************************************/
#define CHAR_READY '\x12'
#define CHAR_REQUEST_READY '\x14'
#define RX_CHUNK_SIZE 64
volatile uint8_t send_ready_flag = 0;
volatile uint8_t request_ready_flag = 0;



static void set_baud_rate(long baud) {
  uint16_t UBRR0_value = ((F_CPU / 16 + baud / 2) / baud - 1);
	UBRR0H = UBRR0_value >> 8;
	UBRR0L = UBRR0_value;
}



void serial_init() {
  set_baud_rate(BAUD_RATE);
  
	/* baud doubler off  - Only needed on Uno XXX */
  UCSR0A &= ~(1 << U2X0);
          
	// enable rx and tx
  UCSR0B |= 1<<RXEN0;
  UCSR0B |= 1<<TXEN0;
	
	// enable interrupt on complete reception of a byte
  UCSR0B |= 1<<RXCIE0;
	  
	// defaults to 8-bit, no parity, 1 stop bit
	
  printPgmString(PSTR("# LasaurGrbl " LASAURGRBL_VERSION));
  printPgmString(PSTR("\n"));
}



void serial_write(uint8_t data) {
    // Calculate next head
    uint8_t next_head = tx_buffer_head + 1;
    if (next_head == TX_BUFFER_SIZE) { next_head = 0; }  // wrap around

    // wait, if buffer is full
    while (next_head == tx_buffer_tail) {
      // sleep_mode();
    }

    // Store data and advance head
    tx_buffer[tx_buffer_head] = data;
    tx_buffer_head = next_head;
    
  	UCSR0B |=  (1 << UDRIE0);  // enable tx interrupt  
}

// tx interrupt, called when UDR0 gets empty
SIGNAL(USART_UDRE_vect) {
  uint8_t tail = tx_buffer_tail;  // optimize for volatile
  
  if (send_ready_flag) {    // request another chunk of data
    UDR0 = CHAR_READY;
    send_ready_flag = 0;
  } else {                    // Send a byte from the buffer 
    UDR0 = tx_buffer[tail];
    if (++tail == TX_BUFFER_SIZE) {tail = 0;}  // increment
    tx_buffer_tail = tail;
  }
  
  // disable tx interrupt, if buffer empty
  if (tail == tx_buffer_head) { UCSR0B &= ~(1 << UDRIE0); }  
}



uint8_t serial_read() {
  // wait, if buffer is empty
  while (rx_buffer_tail == rx_buffer_head) {
    // sleep_mode();
  }
  // return return data, advance tail
	uint8_t data = rx_buffer[rx_buffer_tail];
  if (++rx_buffer_tail == RX_BUFFER_SIZE) {rx_buffer_tail = 0;}  // increment
  ATOMIC_BLOCK(ATOMIC_FORCEON) {
    if (rx_buffer_open_slots == RX_CHUNK_SIZE) {  // enough slots opening up
      if (request_ready_flag) {
        send_ready_flag = 1;
        UCSR0B |=  (1 << UDRIE0);  // enable tx interrupt  
        request_ready_flag = 0;
      }
    }    
    rx_buffer_open_slots++;
  }
	return data;
}

// rx interrupt, called whenever a new byte is in UDR0
SIGNAL(USART_RX_vect) {
  uint8_t data = UDR0;
  if (data == CHAR_STOP) {
    // special stop character, bypass buffer
    stepper_request_stop(STATUS_SERIAL_STOP_REQUEST);
  } else if (data == CHAR_RESUME) {
    // special resume character, bypass buffer
    stepper_stop_resume();
  } else if (data == CHAR_REQUEST_READY) {
    if (rx_buffer_open_slots > RX_CHUNK_SIZE) {
      send_ready_flag = 1;
      UCSR0B |=  (1 << UDRIE0);  // enable tx interrupt 
    } else {
      // send ready when enough slots open up
      request_ready_flag = 1;
    }
  } else {
    uint8_t head = rx_buffer_head;  // optimize for volatile    
    uint8_t next_head = head + 1;
    if (next_head == RX_BUFFER_SIZE) {next_head = 0;}

    if (next_head == rx_buffer_tail) {
      // buffer is full, other side sent too much data
      stepper_request_stop(STATUS_RX_BUFFER_OVERFLOW);
    } else {
      rx_buffer[head] = data;
      rx_buffer_head = next_head;
      rx_buffer_open_slots--;
    }
  }
}


uint8_t serial_available() {
  return RX_BUFFER_SIZE - rx_buffer_open_slots;
}



void printString(const char *s) {
  while (*s) {
    serial_write(*s++);
  }
}

// Print a string stored in PGM-memory
void printPgmString(const char *s) {
  char c;
  while ((c = pgm_read_byte_near(s++))) {
    serial_write(c);
  }
}

void printIntegerInBase(unsigned long n, unsigned long base) {
  unsigned char buf[8 * sizeof(long)]; // Assumes 8-bit chars.
  unsigned long i = 0;

  if (n == 0) {
    serial_write('0');
    return;
  }

  while (n > 0) {
    buf[i++] = n % base;
    n /= base;
  }

  for (; i > 0; i--) {
    serial_write(buf[i - 1] < 10 ?
    '0' + buf[i - 1] :
    'A' + buf[i - 1] - 10);
  }
}

void printInteger(long n) {
  if (n < 0) {
    serial_write('-');
    n = -n;
  }

  printIntegerInBase(n, 10);
}

void printFloat(double n) {
  if (n < 0) {
    serial_write('-');
    n = -n;
  }
  n += 0.5/1000; // Add rounding factor
 
  long integer_part;
  integer_part = (int)n;
  printIntegerInBase(integer_part,10);
  
  serial_write('.');
  
  n -= integer_part;
  int decimals = 3;
  uint8_t decimal_part;
  while(decimals-- > 0) {
    n *= 10;
    decimal_part = (int) n;
    serial_write('0'+decimal_part);
    n -= decimal_part;
  }
}

