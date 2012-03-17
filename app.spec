# -*- mode: python -*-
a = Analysis(['app.py'],
             pathex=['/Users/noema/Development/git/LasaurApp'],
             hiddenimports=[],
             hookspath=None)
pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          name=os.path.join('dist', 'app'),
          debug=False,
          strip=None,
          upx=True,
          console=True )

a.datas += [
	('css/', '/Users/noema/Development/git/LasaurApp/css', 'DATA'),
	('img/', '/Users/noema/Development/git/LasaurApp/img', 'DATA'),
	('js/', '/Users/noema/Development/git/LasaurApp/js', 'DATA'),
	('app.html', '/Users/noema/Development/git/LasaurApp/app.html', 'DATA')
]     