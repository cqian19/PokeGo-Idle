import struct
import time
import threading

def set_interval(func, sec):
    interval = 0
    stopped = threading.Event()
    def loop():  # executed in another thread
        nonlocal interval
        while not stopped.wait(interval):  # until stopped
            interval = sec
            func()
    t = threading.Thread(target=loop)
    t.daemon = True  # stop if the program exits
    t.start()
    return stopped

def f2i(float):
    return struct.unpack('<Q', struct.pack('<d', float))[0]


def f2h(float):
    return hex(struct.unpack('<Q', struct.pack('<d', float))[0])


def h2f(hex):
    return struct.unpack('<d', struct.pack('<Q', int(hex, 16)))[0]


def encodeLocation(loc):
    return (f2i(loc.latitude), f2i(loc.longitude), f2i(loc.altitude))


def getMs():
    return int(round(time.time() * 1000))
