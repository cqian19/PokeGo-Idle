# coding: utf-8

from flask import Flask, render_template, jsonify
from pogoBot.bot import Bot
from pogoBot.pogoAPI import api

import logging
import argparse
import sys
import threading
import time

app = Flask(__name__, template_folder="templates")

def setupLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('Line %(lineno)d,%(filename)s - %(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class MapHandler():

    lock = threading.Lock()

    def __init__(self, session, geo_key):
        self.session = session
        self.maps_key = geo_key
        app.route('/')(self.default_map)
        app.route('/data', methods=['GET'])(self.get_map_data)
        app.route('/location', methods=['GET'])(self.get_location)
        app.run(debug=False)

    def default_map(self):
        return render_template('example.html', lat=37.4419,lng=-122.1419, geo_key=self.maps_key)

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

if __name__ == "__main__":
    setupLogger()
    logging.debug('Logger set up')

    # Read in args
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

    # Create PokoAuthObject
    poko_session = api.PokeAuthSession(
        args.username,
        args.password,
        args.auth,
        geo_key=args.geo_key
    )
    # Authenticate with a given location
    # Location is not inherent in authentication
    # But is important to session
    try:
        pogo_session = poko_session.authenticate(args.location)
    except Exception as e:
        logging.error('Could not log in. Double check your login credentials. The servers may also be down.')
        raise e
    if pogo_session:
        bot = Bot(poko_session.session, pogo_session, poko_session)
        bot.run()
        mh = MapHandler(pogo_session, args.geo_key)
    else:
        logging.critical('Session not created successfully')
