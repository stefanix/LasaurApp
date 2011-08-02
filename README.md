
LasaurApp
=========

LasaurApp is the official app to control [Lasersaur](http://lasersaur.com) laser cutters. At the moment it has the following features:

- send G-code to the lasersaur
- convert SVG files to G-code
- GUI widget to move the laser head
- handy G-code programs for the optics calibration process

This app is written mostly in cross-platform, cross-browser Javascript. Only a lightweight backend is used to relay to/from the USB port. This is done this way because we imagine laser cutters being shared in shops. We see people  controlling laser cutters from their laptops and not wanting to go through annoying setup steps (e.g: app or driver installation).

**DISCLAIMER:** Please be aware that operating a diy laser cutter can be dangerous and requires full awareness of the risks involved. You build the machine and you will have to make sure it is safe. The instructions of the Lasersaur project and related software come without any warranty or guarantees whatsoever. All information is provided as-is and without claims to mechanical or electrical fitness, safety, or usefulness. You are fully responsible for doing your own evaluations and making sure your system does not burn, blind, or electrocute people.


How to Use this App
-------------------

* install [pysersial](http://pyserial.sourceforge.net/)
* edit app.py and define the port of the Lasersaur (*ARDUINO_PORT*)
* run *python app.py*
* open *http://localhost:4444* 
  (in a browser with basic html5 support)
