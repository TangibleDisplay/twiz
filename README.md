## Twiz

### About

A user friendly interface to control any osc or midi enabled interface
with your Twiz.

### Installation

#### Requirements

- Kivy
- bluez
- rtmidi2
- assimp

#### Example on ubuntu:

##### Kivy:

###### using apt-get:

    sudo add-apt-repository ppa:kivy-team/kivy-daily    # nightly build
    sudo apt-get update
    sudo apt-get install python-kivy

###### using git:

    git clone git://github.com/kivy/kivy.git
    cd kivy
    make
    python setup.py install --user
    # optional: cd .. && rm -rf kivy
    sudo apt-get install python-pygame

##### bluez:

    sudo apt-get install bluez libbluetooth-dev

##### rtmidi2:

    sudo apt-get install python-pip libasound2-dev
    sudo pip install rtmidi2

##### assimp:

    sudo apt-get install cmake
    git clone https://github.com/assimp/assimp
    cd assimp
    cmake -G 'Unix Makefiles'
    make
    sudo cp **/libassimp.so /usr/local/lib
    cd ports/PyAssimp
    python setup.py install --user

### Usage

    python main.py


But the access to the BLE dongle might need sudo:

    sudo python main.py

...and if the 3d cube blinks, using optirun might fix the problem on certain graphic cards:

    sudo optirun python main.py      # more here: wiki.ubuntu.com/Bumblebee

