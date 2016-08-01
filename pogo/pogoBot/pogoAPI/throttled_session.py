from requests import Request, session
from requests_throttler import BaseThrottler
import logging
THROTTLE_DELAY = 1/3 + .05

class ThrottledSession():

    def __init__(self):
        super().__init__()
        self.session = self.createBaseSession()
        self.throttle = BaseThrottler(name='mainThrottle', session=self.session, delay=THROTTLE_DELAY)
        self.throttle.start()
        self.orig = None

    def createBaseSession(self):
        sess = session()
        sess.headers = {
            'User-Agent': 'Niantic App',
        }
        sess.verify = False
        return sess

    def post(self, url, **kwargs):
        wrapper = Request(method='POST', url=url, **kwargs)
        res = self.throttle.submit(wrapper).response
        return res

    def get(self, url, **kwargs):
        wrapper = Request(method='GET', url=url, **kwargs)
        res = self.throttle.submit(wrapper).response
        return res

    def restart(self):
        if self.orig:
            self.throttle.shutdown()
            self.throttle = self.orig
            self.throttle.unpause()
            self.orig = None

    def pauseExec(self):
        self.orig = self.throttle
        self.orig.pause()
        self.throttle = BaseThrottler(name='mainThrottle', session=self.session, delay=THROTTLE_DELAY)
        self.throttle.start()

    def stop(self):
        self.throttle.shutdown()