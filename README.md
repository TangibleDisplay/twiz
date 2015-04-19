## Twiz

### About

A user friendly interface to control any osc or midi enabled interface with
your Twiz.


The Twiz are wireless motion sensors sending data using Bluetooth Low energy.

Their IMU (Inertial Measurement Unit) has 9 degrees of freedom and their sensor
fusion (3D accelerometer + 3D gyroscope + 3D magnetometer) is made on board.

The fusion result is sent as Euler angles, telling how it is tilted compared
to the gravity vector and how it is oriented compared to the north pole.


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

##### bluez:

    sudo apt-get install bluez libbluetooth-dev

##### rtmidi2 (optional, not used currently):

    sudo apt-get install python-pip libasound2-dev
    sudo pip install rtmidi2

##### assimp (optional):

assimp is a library for loading/rendering 3d models, installing it can make the
3d visualisation slightly better, but the visualisation should be fine without
it.

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



### Details

The data received is as follow:

    * 3D accelerometer values
    * 3D Euler angles (fusion of gyroscope and magnetometer)

These values are advertised in the manufacturer data packet as 12 bytes
representing 6 signed integers, each of them being normalized on 16 bits:

    * Order of the data: 0011 2233 4455  AABB CCDD EEFF
                         x    y    z     yaw pitch roll
                         [accel values]  [euler angles]

    * accel values range: [-2.0 g ; +2.0 g[

    * euler angles range: [-180.0 ; +180.0[

Note: the range of a 16 signed bit value is [-2^15 ; 2^15 - 1]


Examples:

1) If we look at the bytes #4 and #5, we get z = 0x4455.
To get the acceleration value, the calculation is:

    z_accel = 0x4455 * 4.0 / 2^16
            = 17493  * 4.0 / 2^16
            = 1.0677 G (Gravity, not grams ;p)

Note: When the sensor is horizontal with the battery below, z should be -1.


2) To get the yaw angle, corresponding to 0xAABB in our example:

    yaw_angle = 0xAABB * 360.0 / 2^16
              = -21829 * 360.0 / 2^16
              = -119.9 degrees

Note: the accuracy of magnetometers is not that great yet, the fusion with the
gyroscope improves it but decimals are not really relevant.


