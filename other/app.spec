#!/usr/bin/python
# -*- mode: python -*-

import os, sys
from glob import glob

resource_files = []
def add_resource_files(file_list):
    global resource_files
    for resfile in file_list:
        resource_files.append( (os.path.relpath(resfile,'../'), resfile, 'DATA') )    

### files to pack into the executable
add_resource_files( glob('../frontend/app.html') )
add_resource_files( glob('../frontend/css/*.css') )
add_resource_files( glob('../frontend/css/smoothness/*.css') )
add_resource_files( glob('../frontend/css/smoothness/images/*.png') )
add_resource_files( glob('../frontend/img/*') )
add_resource_files( glob('../frontend/js/*') )
add_resource_files( glob('../firmware/*.hex') )


### name of the executable
### depending on platform
targetname = 'lasaurapp'
if sys.platform == "darwin":
    targetname = 'lasaurapp'
    add_resource_files( glob('../firmware/tools_osx/*') )
elif sys.platform == "win32":
    targetname = 'lasaurapp.exe'
    add_resource_files( glob('../firmware/tools_win/*') )
elif sys.platform == "linux" or sys.platform == "linux2":
    targetname = 'lasaurapp'
    add_resource_files( glob('../firmware/tools_linux/*') )


### build TOC
a = Analysis(['../backend/app.py'],
             pathex=[os.path.abspath(__file__)],
             hiddenimports=[],
             hookspath=None)
 

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas + resource_files,
          name=os.path.join('dist', targetname),
          debug=False,
          strip=None,
          upx=True,
          console=True )
   