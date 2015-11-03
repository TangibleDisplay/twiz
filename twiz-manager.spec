import os
from os.path import join

IS_LINUX = os.name == 'posix' and os.uname()[0] == 'Linux'

if IS_LINUX:
    from PyInstaller.depend import dylib
    dylib._unix_excludes.update({
        r'.*nvidia.*': 1,
        })

    dylib.exclude_list = dylib.ExcludeList()

from kivy.tools.packaging.pyinstaller_hooks import get_hooks

a = Analysis(['main.py'],
             pathex=['.'],
             hiddenimports=['numpy.core.multiarray'],
             excludes=['gobject', 'gio', 'PIL', 'gst', 'gtk', 'gi', 'wx', 'twisted', 'curses'] + (['pygame'] if IS_LINUX else []),
             **get_hooks()
             )

pyz = PYZ(a.pure)

name = 'twiz-manager%s' % ('.exe' if os.name == 'nt' else '')

with open('blacklist.txt') as f:
    excludes = [x.strip() for x in f.readlines()]

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=name,
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon=join('data', 'logo.ico'))
coll = COLLECT(exe,
               Tree('.',
               excludes=excludes),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='twiz-manager')

app = BUNDLE(coll,
             name='twiz-manager.app',)
