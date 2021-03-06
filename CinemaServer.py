#!/usr/bin/python
import threading
import socketserver
import socket
import os
import time
import serial  # install pySerial
from pathlib import Path
import RPi.GPIO as GPIO

# using BCM GPIO 00..nn numbers
GPIO.setmode(GPIO.BCM)  #/??

PYTHON_SERVER_PORT = 50000
PYTHON_SERVER_IP = "127.0.0.1"  # Type there server's ip

#TODO check TTY and pySerial
serial_port = serial.Serial("/dev/serial0", baudrate=115200, timeout=1)  # init UART communication with Arduino S3 -> UART #3

os.system('killall -15 omxplayer')
home_dir = str(Path.home())  # get path to user's home directory or type there full path
movie = 0   # movie number
counter = 0  # for tests only
ledSwitch = 0   # LED relay status
ledValue = 128  # LED PWM value

"""
Relays for RaspberryPI
Name         |     Role       |    GPIO
relays[0]:   | ProjectorRelay | GPIO.18
relays[1]:   | Relay 01       | GPIO.23
relays[2]:   | Relay 02       | GPIO.24
relays[3]:   | Relay 03       | GPIO.25
relays[4]:   | Relay 04       | GPIO.08
relays[5]:   | Relay 05       | GPIO.07
relays[6]:   | Relay 06       | GPIO.12
relays[7]:   | Relay 07       | GPIO.16
relays[8]:   | Relay 08       | GPIO.20
relays[9]:   | Relay 09       | GPIO.21

Change relays values using 3.3V on switches

Inputs list (for manual switches):
Name         |     Role       |    GPIO
inputs[0]:   | Free           | 
inputs[1]:   | Switch 01      | GPIO.04
inputs[2]:   | Switch 02      | GPIO.17
inputs[3]:   | Switch 03      | GPIO.27
inputs[4]:   | Switch 04      | GPIO.22
inputs[5]:   | Switch 05      | GPIO.05
inputs[6]:   | Switch 06      | GPIO.06
inputs[7]:   | Switch 07      | GPIO.13
inputs[8]:   | Switch 08      | GPIO.19
inputs[9]:   | Switch 09      | GPIO.26
"""


class Relay:
    def __init__(self, relay_state, relay_port):
        self.state = relay_state
        self.port = relay_port


# Relays list:
relays = [
    Relay(False, 18),
    Relay(False, 23),
    Relay(False, 24),
    Relay(False, 25),
    Relay(False, 8),
    Relay(False, 7),
    Relay(False, 12),
    Relay(False, 16),
    Relay(False, 20),
    Relay(False, 21)]

# setup the relays ports
for i in range(0, 10):
    print("port " + str(i))
    GPIO.setup(relays[i].port, GPIO.OUT)
    GPIO.output(relays[i].port, GPIO.HIGH)

# Inputs (switches) list:
inputs = [
    False,
    4,
    17,
    27,
    22,
    5,
    6,
    13,
    19,
    26
]

# setup the inputs ports
for i in range(1, 10):
    # PULL_DOWN - ster relays using 3.3V on switches
    GPIO.setup(inputs[i], GPIO.IN, pull_up_down=GPIO.PUD_DOWN) # Enable pulldown resistor
    # PULL_UP - ster relays using GND on switches
    # GPIO.setup(inputs[i], GPIO.IN, pull_up_down=GPIO.PUD_UP) # Enable pullup resistor


def switch_relay(rel):
    if rel.state:
        rel.state = False
        GPIO.output(rel.port, GPIO.HIGH)
    else:
        rel.state = True
        GPIO.output(rel.port, GPIO.LOW)


def turn_on_relay(rel):
    rel.state = True
    GPIO.output(rel.port, GPIO.LOW)


def turn_off_relay(rel):
    rel.state = False
    GPIO.output(rel.port, GPIO.HIGH)


def handle_preset(pst_no):
    global relays
    global ledSwitch
    global ledValue
    if pst_no == 1:
        for i in range(1, 4):  # exclude relay0 (projector)
            turn_on_relay(relays[i])
        for i in range(4, 10):
            turn_off_relay(relays[i])
        serial_port.write("REL 0\n".encode())
        ledSwitch = 0
    elif pst_no == 2:
        for i in range(4, 6):  # exclude relay0 (projector)
            turn_on_relay(relays[i])
        for i in range(1, 4):
            turn_off_relay(relays[i])
        for i in range(6, 10):
            turn_off_relay(relays[i])	
        serial_port.write("LED 128\n".encode())
        ledSwitch = 1
        ledValue = 128
    elif pst_no == 3:
        for i in range(6, 8):  # exclude relay0 (projector)
            turn_on_relay(relays[i])
        for i in range(1, 6):
            turn_off_relay(relays[i])
        for i in range(8, 10):
            turn_off_relay(relays[i])
        serial_port.write("REL 0\n".encode())
        ledSwitch = 0
    elif pst_no == 4:
        for i in range(8, 10):  # exclude relay0 (projector)
            turn_on_relay(relays[i])
        for i in range(1, 8):
            turn_off_relay(relays[i])
        serial_port.write("REL 0\n".encode())
        ledSwitch = 0
    elif pst_no == 10:  # turn on everything
        for i in range(1, 10):
            turn_on_relay(relays[i])
        serial_port.write("REL 1\n".encode())
        ledSwitch = 1
    elif pst_no == 11:  # turn off everything
        for i in range(1, 10):  # exclude relay0 (projector)
            turn_off_relay(relays[i])
        serial_port.write("REL 0\n".encode())
        ledSwitch = 0


