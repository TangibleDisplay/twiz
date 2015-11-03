project=twiz-manager
ifdef ComSpec
	RM=cmd /C del /F /Q
	RMDIR=cmd /C rd /S /Q
	MV=cmd /C move
	condiment=python -m condiment
        pyinstaller=pyinstaller
	installer="\Program Files (x86)\Inno Setup 5\ISCC.exe" $(project).iss
else
	UNAME_S = $(shell uname -s)
	RM=rm -f
	RMDIR=rm -rf
	MV=mv
	condiment=condiment
        pyinstaller=pyinstaller
	installer=tar -C dist -caf dist/$(project).tar.bz2 $(project)
	make_icon=tools/create_icon.sh
	ifeq ($(UNAME_S), Darwin)
		installer=hdiutil create dist/$(project).dmg -srcfolder dist/$(project).app -ov
		make_icon=tools/create_osx_icon.sh
		pyinstaller=kivy /usr/local/bin/pyinstaller -w
		condiment=/usr/local/bin/condiment
	endif
endif

#all: Prepare Cythonize Package Installer
all: Package Installer

Prepare:
	-$(MV) main.py _main.py
	$(condiment) _main.py > main.py

Cythonize:
	python setup.py build_ext --inplace

Package:
	-$(RMDIR) build
	-$(RMDIR) dist
	$(pyinstaller) $(project).spec -y --debug

Installer:
	$(installer)

Restore:
	git reset --hard

Icon:
	$(make_icon)
