
TODO
-----
- F unit?
- 1,2,3 keys for selecting tabs
- simi bug
- shape order optimization
- automatic recognition for svg72/svg90
- better contrast for selected colors
- default colors R,G,B to Pass 1,2,3
- connection button status
- error reporting in ui
- offset feature, G0F10000 causes wild pos after setting offset
- cancel button fail on long lines
- door open pause, still causes problems

BUG
---
- invisible super slow black lines

YAG
----
- some files cause the origin to drift
- homing does not reset stop mode


- sperrholz pappel 8mm


- bed size: 48x24" or 1220x610mm
  also for direct control


Laser Style by color
--------------------

- Recognize all colors in svg and provide laser style panel for each
- add a simple way of combining colors



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



LasaurApp inkscape import workflow
===================================

- in "File/Document Properties" set "Custom size" to 1220x620mm
  (Set "Default units" to whatever you like)
- import or draw something
- set all outlines you want to cut red (stroke color: 255,0,0)
- save as "Plain SVG"
- import in LasaurApp



