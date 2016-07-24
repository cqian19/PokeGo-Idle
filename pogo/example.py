# coding: utf-8

from flask import Flask, render_template, jsonify
from pogoBot.bot import Bot
from pogoBot.pogoAPI import api

import logging
import argparse
import sys

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

    def __init__(self, session):
        self.session = session
        app.route('/')(self.fullmap)
        app.route('/data', methods=['GET'])(self.get_map_data)

    def fullmap(self):
        return render_template('example.html', lat=37.4419,lng=-122.1419)

    def get_map_data(self):
        data = {}
        cells = self.session.getMapObjects()
        data['location'] = self.session.getCoordinates()
        data['pokemon'] = self.session.cleanPokemon(cells)
        data['forts'] = self.session.cleanStops(cells)
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
    session = poko_session.authenticate(args.location)

    # Time to show off what we can do
    if session:
        bot = Bot(session)
        bot.run()
    else:
        logging.critical('Session not created successfully')
    app.config['GOOGLEMAPS_KEY'] = args.geo_key
    mh = MapHandler(session)
    app.run(debug=True, use_reloader=True)
