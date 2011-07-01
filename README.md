
LasaurApp is the cannonical app to control a Lasersaur. At the moment it only does two things (1) directly controls the Lasersaur through a interactive GUI widget and (2) submits G-code snippets and files to the Lasersaur.

This app is written mostly in cross-platform, cross-browser Javascript. Only a lightweight backend is used to relay to/from the USB port.

How to Use this App
-------------------

* edit app.py and define the port of the Lasersaur (*ARDUINO_PORT*)
* run *python app.py*
* open *http://localhost:8080*
