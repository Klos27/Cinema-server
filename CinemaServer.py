#!/usr/bin/python
import threading
import socketserver
import socket
# import RPi.GPIO as GPIO
import os
import time
from pathlib import Path

PYTHON_SERVER_PORT = 50000
PYTHON_SERVER_IP = "192.168.200.194"  # Type there server's ip

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_UP)
# GPIO.setup(24, GPIO.OUT)
# GPIO.output(24, 1)         # Turn off realy

# TODO RELAYS AND UDP CODES
# TODO Clean up code -.-
os.system('killall -15 mpv')

relay = 0  # relay turned off
timeout = 0
counter = 0


def movies(num):
    """Thread omxplayer-raspberryPI (mpv - orangePI) function"""
    #    print('Play the movie')
    time.sleep(2)  # Wait until monitor turns on -- Tutaj wpisz ile sekund na rozruch monitora

    my_file = Path('/home/agstakino/Videos/' + num + '.mp4')
    if my_file.is_file():
        os.system(
            'mpv --loop --no-audio --no-sub --fullscreen --no-osc --osd-level=0 --term-osd=force /home/agstakino/Videos/' + num + '.mp4')
    # print("Kill the movie")
    else:
        print("No such file")
    return


# Put the code you want to do something based on when you get data here.
def onData(data, sock, client_address):
    global counter
    #    print("Python got data: " + data.decode("utf-8"))
    msg = data.decode("utf-8")
    #    print(msg)
    #    print("client_addr: ", client_address)
    # sock.sendto(data, (client_address[0], 50001))     #ECHO SERVER
    try:
        cmd = msg[:msg.rindex(' ')]
        #        print(cmd)
        strval = msg[msg.rindex(' ') + 1:]
        val = int(strval)
        #        print(strval)
        # TODO write there cases
        if cmd == "MOV":
            if (val <= 10) and (val > 0):   # 9 movies from 1.mp4 to 10.mp4 to show on projector
                my_file = Path('/home/agstakino/Videos/' + strval + '.mp4')
                if my_file.is_file():  # start movie only if file exists
                    # TODO turn on projector relay
                    os.system('killall -15 mpv')
                    t = threading.Thread(target=movies(strval))
                    t.start()
            elif val == 0:
                os.system('killall -15 mpv')
                # TODO turn off projector relay
            # else:
            #     print("Wrong MOV number")
        elif cmd == "LED":
            if (val < 256) and (val > 0):   # LED PWM 0-255
                #               print("LED set to -> " + strval)
                sock.sendto(("LED set to -> " + strval).encode(), (client_address[0], 50001))
            elif val == 0:
                sock.sendto("LED TURNED OFF: value is set to 0".encode(), (client_address[0], 50001))
                #                print("LED TURNED OFF: value is set to 0")
                #           else:
                #                print("Wrong LED value")
    except ValueError:
        if msg == "state":
            # TODO send back system's state
            #           print("HELLO THERE")
            # sockOut = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msgToSent = "HELLO THERE " + str(counter)
            counter = counter + 1
            sock.sendto(msgToSent.encode(), (client_address[0], 50001))
            # sock.connect(client_address + ":50000")
            # sock.sendall("HELLO THERE".encode())
            # sock.sendto("HELLO THERE".encode(), client_address)
            # sock.send("Hello There".encode())
            # finally:
            #     sock.close()
        else:
            #           print("Oops!  That was no valid number.  Try again...")
            sock.sendto("WRONG CODE!".encode(), (client_address[0], 50001))


class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]
        onData(data, sock, self.client_address)


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass

# START SERVER
try:
    server = ThreadedUDPServer((PYTHON_SERVER_IP, PYTHON_SERVER_PORT), ThreadedUDPRequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    print("Server loop running in thread: ", server_thread.name)
    while True:
        pass
        # time.sleep(20)
finally:
    print("Shutting down Python server")
    server.shutdown()
    server.server_close()