def movies(num):
    global movie
    global home_dir
    # This function runs in another thread
    my_file = Path(home_dir + '/Videos/' + num + '.mp4')
    if my_file.is_file():
        movie = num
        #TODO this function convert to omxplayer
        os.system(
            'omxplayer --loop -o hdmi --blank --vol -200 --no-osd '
            + home_dir + '/Videos/' + num + '.mp4')
    else:
        print("No such file")
    return


# Put the code you want to do something based on when you get data here.
def on_data(data, sock, client_address):
    global counter
    global home_dir
    global inputs
    global relays
    global serial_port
    global ledSwitch
    global ledValue
    global movie
    msg = data.decode("utf-8")
    # print("client_addr: ", client_address)
    # print(msg)
    # sock.sendto(data, (client_address[0], 50001))     #ECHO SERVER
    try:
        cmd = msg[:msg.rindex(' ')]
        strval = msg[msg.rindex(' ') + 1:]
        val = int(strval)
        if cmd == "MOV":
            if (val <= 10) and (val > 0):  # 9 movies from 1.mp4 to 10.mp4 to show on projector
                my_file = Path(home_dir + '/Videos/' + strval + '.mp4')
                if my_file.is_file():  # start movie only if file exists
                    movie = val
                    if relays[0].state == False:
                        # add some latency there if needed
                        # time.sleep(2)  # 2sec latency
                        turn_on_relay(relays[0]) 
                    os.system('killall -15 omxplayer')
                    t = threading.Thread(target=movies(strval))
                    t.start()
            elif val == 0:
                turn_off_relay(relays[0])
                os.system('killall -15 omxplayer')
                movie = 0
        elif cmd == "LED":
            if (val < 256) and (val > 0):  # LED PWM 0-255 (cmd: "LED 128")
                # sock.sendto(("LED set to -> " + strval).encode(), (client_address[0], 50001))
                msg = "LED " + strval + "\n"
                serial_port.write(msg.encode())
                ledSwitch = 1
                ledValue = val
            elif val == 0:
                # sock.sendto("LED TURNED OFF: value is set to 0".encode(), (client_address[0], 50001))
                serial_port.write("LED 0\n".encode())
                ledSwitch = 0
                ledValue = 0
        elif cmd[:3] == "REL":
            rel_no = int(cmd[3:5])  # cmd like "REL01 1" for relays_no 00-99
            if rel_no == 0: # switch led
                if val == 0:
                    serial_port.write("REL 0\n".encode())
                    ledSwitch = 0
                else:
                    serial_port.write("REL 1\n".encode())
                    ledSwitch = 1
            else:
                if val == 0:
                    turn_off_relay(relays[rel_no])
                elif val == 1:
                    turn_on_relay(relays[rel_no])
                elif val == 2:
                    switch_relay(relays[rel_no])
        elif cmd[:3] == "PST":
            print("run PST")
            preset_no = int(cmd[3:5])  # cmd like "PST05 00" for preset 00-99
            print(preset_no)
            handle_preset(preset_no)
    except ValueError:
        if msg == "STATUS":
            msg_to_sent = "status;"
            msg_to_sent += str(ledSwitch) + ";"
            if ledValue >= 100:
                msg_to_sent += str(ledValue) + ";"
            elif ledValue >= 10:
                msg_to_sent += "0" + str(ledValue) + ";"
            elif ledValue >= 0:
                msg_to_sent += "00" + str(ledValue) + ";"
            else:
                msg_to_sent += "000;"
            for i in range(1, 10):
                if (relays[i].state):
                    msg_to_sent += "1;"
                else:
                    msg_to_sent += "0;"
            msg_to_sent += "movie;"
            msg_to_sent += str(movie)
            # send system state code: Status;rel1;rel2;...;movie;movie_number
            sock.sendto(msg_to_sent.encode(), (client_address[0], 50001))
        # else:
            # print("Oops!  That was no valid number.  Try again...")
            # sock.sendto("WRONG CODE!".encode(), (client_address[0], 50001))


inputsFlags = [False, False, False, False, False, False, False, False, False, False]


def check_switches():
    global inputsFlags
    global inputs
    global relays
    for i in range (1,10):
        if GPIO.input(inputs[i]) == 0:
            inputsFlags[i] = False
        elif inputsFlags[i] == False:
            inputsFlags[i] = True
            switch_relay(relays[i])
        

class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]
        on_data(data, sock, self.client_address)


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass


# START SERVER
try:
    # time.sleep(60) # wait some time for Linux boot - needed while this script is loaded before network service!
    server = ThreadedUDPServer((PYTHON_SERVER_IP, PYTHON_SERVER_PORT), ThreadedUDPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server is running in thread: ", server_thread.name)
    serial_port.write("LED 0\n".encode())
    ledSwtich = 0
    ledValue = 0
    while True:
        # TODO change to button interrupt handler
        check_switches()
        # pass
        # time.sleep(20)
finally:
    print("Shutting down Python server")
    server.shutdown()
    server.server_close()
    GPIO.cleanup()
