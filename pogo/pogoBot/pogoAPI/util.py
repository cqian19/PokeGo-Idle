import datetime
import struct
import threading
import time


def getJSTime():
    d = datetime.datetime.utcnow()
    for_js = int(time.mktime(d.timetuple())) * 1000
    return for_js

def set_interval(func, sec):
    interval = 0
    stopped = threading.Event()
    outside = threading.Event()
    def loop():  # executed in another thread
        nonlocal interval
        while not stopped.wait(interval) and outside.wait():  # until stopped
            interval = sec
            func()
    outside.set()
    t = threading.Thread(target=loop)
    t.daemon = True  # stop if the program exits
    t.start()
    return outside

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
