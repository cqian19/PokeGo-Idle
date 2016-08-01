from pogoAPI.inventory import items
from mod import Handler
import time


class inventoryHandler(Handler):

    # Get profile
    def getProfile(self):
        self.logger.info("Printing Profile:")
        profile = self.session.checkProfile()
        self.logger.info(profile)

    # Do Inventory stuff
    def getInventory(self):
        self.logger.info("Get Inventory:")
        self.logger.info(self.session.checkInventory())


    # A very brute force approach to evolving
    def evolveAllPokemon(self):
        inventory = self.session.checkInventory()
        for pokemon in inventory["party"]:
            self.logger.info(self.session.evolvePokemon(pokemon))
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
        self.logger.info("Cleaning out Inventory...")
        bag = self.session.checkInventory().bag
        itemsCount = sum(map(lambda b: int(b), bag.values()))
        maxItems = self.session.checkPlayerData().max_item_storage
        self.logger.info("Inventory capacity {0}/{1}".format(itemsCount, maxItems))
        if (itemsCount/maxItems) < .8: return
        # Clear out all of a crtain type
        tossable = [items.POTION, items.SUPER_POTION, items.REVIVE]
        for toss in tossable:
            if toss in bag:
                self.session.recycleItem(toss, bag[toss])

        # Limit a certain type
        limited = {
            items.POKE_BALL: 50,
            items.GREAT_BALL: 100,
            items.ULTRA_BALL: 150,
            items.RAZZ_BERRY: 25,
            items.REVIVE: 10,
            items.HYPER_POTION: 20,
        }
        for limit in limited:
            if limit in bag and int(bag[limit]) > limited[limit]:
                self.session.recycleItem(limit, bag[limit] - limited[limit])