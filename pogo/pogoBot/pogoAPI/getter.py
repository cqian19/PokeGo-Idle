import logging
import random
import threading

from POGOProtos.Networking.Requests import RequestType_pb2
from POGOProtos.Networking.Requests import Request_pb2
from POGOProtos.Networking.Requests.Messages import DownloadSettingsMessage_pb2
from POGOProtos.Networking.Requests.Messages import FortDetailsMessage_pb2
from POGOProtos.Networking.Requests.Messages import FortSearchMessage_pb2
from POGOProtos.Networking.Requests.Messages import GetInventoryMessage_pb2
from POGOProtos.Networking.Requests.Messages import GetMapObjectsMessage_pb2
from custom_exceptions import GeneralPogoException
from inventory import Inventory
from util import set_interval

RPC_ID = int(random.random() * 10 ** 12)

class Getter():

    def __init__(self, session, location, state):
        self._state = state
        self.location = location
        self.session = session
        # Set up Inventory
        self.pokemon = []
        self.caughtPokemon = []
        self.forts = []
        self.stops = []
        self.lastCells = []
        self.inventory = []
        self.threads = []
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
            self._state.badges.ParseFromString(res.returns[3])
            self._state.settings.ParseFromString(res.returns[4])
        except Exception as e:
            logging.error(e)
            raise GeneralPogoException("Error parsing response. Malformed response")

        # Finally make inventory usable
        item = self._state.inventory.inventory_delta.inventory_items
        self.inventory = Inventory(item)


    def getCoordinates(self):
        return self.location.getCoordinates()

    # Core api calls
    # Get profile
    def getProfile(self):
        # Create profile request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.GET_PLAYER
        )]

        # Send
        res = self.session.wrapAndRequest(payload)

        # Parse
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
            pokemon, stops = [], []
            pokemonSeen, stopsSeen = {}, {}
            steps = self.location.getAllSteps(radius)
            for lat, lon in steps:
                objectCells = []
                # allSteps = self.location.getAllSteps(radius)
                cells = self.location.getCells(lat, lon)
                timestamps = [0, ] * len(cells)
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
                # Send
                res = self.session.wrapAndRequest(payload, latitude=lat, longitude=lon)
                # Parse
                self._state.mapObjects.ParseFromString(res.returns[0])
                self.updateAllStops(self._state.mapObjects, stops, stopsSeen)
                self.updateAllPokemon(self._state.mapObjects, pokemon, pokemonSeen)
            self.pokemon = pokemon
            self.stops = stops
            return objectCells

    def getCaughtPokemon(self):
        orig = self.caughtPokemon
        self.caughtPokemon = []
        return orig

    def updateAllPokemon(self, cells, curList, seenIds):
        print("Updating pokemon")
        for cell in cells.map_cells:
            for poke in cell.wild_pokemons:
                if poke.encounter_id not in seenIds:
                    curList.append(poke)
                    seenIds[poke.encounter_id] = True

    def updateAllStops(self, cells, curList, seenIds):
        print("Updating forts")
        for cell in cells.map_cells:
            for fort in cell.forts:
                if fort.type == 1 and fort.id not in seenIds:
                    curList.append(fort)
                    seenIds[fort.id] = True

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
        self.getMapObjects(200)
        mapObjThread = set_interval(self.getMapObjects, 20)
        getProfThread = set_interval(self.getProfile, 1)
        self.threads.append(mapObjThread)
        self.threads.append(getProfThread)

    def run(self):
        mainThread = threading.Thread(target=self._createThreads)
        mainThread.start()

    def pause(self):
        for thread in self.threads:
            thread.set()