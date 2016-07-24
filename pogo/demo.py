#!/usr/bin/python
import argparse
import logging
import time
import sys
from pogoAPI import api, custom_exceptions, location
from pogoBot import fort_mod, inventory_mod, pokemon_mod
def setupLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('Line %(lineno)d,%(filename)s - %(asctime)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class Bot():

    def __init__(self, session):
        self.session = session
        self.fh = fort_mod.fortHandler(session)
        self.ih = inventory_mod.inventoryHandler(session)
        self.ph = pokemon_mod.pokemonHandler(session)

    # Basic bot
    def simpleBot(self):
        # Trying not to flood the servers
        cooldown = 1

        # Run the bot
        while True:
            try:
                forts = self.fh.sortCloseForts(session)
                for fort in forts:
                    pokemon = self.ph.findClosestPokemon(session)
                    self.ph.walkAndCatch(session, pokemon)
                    self.ph.walkAndSpin(session, fort)
                    cooldown = 1
                    time.sleep(1)

            # Catch problems and reauthenticate
            except custom_exceptions.GeneralPogoException as e:
                logging.critical('GeneralPogoException raised: %s', e)
                session = poko_session.reauthenticate(session)
                time.sleep(cooldown)
                cooldown *= 2

            except Exception as e:
                logging.critical('Exception raised: %s', e)
                session = poko_session.reauthenticate(session)
                time.sleep(cooldown)
                cooldown *= 2

# Entry point
# Start off authentication and demo
if __name__ == '__main__':
    setupLogger()
    logging.debug('Logger set up')

    # Read in args
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--auth", help="Auth Service", required=True)
    parser.add_argument("-u", "--username", help="Username", required=True)
    parser.add_argument("-p", "--password", help="Password", required=True)
    parser.add_argument("-l", "--location", help="Location", required=True)
    parser.add_argument("-g", "--geo_key", help="GEO API Secret")
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
        """
        getProfile(session)
        getInventory(session)

        # Pokemon related
        pokemon = findClosestPokemon(session)
        walkAndCatch(session, pokemon)

        # Pokestop related
        fort = findClosestFort(session)
        walkAndSpin(session, fort)
        """
    else:
        logging.critical('Session not created successfully')
