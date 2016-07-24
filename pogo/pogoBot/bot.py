#!/usr/bin/python
import logging
import time
import sys
from pogoAPI import api, custom_exceptions, location
from . import fort_mod, inventory_mod, pokemon_mod


class Bot():

    def __init__(self, session):
        self.session = session
        self.fh = fort_mod.fortHandler(session)
        self.ih = inventory_mod.inventoryHandler(session)
        self.ph = pokemon_mod.pokemonHandler(session)

    # Basic bot
    def run (self):
        # Trying not to flood the servers
        cooldown = 1
        self.ih.getProfile()
        self.ih.getInventory()
        # Run the bot
        """while True:
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
        """
