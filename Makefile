all: Package Installer

Package:
	pyinstaller twiz-manager.spec -y

Installer:
	tar -C dist -caf twiz-manager.tar.bz2 twiz-manager
