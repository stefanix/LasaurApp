

BBB
---
- pin P8:46 connected to avr reset would prevent the BBB from booting
- solution: disconnect pin and use P8:44
- to make this backward compatiple switch both pins in software
- also the uart1 mux settings error on the BBB


TODO (raster branch)
---------------------
- gcode import support, and lsa
- job selected path visual clues, bbox
- stats
- configurable width/height, bbox checks
- bigger stop button
- pause
  - break up long lines so pause feature is more snappy
- importing progress bar
- testing
  - offset is punk
  - pause feature
  - busy when jogging
  - mover widget allows too much movement
  - fix fluid design, update bootstrap

TODO
-----
- login/claim, single user restriction, keep login alive signal
- dial in widget
- doc link to reveal library location so people can add more files
- open/save gcode files, show warning and link to supported features
- shortcut keys, e.g 1,2,3 for tabs, arrors for direct control



Inkscape Units
----------------

It appears that inkscape uses px internally.

The scaling factor from a mm dxf to px in inkscape is:
0.2822222222

This is derived from:
25.4/90

25.4 being the mm/in and
90 being the default dpi of inkscape

1220px = 344.31111108mm
620px = 174.97777776mm

http://www.w3.org/TR/SVG/coords.html#Units

for 90 dpi
"1pt" equals "1.25px" (and therefore 1.25 user units)
"1pc" equals "15px" (and therefore 15 user units)
"1mm" would be "3.543307px" (3.543307 user units)
"1cm" equals "35.43307px" (and therefore 35.43307 user units)
"1in" equals "90px" (and therefore 90 user units)


Intaglio Units
--------------
Intaglio sets the width/height attribute to the document dimensions.
3456,1728
=> 72dpi


Illustrator Units
-----------------

Illustrator sets both the width/height and the viewport attributes of the svg tag. Unfortunately it does not set this to the document dimensions but to the bounding box of all the geometry. This makes it completely useless to figure out the dpi scaling factor for pixels to in/mm conversion.

3460.472 x 1736.945




