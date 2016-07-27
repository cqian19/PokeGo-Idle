from pogoAPI.inventory import items
from mod import Handler
import logging
import time


class inventoryHandler(Handler):

    # Get profile
    def getProfile(self):
        logging.info("Printing Profile:")
        profile = self.session.checkProfile()
        logging.info(profile)

    # Do Inventory stuff
    def getInventory(self):
        logging.info("Get Inventory:")
        logging.info(self.session.checkInventory())


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
        return self.session.recycleItem(items.REVIVE, bag[items.REVIVE])


    # Set an egg to an incubator
    def setEgg(self):
        inventory = self.session.checkInventory()

        # If no eggs, nothing we can do
        if len(inventory["eggs"]) == 0:
            return None

        egg = inventory["eggs"][0]
        incubator = inventory["incubators"][0]
        return self.session.setEgg(incubator, egg)

    def cleanInventory(self):
        logging.info("Cleaning out Inventory...")
        bag = self.session.checkInventory().bag
        items = sum(bag.values())
        maxItems = self.session.checkPlayerData().max_item_storage
        logging.info("Inventory capacity {0}/{1}".format(items, maxItems))
        if (items/maxItems) < .9: return
        # Clear out all of a crtain type
        tossable = [items.POTION, items.SUPER_POTION, items.REVIVE]
        keep = {
            items.POTION: 0,
            items.SUPER_POTION : 20,
            items.REVIVE: 10
        }
        for toss in tossable:
            if toss in bag and bag[toss] - keep[toss] > 0:
                self.session.recycleItem(toss, bag[toss] - keep[toss])

        # Limit a certain type
        limited = {
            items.POKE_BALL: 50,
            items.GREAT_BALL: 100,
            items.ULTRA_BALL: 150,
            items.RAZZ_BERRY: 25
        }
        for limit in limited:
            if limit in bag and bag[limit] > limited[limit]:
                self.session.recycleItem(limit, bag[limit] - limited[limit])