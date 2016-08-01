from POGOProtos.Networking.Requests import RequestType_pb2
from POGOProtos.Networking.Requests import Request_pb2
from POGOProtos.Networking.Requests.Messages import DownloadSettingsMessage_pb2
from POGOProtos.Networking.Requests.Messages import FortDetailsMessage_pb2
from POGOProtos.Networking.Requests.Messages import FortSearchMessage_pb2
from POGOProtos.Networking.Requests.Messages import GetInventoryMessage_pb2
from POGOProtos.Networking.Requests.Messages import GetMapObjectsMessage_pb2
from custom_exceptions import GeneralPogoException
from inventory import Inventory, items
from util import set_interval, getJSTime
from pokedex import pokedex
from datetime import datetime
import logging
import random
import threading
import time

RPC_ID = int(random.random() * 10 ** 12)
STOP_COOLDOWN = 305

class Getter():

    def __init__(self, session, location, state):
        self._state = state
        self.location = location
        self.session = session
        # Set up Inventory
        self.pokemon = {}
        self.caughtPokemon = []
        self.pastStops = {}
        self.pastEvents = []
        self.forts = {}
        self.gyms = {}
        self.stops = {}
        self.inventory = []
        self.threads = []
        self.threadBlock = threading.Event()
        self.lock = threading.Lock()

    @staticmethod
    def getDefaults():
        # Allocate for 4 default requests
        data = [None, ] * 4

        # Create Egg request
        data[0] = Request_pb2.Request(
            request_type=RequestType_pb2.GET_HATCHED_EGGS
        )

        # Create Inventory Request
        data[1] = Request_pb2.Request(
            request_type=RequestType_pb2.GET_INVENTORY,
            request_message=GetInventoryMessage_pb2.GetInventoryMessage(
                last_timestamp_ms=0
            ).SerializeToString()
        )

        # Create Badge request
        data[2] = Request_pb2.Request(
            request_type=RequestType_pb2.CHECK_AWARDED_BADGES
        )

        # Create Settings request
        data[3] = Request_pb2.Request(
            request_type=RequestType_pb2.DOWNLOAD_SETTINGS,
            request_message=DownloadSettingsMessage_pb2.DownloadSettingsMessage(
                hash="4a2e9bc330dae60e7b74fc85b98868ab4700802e"
            ).SerializeToString()
        )

        return data

    def parseDefault(self, res):
        try:
            self._state.eggs.ParseFromString(res.returns[1])
            self._state.inventory.ParseFromString(res.returns[2])
            self.parsePlayerStats(self._state.inventory)
            self._state.badges.ParseFromString(res.returns[3])
            self._state.settings.ParseFromString(res.returns[4])
        except Exception as e:
            logging.exception(e)

        # Finally make inventory usable
        item = self._state.inventory.inventory_delta.inventory_items
        self.inventory = Inventory(item)

    def parsePlayerStats(self, inventory):
        for i in inventory.inventory_delta.inventory_items:
            stats = i.inventory_item_data.player_stats
            level = stats.level
            if level:
                self._state.playerStats = stats
                break

    def getCoordinates(self):
        return self.location.getCoordinates()

    # Core api calls
    # Get profile
    def getProfile(self):
        # Create profile request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.GET_PLAYER
        )]
        payload += self.getDefaults()
        self.threadBlock.wait()
        # Send
        res = self.session.wrapAndRequest(payload)
        # Parse
        self.parseDefault(res)
        self._state.profile.ParseFromString(res.returns[0])
        self._state.player_data = self._state.profile.player_data
        # Return everything
        return self._state.profile


    def getFortSearch(self, fort):
        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.FORT_SEARCH,
            request_message=FortSearchMessage_pb2.FortSearchMessage(
                fort_id=fort.id,
                player_latitude=self.location.latitude,
                player_longitude=self.location.longitude,
                fort_latitude=fort.latitude,
                fort_longitude=fort.longitude
            ).SerializeToString()
        )]

        # Send
        res = self.session.wrapAndRequest(payload)

        # Parse
        self._state.fortSearch.ParseFromString(res.returns[0])

        # Return everything
        return self._state.fortSearch

    def getFortDetails(self, fort):
        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.FORT_DETAILS,
            request_message=FortDetailsMessage_pb2.FortDetailsMessage(
                fort_id=fort.id,
                latitude=fort.latitude,
                longitude=fort.longitude,
            ).SerializeToString()
        )]

        # Send
        res = self.session.wrapAndRequest(payload)

        # Parse
        self._state.fortDetails.ParseFromString(res.returns[0])

        # Return everything
        return self._state.fortDetails

    # Hooks for those bundled in default
    def getMapObjects(self, radius=600):
        with self.lock:
            steps = self.location.getAllSteps(radius)
            for lat, lon in steps:
                cells = self.location.getCells(lat, lon)
                timestamps = [0, ] * len(cells)
                time.sleep(1)
                # Create request
                payload = [Request_pb2.Request(
                    request_type=RequestType_pb2.GET_MAP_OBJECTS,
                    request_message=GetMapObjectsMessage_pb2.GetMapObjectsMessage(
                        cell_id=cells,
                        since_timestamp_ms=timestamps,
                        latitude=lat,
                        longitude=lon
                    ).SerializeToString()
                )]
                self.threadBlock.wait()
                # Send
                res = self.session.wrapAndRequest(payload, latitude=lat, longitude=lon)
                # Parse
                self._state.mapObjects.ParseFromString(res.returns[0])
                self.updateAllForts(self._state.mapObjects)
                self.updateAllPokemon(self._state.mapObjects)

    def getPastNotifications(self):
        orig = list(reversed(self.pastEvents))
        self.pastEvents = []
        return orig

    def setPastStop(self, fort, res):
        if not res.experience_awarded:  # Glitched response?
            return
        self.pastStops[fort.id] = time.time()
        d = {
            'event': 'stopEvent',
            'timestamp': getJSTime(),
            'lure': bool(fort.lure_info.encounter_id),
            'award': {
                'Xp': res.experience_awarded
            }
        }
        it = {}
        if res.pokemon_data_egg.id:
            it['Pokemon Egg'] = 1
        for i in res.items_awarded:
            itemName = items[i.item_id]
            it[itemName] = it.get(itemName, 0) + i.item_count
        it['Xp'] = res.experience_awarded
        d['award'] = it
        self.pastEvents.append(d)

    def filterUnspinnedStops(self, stops):
        now = time.time()
        l = []
        for stop in stops:
            if stop.id not in self.pastStops or now - self.pastStops[stop.id] > STOP_COOLDOWN:
                l.append(stop)
        return l

    def getCaughtPokemon(self):
        orig = self.caughtPokemon
        self.caughtPokemon = []
        return orig

    def setCaughtPokemon(self, poke, status, award=None):
        self.pokemon.pop(poke.encounter_id, None)
        self.caughtPokemon.append(poke)
        hasAward = award is not None
        d = {
            'event': 'pokemonEvent',
            'status': status,
            'id': poke.pokemon_data.pokemon_id,
            'name': pokedex[poke.pokemon_data.pokemon_id],
            'cp': poke.pokemon_data.cp,
            'timestamp': getJSTime(),
            'hasAward': hasAward,
        }
        if hasAward:
            xpSum = candySum = stardustSum = 0
            for i in award.xp:
                xpSum += i
            for i in award.candy:
                candySum += i
            for i in award.stardust:
                stardustSum += i
            d.update({
                'award': {
                    'xp': 0 if not hasAward else xpSum,
                    'candy': 0 if not hasAward else candySum,
                    'stardust': 0 if not hasAward else stardustSum
                }
            })
        self.pastEvents.append(d)

    def updateAllPokemon(self, cells):
        print("Updating pokemon")
        for cell in cells.map_cells:
            for poke in cell.wild_pokemons:
                if poke.encounter_id not in self.pokemon:
                    self.pokemon[poke.encounter_id] = poke
        self.cleanOldPokemon()

    def cleanOldPokemon(self):
        now = datetime.utcnow()
        for id, poke in list(self.pokemon.items()):
            # Don't deal with pokemon with bugged negative time_till_hidden
            if poke.time_till_hidden_ms > 0:
                d_t = datetime.utcfromtimestamp(
                    (poke.last_modified_timestamp_ms +
                     poke.time_till_hidden_ms) / 1000.0)
                if now > d_t:
                    self.pokemon.pop(id)

    def updateAllForts(self, cells):
        print("Updating forts")
        for cell in cells.map_cells:
            for fort in cell.forts:
                if fort.id not in self.forts:
                    stor = self.stops if fort.type == 1 else self.gyms
                    stor[fort.id] = fort
                    self.forts[fort.id] = fort

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
        print("Create thread")
        self.getMapObjects(200)
        mapObjThread = set_interval(self.getMapObjects, 50)
        getProfThread = set_interval(self.getProfile, 3)
        self.threads.append(mapObjThread)
        self.threads.append(getProfThread)

    def run(self):
        self.threadBlock.set()
        self.getProfile()
        mainThread = threading.Thread(target=self._createThreads)
        mainThread.start()

    def unpause(self):
        self.threadBlock.set()
        for thread in self.threads:
            thread.set()

    def pause(self):
        print("Pausing")
        self.threadBlock.clear()
        for thread in self.threads:
            thread.clear()
