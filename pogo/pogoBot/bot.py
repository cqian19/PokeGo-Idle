#!/usr/bin/python
from pogoAPI import api, custom_exceptions, location
from . import fort_mod, inventory_mod, pokemon_mod
from pogoAPI.custom_exceptions import GeneralPogoException
import logging
import threading
import time
import sys

class Bot():

    def __init__(self, session, poko_session):
        self.session = session
        self.poko_session = poko_session
        self.fh = fort_mod.fortHandler(session)
        self.ih = inventory_mod.inventoryHandler(session)
        self.ph = pokemon_mod.pokemonHandler(session)
        self.mods = [self.fh, self.ih, self.ph]

    # Basic bot
    def main(self):
        # Trying not to flood the servers
        cooldown = 1

        # Run the bot
        while True:
            time.sleep(1)
            forts = self.fh.sortCloseForts()
            self.ph.cleanPokemon(thresholdCP=300)
            self.ih.cleanInventory()
            try:
                for fort in forts:
                    pokemon = self.ph.findBestPokemon()
                    self.ph.walkAndCatch(pokemon)
                    self.fh.walkAndSpin(fort)
                    cooldown = 1

            # Catch problems and reauthenticate
            except GeneralPogoException as e:
                logging.critical('GeneralPogoException raised: %s', e)
                self.session.pause()
                self.session = self.poko_session.reauthenticate(self.session)
                for mod in self.mods:
                    mod.setSession(self.session)
                time.sleep(cooldown)
                cooldown *= 2

            except Exception as e:
                logging.critical('Exception raised: %s', e)
                self.session.pause()
                self.session = self.poko_session.reauthenticate(self.session)
                for mod in self.mods:
                    mod.setSession(self.session)
                time.sleep(cooldown)
                cooldown *= 2

    def run (self):
        if not hasattr(self, 'mainThread'):
            self.mainThread = threading.Thread(target=self.main)
        self.mainThread.start()

    def stop(self):
        if self.mainThread:
            self.mainThread.stop()
