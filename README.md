
LasaurApp
=========

LasaurApp is the official app to control [Lasersaur](http://lasersaur.com) laser cutters. At the moment it has the following features:

- send G-code to the lasersaur
- convert SVG files to G-code (and optimize)
- GUI widget to move the laser head
- handy G-code programs for the optics calibration process

This app is written mostly in cross-platform, cross-browser Javascript. The idea is to use only a lightweight backend for relaying to and from the USB port. Eventually this backend can either move to the controller on the Lasersaur or to a small dedicated computer. 

This is done this way because we imagine laser cutters being shared in shops. We see people  controlling laser cutters from their laptops and not wanting to go through annoying setup processes. Besides this, html-based GUIs are just awesome :)

**DISCLAIMER:** Please be aware that operating a self-built laser cutter can be dangerous and requires full awareness of the risks involved. NORTD Labs does not warrant for any contents of the manual and does not assume any risks whatsoever with regard to the contents of this manual or the machine assembled by you. NORTD Labs further does not warrant for and does not assume any risks whatsoever with regard to any parts of the machine contained in this manual which are provided by third parties. You need to have the necessary experience in handling high-voltage electrical devices and class 4 laser beams to build the machine described in this manual. Otherwise you should seek professional advice for building the machine. 


How to Use this App
-------------------

* make sure you have Python 2.7
* run *python backend/app.py*
* The GUI will open in a browser at *http://localhost:4444* 
  (supported are Firefox, Chrome, and likely future Safari 6+ or IE 10+)

For more information see the [Lasersaur Software Setup Guide](http://labs.nortd.com/lasersaur/manual/software_setup).



Notes on Creating Standalone Apps
----------------------------------

With [PyInstaller](http://www.pyinstaller.org) it's possible to convert a python app to a standalone, single file executable. This allows us to make the setup process much easier and remove all the the prerequisites on the target machine (including python).

From a shell/Terminal do the following:

* go to LasaurApp/other directory
* run 'python pyinstaller/pyinstaller.py --onefile app.spec'
* the executable will be other/dist/lasaurapp (or dist/lasaurapp.exe on Windows)

Most of the setup for making this happen is in the app.spec file. Here all the accessory data and frontend files are listed for inclusion in the executable. In the actual code the data root directory can be found in 'sys._MEIPASS'.

