#include <avr/interrupt.h>
#include "config.h"

void laser_init() {
  //// laser control
  // Setup Timer0.
  // Timer0 can pwm either PD5 (OC0B) or PD6 (OC0A), we use PD6
  //
  // PD6 is wired to enable/disable the laser.  The other PSU input
  // which allows to change the output current (via resistor or fast
  // PWM) is not under our control.  The Coletech 100W PSU specifies
  // the response time (to reach nominal current) to be <=1ms, which
  // gives a rough idea about the minimum pulse duration.
  //
  // TCCR0A and TCCR0B are the registers to setup Timer0
  // see chapter "8-bit Timer/Counter0 with PWM" in Atmga328 specs
  // OCR0A sets the duty cycle 0-255 corresponding to 0-100%
  // also see: http://arduino.cc/en/Tutorial/SecretsOfArduinoPWM
  //
  // Timer0 is used to fully enable or disable the laser for a whole
  // timer period, rather than as a PWM. This allows to control
  // precisely the position where a pulse starts in raster mode.

  DDRD |= (1 << DDD6);    // set PD6 as an output
  OCR0A = 0;              // disable
  // Control register setup:
  // - phase-correct PWM (because it allows both always-on and always-off)
  // - OC0A: output (non-inverted)
  // - OC0B: disconnected
  // - prescaler: 1 (options: 1, 8, 64, 256, 1024)
  // - period = prescaler*LASER_IRQ_CYCLES/16Mhz = 31.875us
  TCCR0A = _BV(COM0A1) | _BV(WGM00);
  TCCR0B = _BV(CS00);
  TIMSK0 |= _BV(TOIE0); // Enable Timer0 overflow interrupt
}

static volatile uint16_t pulse_frequency;
static volatile uint16_t pulse_timer;
static volatile uint8_t pulse_duration;

static volatile uint8_t * raster_data_end;
static volatile uint8_t * raster_data_next;

static uint8_t pulse_remaining;
static uint8_t enforce_minimum_period;

// Laser ISR
ISR(TIMER0_OVF_vect) {
  pulse_timer += pulse_frequency;
  if (pulse_timer < pulse_frequency) { // overflow
    if (raster_data_next != raster_data_end) {
      pulse_remaining = *raster_data_next++;
    } else {
      pulse_remaining = pulse_duration;
    }

    // protect against short pulses
    if (pulse_remaining < LASER_MINIMUM_PULSE_DURATION) pulse_remaining = 0;
    // protect against high frequencies
    if (pulse_remaining) {
      if (enforce_minimum_period) {
        pulse_remaining = 0;
        pulse_frequency = 0; // make the problem easier to recognize
      } else {
        enforce_minimum_period = LASER_MINIMUM_PULSE_PERIOD;
      }
    }
  }
  if (enforce_minimum_period) enforce_minimum_period--;

  if (pulse_remaining > 0) {
    OCR0A = 255;
    pulse_remaining--;
  }  else {
    OCR0A = 0;
  }
}

void laser_start_raster(uint8_t * data, uint8_t length)
{
  cli();
  raster_data_next = data;
  raster_data_end = data + length;
  pulse_timer = 0xFFFF; // first pulse starts now
  pulse_duration = 0; // used when running out of data
  sei();
}

void laser_set_pulse_duration(uint8_t new_pulse_duration)
{
  cli();
  pulse_duration = new_pulse_duration;
  // disable raster (if still running)
  raster_data_next = raster_data_end;
  sei();
}

void laser_set_pulse_frequency(uint16_t new_pulse_frequency)
{
  cli();
  pulse_frequency = new_pulse_frequency;
  sei();
}
