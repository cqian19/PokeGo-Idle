# coding: utf-8

import logging
import threading

from flask import Flask, render_template, jsonify, request, redirect, url_for

from pogoBot.bot import Bot
from pogoBot.pogoAPI.api import PokeAuthSession
from pogoBot.pogoAPI.custom_exceptions import GeneralPogoException
from config import Config

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

    def __init__(self, logger):
        self.is_logged_in = False
        self.first_login = True
        self.logger = logger
        self.config = Config()
        app.route('/', methods = ['GET', 'POST'])(self.login)
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
        return jsonify(d)

    def search(self):
        loc = request.json['location']
        print(loc)
        status = 1
        try:
            self.bot.stop()
            self.session.changeLocation(loc)
        except Exception as e:
            status = 0
        self.bot.run()
        return jsonify({'status': str(status)})

    def login(self, error=None):
        if request.method == 'GET':
            if self.is_logged_in:
                return redirect(url_for('default_map'))
        if request.method == 'POST':
            print(request.form)
            try:
                self.do_login(request.form)
            except GeneralPogoException as e:
                error = e.__str__()
            except Exception as e:
                self.logger.exception(e)
                error = "Internal server error: " + e.__str__()
            else:
                self.is_logged_in = True
                app.route('/game', methods=['GET'])(self.default_map)
                app.route('/data', methods=['GET'])(self.get_map_data)
                app.route('/loggedIn', methods=['GET'])(self.logged_in)
                app.route('/location', methods=['GET'])(self.get_location)
                app.route('/pastInfo', methods=['GET'])(self.get_past_items)
                app.route('/playerData', methods=['GET'])(self.get_profile)
                app.route('/search', methods=['POST'])(self.search)
                return redirect(url_for('default_map'))
        if self.first_login:
            config = self.config.get_config()
            self.first_login = False
        else:
            config = {}
        return render_template('login.html', error=error, config=config)

    def do_login(self, args):
        # Currently has username, password, method, api_key, location
        # Create PokoAuthObject
        poko_session = PokeAuthSession(
            args['username'],
            args['password'],
            args['method'],
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
        else:
            self.config.update_config({
                'username': args['username'],
                'key': args['api_key'],
                'location': args['location'],
                'method': args['method']
            })
            self.maps_key = args['api_key']
            self.session = pogo_session
            self.bot = Bot(poko_session.session, pogo_session, poko_session, logger)
            self.bot.run()

if __name__ == "__main__":
    logger = setupLogger()
    logger.debug('Logger set up')
    MapHandler(logger)

