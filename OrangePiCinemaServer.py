#!/usr/bin/python
import threading
import socketserver
import socket
import os
import time
import serial  # install pySerial
from pathlib import Path

# Install GPIO lib: https://github.com/duxingkei33/orangepi_PC_gpio_pyH3
from pyA20.gpio import gpio  # OrangePI
from pyA20.gpio import port  # OrangePI
# import RPi.GPIO as GPIO    # RaspberryPI

gpio.init()  # initialize the gpio module

PYTHON_SERVER_PORT = 50000
PYTHON_SERVER_IP = "192.168.200.50"  # Type there server's ip

serial_port = serial.Serial("/dev/ttyS3", baudrate=115200, timeout=1)  # init UART communication with Arduino S3 -> UART #3

os.system('killall -15 mpv')
home_dir = str(Path.home())  # get path to user's home directory or type there full path
movie = 0   # movie number
counter = 0  # for tests only
ledSwitch = 0   # LED relay status
ledValue = 128  # LED PWM value

"""
Relays for OrangePI
Name         |     Role       |    Port
relays[0]:   | ProjectorRelay | port.PD14   
relays[1]:   | Relay 01       | port.PC4 
relays[2]:   | Relay 02       | port.PC7 
relays[3]:   | Relay 03       | port.PA2 
relays[4]:   | Relay 04       | port.PA21  
relays[5]:   | Relay 05       | port.PA18 
relays[6]:   | Relay 06       | port.PG8 
relays[7]:   | Relay 07       | port.PG9 
relays[8]:   | Relay 08       | port.PG6 
relays[9]:   | Relay 09       | port.PG7 

Inputs list (for manual switches):
Name         |     Role       |    Port
inputs[0]:   | Free           | 
inputs[1]:   | Switch 01      | port.PA6 
inputs[2]:   | Switch 02      | port.PA1 
inputs[3]:   | Switch 03      | port.PA0 
inputs[4]:   | Switch 04      | port.PA3  
inputs[5]:   | Switch 05      | port.PA7 
inputs[6]:   | Switch 06      | port.PA8 
inputs[7]:   | Switch 07      | port.PA9 
inputs[8]:   | Switch 08      | port.PA10 
inputs[9]:   | Switch 09      | port.PA20  
"""


class Relay:
    def __init__(self, relay_state, relay_port):
        self.state = relay_state
        self.port = relay_port


# Relays list:
relays = [
    Relay(False, port.PD14),
    Relay(False, port.PC4),
    Relay(False, port.PC7),
    Relay(False, port.PA2),
    Relay(False, port.PA21),
    Relay(False, port.PA18),
    Relay(False, port.PG8),
    Relay(False, port.PG9),
    Relay(False, port.PG6),
    Relay(False, port.PG7)]

# setup the relays ports
for i in range(0, 10):
    gpio.setcfg(relays[i].port, gpio.OUTPUT)
    gpio.output(relays[i].port, gpio.HIGH)

# Inputs (switches) list:
inputs = [
    False,
    port.PA6,
    port.PA1,
    port.PA0,
    port.PA3,
    port.PA7,
    port.PA8,
    port.PA9,
    port.PA10,
    port.PA20
]

# setup the inputs ports
for i in range(1, 10):
    gpio.setcfg(inputs[i], gpio.INPUT)
    gpio.pullup(inputs[i], gpio.PULLDOWN)  # Enable pulldown resistor
    # gpio.pullup(relays[i].port, gpio.PULLUP)


def switch_relay(rel):
    if rel.state:
        rel.state = False
        gpio.output(rel.port, gpio.HIGH)
    else:
        rel.state = True
        gpio.output(rel.port, gpio.LOW)


def turn_on_relay(rel):
    rel.state = True
    gpio.output(rel.port, gpio.LOW)


def turn_off_relay(rel):
    rel.state = False
    gpio.output(rel.port, gpio.HIGH)


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
    # mpv - orangePI player (for RaspberryPI use omxplayer)
    my_file = Path(home_dir + '/Videos/' + num + '.mp4')
    if my_file.is_file():
        movie = num
        os.system(
            'mpv --loop --no-audio --no-sub --fullscreen --no-osc --osd-level=0 --term-osd=force '
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
                    os.system('killall -15 mpv')
                    t = threading.Thread(target=movies(strval))
                    t.start()
            elif val == 0:
                turn_off_relay(relays[0])
                os.system('killall -15 mpv')
                movie = 0
        elif cmd == "LED":
            if (val < 256) and (val > 0):  # LED PWM 0-255
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
            rel_no = int(cmd[3:5])  # cmd like REL05 for relays_no 00-99
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
            preset_no = int(cmd[3:5])  # cmd like PST05 for preset 00-99
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
        if gpio.input(inputs[i]) == 0:
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
        # on OrangePi there is no Event capture mechanism like capture rising edge interrupt
        # as it is on RaspberryPi
        # so you have to check periodically for any buttons change
        check_switches()
        # pass
        # time.sleep(20)
finally:
    print("Shutting down Python server")
    server.shutdown()
    server.server_close()
