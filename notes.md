

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


Experimentation with PyQt and PyInstaller
=========================================
- osx
  - using homebrew to install pyqt
  - before running python need to export python path
    - export PYTHONPATH=/usr/local/lib/python2.7/site-packages:$PYTHONPATH
  - running pyinstaller with --onedir -w options creates app bundle
    - python pyinstaller/pyinstaller.py --onedir -w app.py
  - intro to pyqt here:
    - http://zetcode.com/tutorials/pyqt4/



PyQt installation - using QtSDK
================================

## qt
git clone git://gitorious.org/qt/qt.git
./configure -arch x86_64 -confirm-license -opensource -nomake demos -nomake examples
make
make install
-> will be installed in: /usr/local/Trolltech/Qt-4.8.1

## sip
python configure.py -d /Library/Python/2.7/site-packages --arch x86_64
make
make install

## pyqt
python configure.py -q /Users/noema/Development/QtSDK/Desktop/Qt/4.8.0/gcc/bin/qmake -d /Library/Python/2.7/site-packages -g --use-arch x86_6
[export PATH=$PATH:/usr/local/Trolltech/Qt-4.8.0/bin/]
make 
make install






