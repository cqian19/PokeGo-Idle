import logging
import time


class inventoryHandler():

    def __init__(self,session):
        self.session = session

    # Get profile
    def getProfile(self):
        logging.info("Printing Profile:")
        profile = self.session.getProfile()
        logging.info(profile)

    # Do Inventory stuff
    def getInventory(self):
        logging.info("Get Inventory:")
        logging.info(self.session.getInventory())


    # A very brute force approach to evolving
    def evolveAllPokemon(self):
        inventory = self.session.checkInventory()
        for pokemon in inventory["party"]:
            logging.info(self.session.evolvePokemon(pokemon))
            time.sleep(1)


    # You probably don't want to run this
    def releaseAllPokemon(self):
        inventory = self.session.checkInventory()
        for pokemon in inventory["party"]:
            self.session.releasePokemon(pokemon)
            time.sleep(1)


    # Just incase you didn't want any revives
    def tossRevives(self):
        bag = self.session.checkInventory()["bag"]

        # 201 are revives.
        # TODO: We should have a reverse lookup here
        return self.session.recycleItem(201, bag[201])


    # Set an egg to an incubator
    def setEgg(self):
        inventory = self.session.checkInventory()

        # If no eggs, nothing we can do
        if len(inventory["eggs"]) == 0:
            return None

        egg = inventory["eggs"][0]
        incubator = inventory["incubators"][0]
        return self.session.setEgg(incubator, egg)