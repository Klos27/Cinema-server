# Cinema-server
Cinema UDP server made in python (connect with Android app).
Switching on/off lights + PWM LED + Display animations on projector

### OrangePi:
Instruction for OrangePi Pc Plus

Sorry, but project droped.
Just install GPIO for OrangePi and pyserial 

### RaspberryPi:
Instruction for Raspberry Pi 2B / 3B / 3B+
sudo apt install python3-rpi.gpio
sudo apt install python3-pip
sudo python3 -m pip install pyserial

default: use 3.3V on switches to steer realys

use script listGPIO.sh to see GPIO changes

test UDP connection using:
echo "PST11 00" > /dev/udp/127.0.0.1/50000
echo "PST10 00" > /dev/udp/127.0.0.1/50000

echo "REL05 1" > /dev/udp/127.0.0.1/50000
echo "REL05 0" > /dev/udp/127.0.0.1/50000
