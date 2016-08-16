#!/usr/bin/python
import logging
import threading
import time

from .pogoAPI.custom_exceptions import GeneralPogoException
from . import fort_mod, inventory_mod, pokemon_mod


class Bot():

    def __init__(self, session, pogo_session, poko_session, logger, config):
        self.session = session
        self.pogo_session = pogo_session
        self.poko_session = poko_session
        self.logger = logger
        self.fh = fort_mod.fortHandler(pogo_session, logger, config)
        self.ih = inventory_mod.inventoryHandler(pogo_session, logger, config)
        self.ph = pokemon_mod.pokemonHandler(pogo_session, logger, config)
        self.mods = [self.fh, self.ih, self.ph]
        self.started = False
        self.mainThread = None

    # Basic bot
    def main(self):
        # Trying not to flood the servers
        cooldown = 1

        # Run the bot
        while self.started:
            time.sleep(1)
            try:
                self.ph.cleanPokemon()
                self.ih.cleanInventory()
                pokemon = self.ph.findBestPokemon()

                if pokemon:
                    for i in self.ph.walkAndCatch(pokemon):
                        if not self.started:
                            break
                        forts = self.fh.sortCloseForts()
                        self.fh.spinAll(forts)
                        cooldown = 1
                else:
                    forts = self.fh.findClosestForts(num=4)
                    if forts:
                        for fort in forts:
                            self.fh.walkAndSpin(fort)
                            if self.ph.findBestPokemon():
                                break

            # Catch problems and reauthenticate
            except GeneralPogoException as e:
                logging.critical('GeneralPogoException raised: %s', e)
                self.pogo_session.pause()
                time.sleep(5)
                self.pogo_session = self.poko_session.reauthenticate(self.pogo_session)
                for mod in self.mods:
                    mod.setSession(self.pogo_session)
                time.sleep(cooldown)
                cooldown *= 2

            except Exception as e:
                logging.exception('Exception raised: %s', e)
                self.pogo_session.pause()
                time.sleep(5)
                self.pogo_session = self.poko_session.reauthenticate(self.pogo_session)
                for mod in self.mods:
                    mod.setSession(self.pogo_session)
                time.sleep(cooldown)
                cooldown *= 2

    def run(self):
        self.started = True
        if self.mainThread and self.mainThread.is_alive():
            self.mainThread.join()
        self.mainThread = threading.Thread(target=self.main)
        self.mainThread.start()

    def stop(self):
        self.started = False
        self.mainThread.join()
