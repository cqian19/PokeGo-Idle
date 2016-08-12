import datetime
import struct
import threading
import time
import os
import sys
import platform
import pprint

def fprint(response):
    print('Response dictionary:\n\r{}'.format(pprint.PrettyPrinter(indent=2).pformat(response)))

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

def get_encryption_lib_path():
    lib_path = ""
    # win32 doesn't mean necessarily 32 bits
    if sys.platform == "win32":
        if platform.architecture()[0] == '64bit':
            lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/encrypt64bit.dll"))
        else:
            lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/encrypt32bit.dll"))

    elif sys.platform == "darwin":
        lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/libencrypt-osx-64.so"))

    elif os.uname()[4].startswith("arm") and platform.architecture()[0] == '32bit':
        lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/libencrypt-linux-arm-32.so"))

    elif sys.platform.startswith('linux'):
        if platform.architecture()[0] == '64bit':
            lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/libencrypt-linux-x86-64.so"))
        else:
            lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/libencrypt-linux-x86-32.so"))

    elif sys.platform.startswith('freebsd-10'):
        lib_path = os.path.join(os.path.dirname(__file__), os.path.relpath("encrypt/libencrypt-freebsd10-64.so"))
    else:
        err = "Unexpected/unsupported platform '{}'".format(sys.platform)
        raise Exception(err)

    if not os.path.isfile(lib_path):
        err = "Could not find {} encryption library {}".format(sys.platform, lib_path)
        raise Exception(err)
    return lib_path

def is_float(num):
    try:
        float(num)
        return True
    except ValueError:
        return False