import logging
import random
import threading
import time
import math
from datetime import datetime
from . import location
from .inventory import Inventory, items
from .pokedex import pokedex
from .util import set_interval, fprint, getJSTime
from .custom_exceptions import GeneralPogoException

RPC_ID = int(random.random() * 10 ** 12)
STOP_COOLDOWN = 305

class Getter():

    def __init__(self, state, location, api, logger, config):
        # self._state = state
        self.location = location
        self._state = state
        self.api = api
        self.logger = logger
        self.config = config
        self.locChanged = False
        # Set up Inventory
        self.pokemon = {}
        self.caughtPokemon = []
        self.pastStops = {}
        self.pastEvents = []
        self.forts = {}
        self.gyms = {}
        self.stops = {}
        self.inventory = None
        self.threads = []
        self.threadBlock = threading.Event()
        self.lock = threading.Lock()
        time.sleep(1)
        self.getProfile()

    @staticmethod
    def getDefaults(req):
        req.get_inventory(last_timestamp_ms=0)
        req.get_hatched_eggs()
        req.check_awarded_badges()
        req.download_settings(hash="4a2e9bc330dae60e7b74fc85b98868ab4700802e")

    def parseDefault(self, res):
        try:
            self._state.eggs = res['GET_HATCHED_EGGS'] # Currently only success
            self._state.inventory = res['GET_INVENTORY']
            self.parsePlayerStats(self._state.inventory)
            self._state.badges = res['CHECK_AWARDED_BADGES'] # Currently only success
            self._state.settings = res['DOWNLOAD_SETTINGS']
        except KeyError as e:
            raise GeneralPogoException("Player profile is missing a field. Possible hardban.")
        except Exception as e:
            logging.exception(e)

        # Finally make inventory usable
        item = self._state.inventory['inventory_delta']['inventory_items']
        self.inventory = Inventory(item)

    def parsePlayerStats(self, inventory):
        for i in inventory['inventory_delta']['inventory_items']:
            if 'player_stats' in i['inventory_item_data']:
                stats = i['inventory_item_data']['player_stats']
                level = stats['level']
                self._state.playerStats = stats
                break

    def getCoordinates(self):
        return self.location.getCoordinates()

    # Core api calls
    # Get profile
    def getProfile(self):
        # Create profile request
        req = self.api.create_request()
        # self.threadBlock.wait()
        req.get_player()
        self.getDefaults(req)
        try:
            res = req.call()
            res = res['responses']
        except:
            raise GeneralPogoException("Getting profile failed. Double check your username and password.")
        # Parse
        self.parseDefault(res)
        self._state.profile = res['GET_PLAYER']
        self._state.player_data = self._state.profile['player_data']
        # Return everything
        return self._state.profile

    def getFortSearch(self, fort):
        # Create request
        res = self.api.fort_search(
            fort_id=fort['id'],
            player_latitude=self.location.latitude,
            player_longitude=self.location.longitude,
            fort_latitude=fort['latitude'],
            fort_longitude=fort['longitude']
        )
        self._state.fortSearch = res['responses']['FORT_SEARCH']
        return self._state.fortSearch

    def getFortDetails(self, fort):
        # Create request
        res = self.api.fort_details(
            fort_id=fort['id'],
            latitude=fort['latitude'],
            longitude=fort['longitude'],
        )
        self._state.fortDetails = res['responses']['FORT_DETAILS']
        return self._state.fortDetails

    # Hooks for those bundled in default
    def getMapObjects(self):
        with self.lock:
            radius = self.config.get('searchRadius')
            if not self.radius or self.radius != radius:
                # Radius changed
                changed = self._updateGMOTime(radius)
                self.radius = radius
                if changed: return
            steps = self.location.getAllSteps(radius)
            for lat, lon in steps:
                cells = self.location.getCells(lat, lon)
                timestamps = [0, ] * len(cells)
                time.sleep(1)
                self.threadBlock.wait()
                res = self.api.get_map_objects(
                    location_override=(lat, lon, 8),
                    cell_id = cells,
                    since_timestamp_ms = timestamps,
                    latitude = lat,
                    longitude = lon
                )
                if self.locChanged:
                    self.locChanged = False
                    break
                self._state.mapObjects = res['responses']['GET_MAP_OBJECTS']
                self.updateAllForts(self._state.mapObjects)
                self.updateAllPokemon(self._state.mapObjects)

    def _calculateMapObjectsTime(self, radius):
        return math.ceil(radius / location.DEFAULT_RADIUS) ** 2 + 3

    def _updateGMOTime(self, radius=None):
        newInterval = 0 if not radius else self._calculateMapObjectsTime(radius)
        oldInterval = self._calculateMapObjectsTime(self.radius)
        if not newInterval or newInterval != oldInterval:
            interval = oldInterval if not radius else newInterval
            self.mapObjThread.clear()
            self.threads.remove(self.mapObjThread)
            self.mapObjThread = set_interval(self.getMapObjects, interval)
            self.threads.append(self.mapObjThread)
            return True
        return False

    def getPastNotifications(self):
        orig = list(reversed(self.pastEvents))
        self.pastEvents = []
        return orig

    def filterUnspinnedStops(self, stops):
        now = datetime.utcnow()
        l = []
        for stop in stops:
            if stop['id'] not in self.pastStops:
                l.append(stop)
            else:
                d_t = datetime.utcfromtimestamp(self.pastStops[stop['id']] / 1000.0)
                if now > d_t:
                    l.append(stop)
        return l

    def getInventoryCapacity(self):
        bag = self.inventory.bag
        itemsCount = sum(map(lambda b: int(b), bag.values()))
        maxItems = self._state.player_data['max_item_storage']
        return [itemsCount, maxItems]

    def getPokemonCapacity(self):
        party = self.inventory.party
        stored = len(party)
        maxStorage = self._state.player_data['max_pokemon_storage']
        return [stored, maxStorage]

    def getCaughtPokemon(self):
        orig = self.caughtPokemon
        self.caughtPokemon = []
        return orig

    def setCaughtPokemon(self, poke, status, award=None):
        self.pokemon.pop(poke['encounter_id'], None)
        self.caughtPokemon.append(poke)
        hasAward = award is not None
        d = {
            'event': 'pokemonEvent',
            'status': status,
            'id': poke['pokemon_data']['pokemon_id'],
            'name': pokedex[poke['pokemon_data']['pokemon_id']],
            'cp': poke['pokemon_data'].get('cp', 0),
            'timestamp': getJSTime(),
            'hasAward': hasAward,
        }
        if hasAward:
            d.update({
                'award': {
                    'xp': sum(award['xp']),
                    'candy': sum(award['candy']),
                    'stardust': sum(award['stardust'])
                }
            })
            self.logger.info("Successfully caught pokemon.\n" +
                             "Received {0} exp, {1] candy, and {2} stardust.".format(
                                 d['award']['xp'], d['award']['candy'], d['award']['stardust']
                             ))
        self.pastEvents.append(d)

    def setPastStop(self, fort, res):
        if not res.get('experience_awarded'):  # Glitched response?
            return
        self.pastStops[fort['id']] = res['cooldown_complete_timestamp_ms']
        d = {
            'event': 'stopEvent',
            'timestamp': getJSTime(),
            'lure': bool(fort.get('lure_info')),
            'award': {
                'xp': res['experience_awarded']
            }
        }
        it = {}
        if res.get('pokemon_data_egg'):
            it['Pokemon Egg'] = 1
        for i in res.get('items_awarded', []):
            itemName = items[i['item_id']]
            it[itemName] = it.get(itemName, 0) + i['item_count']
        it['xp'] = res['experience_awarded']
        d['award'] = it
        self.logger.info("Successfully spinned stop.")
        self.pastEvents.append(d)

    def updateAllPokemon(self, cells):
        for cell in cells['map_cells']:
            for poke in cell.get('wild_pokemons', []):
                if poke['encounter_id'] not in self.pokemon:
                    self.pokemon[poke['encounter_id']] = poke
        self.cleanOldPokemon()

    def cleanOldPokemon(self):
        now = datetime.utcnow()
        for id, poke in list(self.pokemon.items()):
            # Don't deal with pokemon with bugged negative time_till_hidden
            if poke['time_till_hidden_ms'] > 0:
                d_t = datetime.utcfromtimestamp(
                    (poke['last_modified_timestamp_ms'] +
                     poke['time_till_hidden_ms']) / 1000.0)
                if now > d_t:
                    self.pokemon.pop(id)

    def updateAllForts(self, cells):
        for cell in cells['map_cells']:
            for fort in cell.get('forts', []):
                if fort['id'] not in self.forts:
                    stor = self.stops if fort.get('type') == 1 else self.gyms
                    stor[fort['id']] = fort
                    self.forts[fort['id']] = fort

    # Getters
    def getRPCId(self):
        global RPC_ID
        RPC_ID = RPC_ID + 1
        return RPC_ID

    def getEggs(self):
        return self._state.eggs

    def getInventory(self):
        return self.inventory

    def getBadges(self):
        return self._state.badges

    def getDownloadSettings(self):
        return self._state.settings

    def _execThread(self, func):
        t = threading.Thread(target=func)
        t.start()

    def _createThreads(self):
        self.radius = self.config.get("searchRadius")
        self.mapObjThread = set_interval(self.getMapObjects, self._calculateMapObjectsTime(self.radius))
        self.getProfThread = set_interval(self.getProfile, 3)
        self.threads.append(self.mapObjThread)
        self.threads.append(self.getProfThread)

    def run(self):
        self.threadBlock.set()
        self.getProfile()
        mainThread = threading.Thread(target=self._createThreads)
        mainThread.start()

    def unpause(self, locChanged=False):
        if locChanged:
            self.locChanged = True
        self.threadBlock.set()
        for thread in self.threads:
            thread.set()

    def pause(self):
        self.threadBlock.clear()
        for thread in self.threads:
            thread.clear()

    def clear(self):
        self.pokemon = {}
        self.forts = {}
        self.gyms = {}
        self.stops = {}

    def copyInto(self, getter):
        getter.pokemon = self.pokemon.copy()
        getter.forts = self.forts.copy()
        getter.gyms = self.gyms.copy()
        getter.stops = self.stops.copy()