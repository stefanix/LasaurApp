
LasaurApp
=========

LasaurApp is the standard app to control a Lasersaur. At the moment it only does two things (1) directly controls the Lasersaur through an interactive GUI widget and (2) submits G-code snippets and files to the Lasersaur.

This app is written mostly in cross-platform, cross-browser Javascript. Only a lightweight backend is used to relay to/from the USB port.

**DISCLAIMER:** Please be aware that operating a diy laser cutter can be dangerous and requires full awareness of the risks involved. You build the machine and you will have to make sure it is safe. The instructions of the Lasersaur project and related software come without any warranty or guarantees whatsoever. All information is provided as-is and without claims to mechanical or electrical fitness, safety, or usefulness. You are fully responsible for doing your own evaluations and making sure your system does not burn, blind, or electrocute people.


How to Use this App
-------------------

* install [pysersial](http://pyserial.sourceforge.net/)
* edit app.py and define the port of the Lasersaur (*ARDUINO_PORT*)
* run *python app.py*
* open *http://localhost:4444* 
  (in a browser with basic html5 support)
