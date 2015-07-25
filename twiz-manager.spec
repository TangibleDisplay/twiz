import os
from os.path import join

IS_LINUX = os.name == 'posix' and os.uname()[0] == 'Linux'
if IS_LINUX:
    from PyInstaller.depend import dylib
    dylib._unix_excludes.update({
        r'.*nvidia.*': 1,
        })

    dylib.exclude_list = dylib.ExcludeList()

from kivy.tools.packaging.pyinstaller_hooks import install_hooks
from os.path import expanduser
install_hooks(globals())

a = Analysis(['main.py'],
             pathex=['.'],
             hiddenimports=['numpy.core.multiarray', 'pyobjus.protocols'],
             excludes=['gobject', 'gio', 'PIL', 'gst', 'gtk', 'gi', 'wx', 'twisted', 'curses'] + (['pygame'] if IS_LINUX else []),
             runtime_hooks=None)

pyz = PYZ(a.pure)

name = 'twiz-manager%s' % ('.exe' if os.name == 'nt' else '')

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name=name,
          debug=False,
          strip=None,
          upx=True,
          console=False,
          icon=join('data', 'Logo vertical.png'))
coll = COLLECT(exe,
               Tree('.',
                    excludes=[
                        '.git', '*.spec', '*.ini', '*.c', 'Makefile',
                        'build', 'dist', '*.pyo', '*.pyc', 'setup.py',
                        'installer', '.gitignore', '*.spw', '*.swo',
                        '*.swn', 'tools',
                        ]),
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=None,
               upx=True,
               name='twiz-manager')
app = BUNDLE(coll,
             name='twiz-manager.app',
             icon='data/Logo vertical.icns')
