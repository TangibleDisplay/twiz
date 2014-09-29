## PloogControl

### About

An user friendly interface to control any osc or midi enabled interface
with your PloogIn device.

### Installation

#### Requirements

- Kivy 1.9.0
- bluez
- rtmidi2
- assimp

#### Example on ubuntu:

    sudo add-apt-repository ppa:kivy-team/kivy-daily    # nightly build
    sudo apt-get update
    sudo apt-get install python-kivy

    sudo apt-get install bluez

    sudo apt-get install python-pip
    sudo pip install rtmidi2

    sudo apt-get install cmake
    git clone https://github.com/assimp/assimp
    cd assimp
    cmake -G 'Unix Makefiles'
    make
    sudo cp **/libassimp.so /usr/local/lib
    cd ports/PyAssimp
    python setup.py install --user

### Usage

    sudo python main.py # bluez might need sudo

