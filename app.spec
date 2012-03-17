#!/usr/bin/python
# -*- mode: python -*-

import os
from glob import glob
        
frontend_files = \
glob('app.html') + \
glob('css/*.css') + \
glob('css/smoothness/*.css') + \
glob('css/smoothness/images/*.png') + \
glob('img/*') + \
glob('js/*')

frontend_files_packed = []
for frontend_file in frontend_files:
    frontend_files_packed.append( (frontend_file, frontend_file, 'DATA') )
    

a = Analysis(['app.py'],
             pathex=[os.path.abspath(__file__)],
             hiddenimports=[],
             hookspath=None)
 

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas + frontend_files_packed,
          name=os.path.join('dist', 'app'),
          debug=False,
          strip=None,
          upx=True,
          console=True )
   