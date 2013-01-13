
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


Notes on Testing on a Virtual Windows System
---------------------------------------------
When running VirtualBox on OSX it has troubles accessing the USB port even when all the VirtualBox settings are correct. This is because OSX captures the device. To make it available in VirtualBox one has to unload it in OSX first. The following works for Arduino Unos:

- sudo kextunload -b com.apple.driver.AppleUSBCDC 

After the VirtualBox session this can be undone with:

- sudo kextload -b com.apple.driver.AppleUSBCDC

For other USB devices thee following may be useful too:
- sudo kextunload -b com.apple.driver.AppleUSBCDCWCM
- sudo kextunload -b com.apple.driver.AppleUSBCDCACMData
- sudo kextunload -b com.apple.driver.AppleUSBCDCACMControl 


BeagleBone/DriveBoard Notes
-----------------------------
The DriveBoard uses UART1 of the BeagleBone. Under Angstrom Linux this gets
mapped to "/dev/ttyO1".

### Python Code

SERIAL_PORT = "/dev/ttyO1"
# echo 0 > /sys/kernel/debug/omap_mux/uart1_txd
fw = file("/sys/kernel/debug/omap_mux/uart1_txd", "w")
fw.write("%X" % (0))
fw.close()
# echo 20 > /sys/kernel/debug/omap_mux/uart1_rxd
fw = file("/sys/kernel/debug/omap_mux/uart1_rxd", "w")
fw.write("%X" % ((1 << 5) | 0))
fw.close()


The BeagleBone also controls the reset pin of the Atmega328 chip. It's
connected to GPIO2_7 which maps to pin 71 (2 * 32 + 7).

### Python code

# echo 71 > /sys/class/gpio/export
fw = file("/sys/class/gpio/export", "w")
fw.write("%d" % (71))
fw.close()

# set the gpio pin to output
# echo out > /sys/class/gpio/gpio71/direction
fw = file("/sys/class/gpio/gpio71/direction", "w")
fw.write("out")
fw.close()

# set the gpio pin high
# echo 1 > /sys/class/gpio/gpio71/value
fw = file("/sys/class/gpio/gpio71/value", "w")
fw.write("1")
fw.flush()

# set the pin low again
# echo 0 > /sys/class/gpio/gpio71/value
# Note: the flush() isn't necessary if you immediately close the file after writing
fw.write("0")
fw.close()


The BeagleBone can also sense which stepper drivers are being used. For
this read pin GPIO2_12 (2*32+12 = 76). Low means Geckos, high means SMC11s.

### Python code

# set the gpio pin to input
fw = file("/sys/class/gpio/gpio76/direction", "w")
fw.write("in")
fw.close()

# get the gpio pin
fw = file("/sys/class/gpio/gpio76/value", "r")
ret = fw.read()
fw.close()