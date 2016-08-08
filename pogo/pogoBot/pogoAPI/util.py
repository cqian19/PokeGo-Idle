import datetime
import struct
import threading
import time
import xxhash

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

class Rand48(object):
    def __init__(self, seed):
        self.n = seed
    def seed(self, seed):
        self.n = seed
    def srand(self, seed):
        self.n = (seed << 16) + 0x330e
    def next(self):
        self.n = (25214903917 * self.n + 11) & (2**48 - 1)
        return self.n
    def drand(self):
        return self.next() / 2**48
    def lrand(self):
        return self.next() >> 17
    def mrand(self):
        n = self.next() >> 16
        if n & (1 << 31):
            n -= 1 << 32
        return n   

def long_to_bytes (val, endianness='big'):
    """
    Use :ref:`string formatting` and :func:`~binascii.unhexlify` to
    convert ``val``, a :func:`long`, to a byte :func:`str`.
    :param long val: The value to pack
    :param str endianness: The endianness of the result. ``'big'`` for
      big-endian, ``'little'`` for little-endian.
    If you want byte- and word-ordering to differ, you're on your own.
    Using :ref:`string formatting` lets us use Python's C innards.
    """

    # one (1) hex digit per four (4) bits
    width = val.bit_length()

    # unhexlify wants an even multiple of eight (8) bits, but we don't
    # want more digits than we need (hence the ternary-ish 'or')
    width += 8 - ((width % 8) or 8)

    # format width specifier: four (4) bits per hex digit
    fmt = '%%0%dx' % (width // 4)

    # prepend zero (0) to the width, to zero-pad the output
    s = unhexlify(fmt % val)

    if endianness == 'little':
        # see http://stackoverflow.com/a/931095/309233
        s = s[::-1]

    return s
    
def generateLocation1(authticket, lat, lng, alt): 
    firstHash = xxhash.xxh32(authticket, seed=0x1B845238).intdigest()
    locationBytes = d2h(lat) + d2h(lng) + d2h(alt)
    if not alt:
        alt = "\x00\x00\x00\x00\x00\x00\x00\x00"
    return xxhash.xxh32(locationBytes, seed=firstHash).intdigest()

def generateLocation2(lat, lng, alt):
    locationBytes = d2h(lat) + d2h(lng) + d2h(alt)
    if not alt:
        alt = "\x00\x00\x00\x00\x00\x00\x00\x00"
    return xxhash.xxh32(locationBytes, seed=0x1B845238).intdigest()      #Hash of location using static seed 0x1B845238

def generateRequestHash(authticket, request):
    firstHash = xxhash.xxh64(authticket, seed=0x1B845238).intdigest()                      
    return xxhash.xxh64(request, seed=firstHash).intdigest()

def d2h(f):
   hex = f2h(f)[2:].replace('L','')
   hex = ("0" * (len(hex) % 2)) + hex
   return  hex.decode("hex")