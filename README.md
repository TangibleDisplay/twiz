## PloogControl

### About

An user friendly interface to control any osc or midi enabled interface
with your PloogIn device.

### Installation

#### Requirements

- Kivy
- bluez
- rtmidi2
- assimp

#### Example on ubuntu:

##### Kivy:

    sudo add-apt-repository ppa:kivy-team/kivy-daily    # nightly build
    sudo apt-get update
    sudo apt-get install python-kivy

##### bluez:

    sudo apt-get install bluez

##### rtmidi2:

    sudo apt-get install python-pip
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


Bluez might need sudo, the following allows keeping the user environment:

    sudo -E sh -c 'python main.py'

If the 3d cube blinks, using optirun might fix the problem on certain graphic cards:

    optirun python main.py      # more here: wiki.ubuntu.com/Bumblebee

