

Raster
======

The elementary building block for doing rasters is the raster line. It's the
same as a normal line but when cruising at constant speed the intensity is
modulated according to a raster buffer.

To get constant speed for the entire raster line an acceleration and
deceleration line needs to come before and after it.

Assume raster line along x-axis.

G0 X<start> Y<start+kerf>
G0 X<start+offset>
G8 X<start+offset+width>
G8 D<raster data>
G8 D<raster data>
G8 D<raster data>
G0 X<start+offset+width+offset>
...



Beam Dynamics Contemplations
============================

### intensity assumptions
intensity 100% = 100 pulses per 32us
intensity 20%  =  20 pulses per 32us
pulses_per_32us * 31250 = pulses_per_seconds
intensity 100% = 3125000 pulses per seconds

!! but pulse length not a good measure, because beginning of the pulse most energy !!


### nominal
nominal_intensity
nominal_steps_per_minute = nominal_feedrate * CONFIG_STEPS_PER_MM

nominal_pulses_per_second = nominal_intensity * 31250
nominal_step_dur_in_seconds = 60/nominal_steps_per_minute
nominal_pulses_per_step = nominal_step_dur_in_seconds / nominal_pulses_per_second

### actual
steps_per_minute
step_dur_in_seconds = 60/steps_per_minute
pulses_per_step = step_dur_in_seconds / pulses_per_second



### Q: what intensity so pulses_per_step == nominal_pulses_per_step?

pulses_per_step == nominal_pulses_per_step
step_dur_in_seconds / pulses_per_second == nominal_step_dur_in_seconds / nominal_pulses_per_second
step_dur_in_seconds / (intensity * 31250) == nominal_step_dur_in_seconds / (nominal_intensity * 31250)
(step_dur_in_seconds/31250) = (intensity*nominal_step_dur_in_seconds) / (nominal_intensity * 31250)

intensity = (step_dur_in_seconds/31250) / ((nominal_step_dur_in_seconds) / (nominal_intensity * 31250))
intensity = (step_dur_in_seconds/31250) * ((nominal_intensity * 31250) / (nominal_step_dur_in_seconds))
intensity = (step_dur_in_seconds * nominal_intensity) / nominal_step_dur_in_seconds
intensity = (60/steps_per_minute * nominal_intensity) / 60/nominal_steps_per_minute
intensity = ((60/steps_per_minute) * nominal_intensity) / (60/(nominal_feedrate*CONFIG_STEPS_PER_MM))
intensity = (nominal_intensity/steps_per_minute) / (1/(nominal_feedrate*CONFIG_STEPS_PER_MM))
intensity = (nominal_intensity/steps_per_minute) * (nominal_feedrate*CONFIG_STEPS_PER_MM)
intensity = (nominal_intensity * nominal_feedrate * CONFIG_STEPS_PER_MM) / steps_per_minute

intensity = (current_block->nominal_laser_intensity * current_block->nominal_speed * CONFIG_STEPS_PER_MM) / steps_per_minute

!! we actually need this based on the actual head speed !!

adjusted_intensity = nominal_intensity * (nominal_speed/actual_speed)