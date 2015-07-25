#!/usr/bin/env sh
APP=$1

rm -rf $APP/Contents/Resources/venv/lib/python2.7/site-packages/docutils
rm -rf $APP/Contents/Resources/venv/lib/python2.7/site-packages/pip
rm -rf $APP/Contents/Resources/venv/lib/python2.7/site-packages/pygments/
rm -rf $APP/Contents/Resources/venv/lib/python2.7/site-packages/Cython/
rm -f $(find $APP -name "*.c")
rm -rf $APP/Contents/Resources/kivy/doc/
rm -rf $APP/Contents/Resources/kivy/kivy/tools/
rm -rf $APP/Contents/Resources/kivy/examples/
rm -rf $APP/Contents/Resources/yourapp/examples/
rm -rf $APP/Contents/Resources/yourapp/tools/
rm -rf $APP/Contents/Frameworks/GStreamer.framework/
rm -rf $APP/Contents/Resources/kivy/build/temp.macosx-10.10-intel-2.7
