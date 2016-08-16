from .custom_exceptions import GeneralPogoException
from .location import Location
from .pgoapi import pgoapi
from .session import PogoSession
from .util import get_encryption_lib_path
# Callbacks and Constants
API_URL = 'https://pgorelease.nianticlabs.com/plfe/rpc'
LOGIN_URL = 'https://sso.pokemon.com/sso/login?service=https%3A%2F%2Fsso.pokemon.com%2Fsso%2Foauth2.0%2FcallbackAuthorize'
LOGIN_OAUTH = 'https://sso.pokemon.com/sso/oauth2.0/accessToken'
PTC_CLIENT_SECRET = 'w8ScCUXJQc6kXKw8FiOhd8Fixzht18Dq3PEVkUCP5ZPxtgyWsbTvWHFLm2wNY0JR'
ANDROID_ID = '9774d56d682e549c'
SERVICE = 'audience:server:client_id:848232511240-7so421jotr2609rmqakceuu1luuq0ptb.apps.googleusercontent.com'
APP = 'com.nianticlabs.pokemongo'
CLIENT_SIG = '321187995bc7cdc2b5fc91b11a96e2baa8602c62'


class PokeAuthSession():
    def __init__(self, username, password, provider, logger, config, geo_key=None):
        if geo_key and not geo_key.startswith('AIza'):
            raise GeneralPogoException("Google Maps key is invalid. Must start with 'AIza'")
        self.geo_key = geo_key
        self.logger = logger
        self.config = config
        self.provider = provider
        self.api = pgoapi.PGoApi(config)
        self.api.activate_signature(get_encryption_lib_path())
        self.session = self.api.get_session()
        # User credentials
        self.username = username
        self.password = password


    def setLocation(self, locationLookup, pogo_session=None):
        # determine location
        location = None
        if pogo_session:
            location = pogo_session.location
        elif locationLookup:
            location = Location(locationLookup, self.geo_key, self.api)
            self.logger.info(location)
        if location:
            self.api.set_position(*location.getCoordinates())
            return location
        else:
            raise GeneralPogoException('Location not found')

    def createPogoSession(self, location, provider=None, pogo_session=None):
        getter = None if not pogo_session else pogo_session.getter
        return PogoSession(
            self.session,
            self.provider,
            location,
            self.logger,
            self.api,
            self.config,
            getter=getter
        )

    def createGoogleSession(self, locationLookup='', pogo_session=None):
        self.logger.info('Creating Google session for %s', self.username)
        location = self.setLocation(locationLookup, pogo_session)
        log = self.api.login('google', self.username, self.password, app_simulation=False)
        if not log:
            raise GeneralPogoException("Google login failed. Double check your login info.")
        return self.createPogoSession(
            location,
            provider='google',
            pogo_session=pogo_session
        )

    def createPTCSession(self, locationLookup='', pogo_session=None):
        instance = self.session
        self.logger.info('Creating PTC session for %s', self.username)
        location = self.setLocation(locationLookup, pogo_session)
        log = self.api.login('ptc', self.username, self.password, app_simulation=False)
        if not log:
            raise GeneralPogoException("Google login failed. Double check your login info.")
        return self.createPogoSession(
            location,
            pogo_session=pogo_session
        )

    def authenticate(self, locationLookup):
        """We already have all information, authenticate"""
        return {
            "google": self.createGoogleSession,
            "ptc": self.createPTCSession
        }[self.provider](locationLookup=locationLookup)

    def reauthenticate(self, pogo_session):
        if self.session:
            self.session = self.api.make_new_session()
        return {
            "google": self.createGoogleSession,
            "ptc": self.createPTCSession
        }[self.provider](pogo_session=pogo_session)
