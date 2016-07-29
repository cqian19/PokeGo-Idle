from requests import Request, session
from requests_throttler import BaseThrottler

THROTTLE_DELAY = 1/3

class ThrottledSession():

    def __init__(self):
        super().__init__()
        self.session = self.createBaseSession()
        self.throttle = BaseThrottler(name='mainThrottle', session=self.session, delay=THROTTLE_DELAY)
        self.throttle.start()

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

    def stop(self):
        self.throttle.shutdown()