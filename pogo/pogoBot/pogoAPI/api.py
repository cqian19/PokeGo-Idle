import requests
import re
import json
import random
from session import PogoSession
from throttled_session import ThrottledSession
from location import Location

from gpsoauth import perform_master_login, perform_oauth

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
    def __init__(self, username, password, provider, logger, geo_key=None):
        self.session = ThrottledSession()
        self.logger = logger
        self.provider = provider

        # User credentials
        self.username = username
        self.password = password

        self.access_token = ''
        self.geo_key = geo_key

    def createPogoSession(self, provider=None, locationLookup='', session=None):
        if self.provider:
            self.provider = provider

        # determine location
        location = None
        if session:
            location = session.location
        elif locationLookup:
            location = Location(locationLookup, self.geo_key)
            self.logger.info(location)

        if self.access_token and location:
            return PogoSession(
                self.session,
                self.provider,
                self.access_token,
                location,
                self.logger
            )

        # else something has gone wrong
        elif location is None:
            self.logger.critical('Location not found')
        elif self.access_token is None:
            self.logger.critical('Access token not generated')
        return None

    def createGoogleSession(self, locationLookup='', session=None):

        self.logger.info('Creating Google session for %s', self.username)

        r1 = perform_master_login(self.username, self.password, ANDROID_ID)
        r2 = perform_oauth(
            self.username,
            r1.get('Token', ''),
            ANDROID_ID,
            SERVICE,
            APP,
            CLIENT_SIG
        )

        self.access_token = r2.get('Auth')  # access token
        return self.createPogoSession(
            provider='google',
            locationLookup=locationLookup,
            session=session
        )

    def createPTCSession(self, locationLookup='', session=None):
        instance = self.session
        self.logger.info('Creating PTC session for %s', self.username)
        r = instance.get(LOGIN_URL)
        jdata = json.loads(r.content.decode())
        data = {
            'lt': jdata['lt'],
            'execution': jdata['execution'],
            '_eventId': 'submit',
            'username': self.username,
            'password': self.password,
        }
        authResponse = instance.post(LOGIN_URL, data=data)

        ticket = None
        try:
            ticket = re.sub('.*ticket=', '', authResponse.history[0].headers['Location'])
        except:
            self.logger.error(authResponse.json()['errors'][0])
            raise

        data1 = {
            'client_id': 'mobile-app_pokemon-go',
            'redirect_uri': 'https://www.nianticlabs.com/pokemongo/error',
            'client_secret': PTC_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'code': ticket,
        }
        r2 = instance.post(LOGIN_OAUTH, data=data1)
        self.access_token = re.sub('&expires.*', '', r2.content.decode('utf-8'))
        self.access_token = re.sub('.*access_token=', '', self.access_token)

        return self.createPogoSession(
            provider='ptc',
            locationLookup=locationLookup,
            session=session
        )

    def authenticate(self, locationLookup):
        """We already have all information, authenticate"""
        return {
            "google": self.createGoogleSession,
            "ptc": self.createPTCSession
        }[self.provider](locationLookup=locationLookup)

    def reauthenticate(self, session):
        """Reauthenticate from an old session"""
        return {
            "google": self.createGoogleSession,
            "ptc": self.createPTCSession
        }[self.provider](session=session)
