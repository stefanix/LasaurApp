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
add_resource_files( glob('../library/*') )

### name of the executable
### depending on platform
target_location = os.path.join('dist', 'lasaurapp')
if sys.platform == "darwin":
    ## to force 32bit use in Terminal "export VERSIONER_PYTHON_PREFER_32_BIT=yes"
    target_location = os.path.join('dist_osx', 'LasaurApp')
    add_resource_files( glob('../firmware/tools_osx/*') )
    resource_files.append( ('.', '../other/dist_osx/python-osx-2.7.1/Python', 'DATA') )  # bugfix: adding python manually
    a = Analysis(['../backend/app.py'],
                 pathex=[os.path.abspath(__file__)],
                 hiddenimports=[],
                 hookspath=None)
    pyz = PYZ(a.pure)
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=1,
              name=os.path.join('build/pyi.darwin/app', 'app'),
              debug=False,
              strip=None,
              upx=True,
              console=False )
    coll = COLLECT(exe,
                   a.binaries,
                   a.zipfiles,
                   a.datas + resource_files,
                   strip=None,
                   upx=True,
                   name=target_location)

    app = BUNDLE(coll,
                 name=target_location + '.app')    
elif sys.platform == "win32":
    target_location = os.path.join('dist_win', 'lasaurapp.exe')
    add_resource_files( glob('../firmware/tools_win/*') )
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
              name=target_location,
              debug=False,
              strip=None,
              upx=True,
              console=False )
# elif sys.platform == "linux" or sys.platform == "linux2":
#     target_location = os.path.join('dist_linux', 'lasaurapp')
#     add_resource_files( glob('../firmware/tools_linux/*') )

