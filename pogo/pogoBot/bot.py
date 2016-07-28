#!/usr/bin/python
from pogoAPI import api, custom_exceptions, location
from . import fort_mod, inventory_mod, pokemon_mod
from pogoAPI.custom_exceptions import GeneralPogoException
import logging
import threading
import time
import sys

class Bot():

    def __init__(self, session, pogo_session, poko_session):
        self.session = session
        self.pogo_session = pogo_session
        self.poko_session = poko_session
        self.fh = fort_mod.fortHandler(pogo_session)
        self.ih = inventory_mod.inventoryHandler(pogo_session)
        self.ph = pokemon_mod.pokemonHandler(pogo_session)
        self.mods = [self.fh, self.ih, self.ph]
        self.mainThread = threading.Thread(target=self.main)
        self.mainThread.daemon = True

    # Basic bot
    def main(self):
        # Trying not to flood the servers
        cooldown = 1

        # Run the bot
        while True:
            time.sleep(1)
            forts = self.fh.sortCloseForts()
            self.ph.cleanPokemon(thresholdCP=800)
            self.ih.cleanInventory()
            try:
                if forts:
                    for fort in forts:
                        pokemon = self.ph.findBestPokemon()
                        if pokemon:
                            self.ph.walkAndCatch(pokemon)
                        self.fh.walkAndSpin(fort)
                        cooldown = 1

            # Catch problems and reauthenticate
            except GeneralPogoException as e:
                logging.critical('GeneralPogoException raised: %s', e)
                self.pogo_session.pause()
                self.pogo_session = self.poko_session.reauthenticate(self.session)
                for mod in self.mods:
                    mod.setSession(self.pogo_session)
                time.sleep(cooldown)
                cooldown *= 2

            except Exception as e:
                logging.exception('Exception raised: %s', e)
                self.pogo_session.pause()
                self.pogo_session = self.poko_session.reauthenticate(self.session)
                for mod in self.mods:
                    mod.setSession(self.pogo_session)
                time.sleep(cooldown)
                cooldown *= 2

    def run (self):
        if not self.mainThread.is_alive():
            self.mainThread.start()

    def stop(self):
        self.mainThread.join()
