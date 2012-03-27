# -*- mode: python -*-
a = Analysis(['../backend/app.py'],
             pathex=['/Users/noema/Development/git/LasaurApp/other'],
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
               a.datas,
               strip=None,
               upx=True,
               name=os.path.join('dist', 'app'))
app = BUNDLE(coll,
             name=os.path.join('dist', 'app.app'))
