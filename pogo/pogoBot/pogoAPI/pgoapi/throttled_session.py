import time

from requests import Request, session
from requests_throttler import BaseThrottler


class ThrottledSession():

    def __init__(self, config):
        super().__init__()
        self.session = self.createBaseSession()
        self.config = config
        self._delay = config.get('requestDelay')
        self.session.headers.update({'User-Agent': 'Niantic App'})
        self.session.verify = True
        self.throttle = BaseThrottler(name='mainThrottle', session=self.session, delay=self._delay)
        self.throttle.start()
        self.orig = None

    def getThrottle(self):
        return self.throttle

    def createBaseSession(self):
        sess = session()
        sess.headers = {
            'User-Agent': 'Niantic App',
        }
        sess.verify = False
        return sess

    def updateDelay(self):
        config_delay = self.config.get('requestDelay')
        if self._delay != config_delay:
            self._delay = config_delay
            if self.throttle:
                self.throttle._delay = self._delay

    def post(self, url, **kwargs):
        self.updateDelay()
        wrapper = Request(method='POST', url=url, **kwargs)
        res = self.throttle.submit(wrapper).response
        return res

    def get(self, url, **kwargs):
        self.updateDelay()
        wrapper = Request(method='GET', url=url, **kwargs)
        res = self.throttle.submit(wrapper).response
        return res

    def makeThrottle(self):
        throttle = BaseThrottler(name='mainThrottle', session=self.session, delay=self._delay)
        return throttle

    def restart(self):
        if self.orig:
            self.throttle.shutdown()
            self.throttle = self.orig
            self.throttle.unpause()
            self.orig = None

    def pauseExec(self):
        self.orig = self.throttle
        self.orig.pause()
        self.throttle = self.makeThrottle()
        self.throttle.start()

    def stop(self):
        self.throttle.shutdown()

    def makeNew(self):
        self.throttle.shutdown()
        time.sleep(1)
        self.throttle = self.makeThrottle()
        self.throttle.start()