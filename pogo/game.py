# coding: utf-8

from flask import Flask, render_template, jsonify, request, redirect, url_for
from pogoBot.bot import Bot
from pogoBot.pogoAPI import api, custom_exceptions
from custom_exceptions import GeneralPogoException

import logging
import argparse
import sys
import threading
import time
import os

app = Flask(__name__, template_folder="templates")

def setupLogger():
    logger = logging.getLogger('requests_throttler')
    logger.propagate = False
    logger = logging.getLogger('urllib3')
    logger.propagate = False

    logger = logging.getLogger(__name__)
    logger.propagate = True
    ch = logging.StreamHandler()
    formatter = logging.Formatter('Line %(lineno)d,%(filename)s - %(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.setLevel(logging.INFO)
    logger.info("Logging set up")
    return logger

class MapHandler():

    lock = threading.Lock()

    def __init__(self):
        self.is_logged_in = False
        app.route('/', methods = ['GET', 'POST'])(self.login)
        """"""
        app.run(debug=False, port=5000)

    def default_map(self):
        lat, lon, _ = self.session.getter.getCoordinates()
        return render_template('game.html', lat=lat, lon=lon, geo_key=self.maps_key)

    def get_map_data(self):
        data = {}
        data['pokemon'] = self.session.cleanPokemon()
        data['forts'] = self.session.cleanStops()
        data['caughtPokemon'] = self.session.cleanPokemon(self.session.getter.getCaughtPokemon())
        return jsonify(data)

    def get_location(self):
        data = {
            'location': self.session.getter.getCoordinates()
        }
        return jsonify(data)

    def get_past_items(self):
        return jsonify(self.session.getter.getPastNotifications())

    def get_profile(self):
        return jsonify(self.session.cleanPlayerInfo())

    def logged_in(self):
        d = {'status': '1' if self.is_logged_in else '0'}
        print(d)
        return jsonify(d)

    def login(self, error=None):
        if request.method == 'GET':
            if self.is_logged_in:
                return redirect(url_for('default_map'))
        if request.method == 'POST':
            print(request.form)
            try:
                self.doLogin(request.form)
            except GeneralPogoException as e:
                error = e.__str__()
            except Exception as e:
                print(e)
                error = "Internal server error: " + e.__str__()
            else:
                self.is_logged_in = True
                app.route('/game', methods=['GET'])(self.default_map)
                app.route('/data', methods=['GET'])(self.get_map_data)
                app.route('/loggedIn', methods=['GET'])(self.logged_in)
                app.route('/location', methods=['GET'])(self.get_location)
                app.route('/pastInfo', methods=['GET'])(self.get_past_items)
                app.route('/playerData', methods=['GET'])(self.get_profile)
                return redirect(url_for('default_map'))
        return render_template('login.html', error=error)

    def doLogin(self, args):
        print("AUTH")
        # Create PokoAuthObject
        poko_session = api.PokeAuthSession(
            args['username'],
            args['password'],
            args['options'],
            logger,
            geo_key=args['api_key'],
        )
        # Authenticate with a given location
        # Location is not inherent in authentication
        # But is important to session
        try:
            pogo_session = poko_session.authenticate(args['location'])
        except Exception as e:
            logging.error('Could not log in. Double check your login credentials. The servers may also be down.')
            raise e
        self.maps_key = args['api_key']
        self.session = pogo_session
        print("DONE")
        if pogo_session:
            bot = Bot(poko_session.session, pogo_session, poko_session, logger)
            bot.run()

if __name__ == "__main__":
    logger = setupLogger()
    logger.debug('Logger set up')
    MapHandler()
    """"# Read in args
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", help="Auth Service", required=True)
    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)
    parser.add_argument("-l", "--location", help="Location", required=True)
    parser.add_argument("-g", "--geo_key", help="GEO API Secret", required = True)
    args = parser.parse_args()

    # Check service
    if args.auth not in ['ptc', 'google']:
        logging.error('Invalid auth service {}'.format(args.auth))
        sys.exit(-1)
    print("AUTH")"""

