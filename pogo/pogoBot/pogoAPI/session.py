# Load Generated Protobuf
from POGOProtos.Networking.Requests import Request_pb2
from POGOProtos.Networking.Requests import RequestType_pb2
from POGOProtos.Networking.Envelopes import ResponseEnvelope_pb2
from POGOProtos.Networking.Envelopes import RequestEnvelope_pb2
from POGOProtos.Networking.Requests.Messages import EncounterMessage_pb2
from POGOProtos.Networking.Requests.Messages import FortSearchMessage_pb2
from POGOProtos.Networking.Requests.Messages import FortDetailsMessage_pb2
from POGOProtos.Networking.Requests.Messages import CatchPokemonMessage_pb2
from POGOProtos.Networking.Requests.Messages import GetInventoryMessage_pb2
from POGOProtos.Networking.Requests.Messages import GetMapObjectsMessage_pb2
from POGOProtos.Networking.Requests.Messages import EvolvePokemonMessage_pb2
from POGOProtos.Networking.Requests.Messages import ReleasePokemonMessage_pb2
from POGOProtos.Networking.Requests.Messages import UseItemCaptureMessage_pb2
from POGOProtos.Networking.Requests.Messages import DownloadSettingsMessage_pb2
from POGOProtos.Networking.Requests.Messages import UseItemEggIncubatorMessage_pb2
from POGOProtos.Networking.Requests.Messages import RecycleInventoryItemMessage_pb2

# Load local
from custom_exceptions import GeneralPogoException
from inventory import Inventory, items
from location import Location
from state import State
from pokedex import pokedex, teams
from getter import Getter

import requests
import time
import threading
import types

# Hide errors (Yes this is terrible, but prettier)
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

API_URL = 'https://pgorelease.nianticlabs.com/plfe/rpc'

class PogoSession():

    lock = threading.Lock()

    def __init__(self, session, authProvider, accessToken, location, logger):
        self.session = session
        self.logger = logger
        self.authProvider = authProvider
        self.accessToken = accessToken
        self._state = State()
        self.location = location
        self.authTicket = None
        self.getter = Getter(self, location, self._state)
        self.endpoint = 'https://{0}{1}'.format(
            self.createApiEndpoint(),
            '/rpc'
        )
        # self.getter.getDefaults()
        # self.getter.getProfile()
        self.getter.run()
        self.lock = threading.Lock()

    def getReqSession(self):
        return self.session

    def wrapInRequest(self, payload, **kwargs):
        # If we haven't authenticated before
        info = None
        if not self.authTicket:
            info = RequestEnvelope_pb2.RequestEnvelope.AuthInfo(
                provider=self.authProvider,
                token=RequestEnvelope_pb2.RequestEnvelope.AuthInfo.JWT(
                    contents=self.accessToken,
                    unknown2=59
                )
            )
        # Build Envelope
        coords = self.getter.getCoordinates()
        latitude = kwargs.get('latitude', coords[0])
        longitude = kwargs.get('longitude', coords[1])
        altitude = coords[2]
        req = RequestEnvelope_pb2.RequestEnvelope(
            status_code=2,
            request_id=self.getter.getRPCId(),
            longitude=longitude,
            latitude=latitude,
            altitude=altitude,
            auth_ticket=self.authTicket,
            unknown12=989,
            auth_info=info
        )
        req.requests.extend(payload)

        return req

    def requestOrThrow(self, req, url=None):
        if url is None:
            url = self.endpoint

        # Send request
        rawResponse = self.session.post(url, data=req.SerializeToString())

        # Parse it out
        res = ResponseEnvelope_pb2.ResponseEnvelope()
        res.ParseFromString(rawResponse.content)

        # Update Auth ticket if it exists
        if res.auth_ticket.start:
            self.authTicket = res.auth_ticket

        return res

    def request(self, req, url=None):
        try:
            return self.requestOrThrow(req, url)
        except Exception as e:
            self.logger.error(e)
            raise GeneralPogoException('Probably server fires.')

    def wrapAndRequest(self, payload, **kwargs):
        res = self.request(self.wrapInRequest(payload, **kwargs))
        if res == []:
            self.logger.critical(res)
            self.logger.critical('Servers seem to be busy. Exiting.')
            raise Exception('No Valid Response.')

        return res

    def __str__(self):
        s = 'Access Token: {0}\nEndpoint: {1}\nLocation: {2}'.format(
            self.accessToken,
            self.endpoint,
            self.location
        )
        return s

    def createApiEndpoint(self):
        payload = []
        msg = Request_pb2.Request(
            request_type=RequestType_pb2.GET_PLAYER
        )
        payload.append(msg)
        req = self.wrapInRequest(payload)
        res = self.request(req, API_URL)
        if res is None:
            self.logger.critical('Servers seem to be busy. Exiting.')
            raise Exception('Could not connect to servers')

        return res.api_url

    # Parse the default responses
    def parseDefault(self, res):
        self.getter.parseDefault(res)

    def setCoordinates(self, latitude, longitude):
        self.location.setCoordinates(latitude, longitude)

    def cleanPokemon(self, pokemons = None):
        r = []
        if pokemons is None:
            pokemons = self.checkAllPokemon()
        for poke in pokemons:
            r.append({
                'encounter_id': poke.encounter_id,
                'pokemon_id': poke.pokemon_data.pokemon_id,
                'name': pokedex[poke.pokemon_data.pokemon_id],
                'latitude': poke.latitude,
                'longitude': poke.longitude,
                'time_remaining': poke.time_till_hidden_ms
            })
        return r

    def cleanStops(self):
        r = []
        stops = list(self.checkAllStops())
        plat, plon, alt = self.getter.getCoordinates()
        seenIds = {}
        for stop in stops:
            if self.location.getDistance(plat, plon, stop.latitude, stop.longitude) < 300:
                if stop.id not in seenIds:
                    seenIds[stop.id] = True
                    r.append({
                        'id': stop.id,
                        'latitude': stop.latitude,
                        'longitude': stop.longitude,
                        'lure': bool(stop.lure_info.encounter_id)
                    })
        return r

    def cleanPlayerInfo(self):
        data = self.checkPlayerData()
        stats = self.checkPlayerStats()
        stardust = 0
        for i in data.currencies:
            if i.name == 'STARDUST':
                stardust = i.amount
                break
        d = {
            'username': data.username,
            'team': teams[data.team],
            'level': stats.level,
            'xp': stats.experience,
            'maxXp': stats.next_level_xp,
            'stardust': stardust,
            'gender': 'Male' if data.avatar.gender == 0 else 'Female'
        }
        return d

    # Get encounter
    def encounterPokemon(self, pokemon):
        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.ENCOUNTER,
            request_message=EncounterMessage_pb2.EncounterMessage(
                encounter_id=pokemon.encounter_id,
                spawn_point_id=pokemon.spawn_point_id,
                player_latitude=self.location.latitude,
                player_longitude=self.location.longitude
            ).SerializeToString()
        )]

        # Send
        res = self.wrapAndRequest(payload)

        # Parse
        self._state.encounter.ParseFromString(res.returns[0])

        # Return everything
        return self._state.encounter

    # Upon Encounter, try and catch
    def catchPokemon(self, pokemon, pokeball=1):

        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.CATCH_POKEMON,
            request_message=CatchPokemonMessage_pb2.CatchPokemonMessage(
                encounter_id=pokemon.encounter_id,
                pokeball=pokeball,
                normalized_reticle_size=1.950,
                spawn_point_guid=pokemon.spawn_point_id,
                hit_pokemon=True,
                spin_modifier=0.850,
                normalized_hit_position=1.0
            ).SerializeToString()
        )]
        # Send
        res = self.wrapAndRequest(payload)
        # Parse
        self._state.catch.ParseFromString(res.returns[0])

        # Return everything
        return self._state.catch

    # Use a razz berry or the like
    def useItemCapture(self, item_id, pokemon):

        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.USE_ITEM_CAPTURE,
            request_message=UseItemCaptureMessage_pb2.UseItemCaptureMessage(
                item_id=item_id,
                encounter_id=pokemon.encounter_id
            ).SerializeToString()
        )]

        # Send
        res = self.wrapAndRequest(payload)

        # Parse
        self._state.itemCapture.ParseFromString(res.returns[0])

        # Return everything
        return self._state.itemCapture

    # Evolve Pokemon
    def evolvePokemon(self, pokemon):

        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.EVOLVE_POKEMON,
            request_message=EvolvePokemonMessage_pb2.EvolvePokemonMessage(
                pokemon_id=pokemon.id
            ).SerializeToString()
        )]

        # Send
        res = self.wrapAndRequest(payload)

        # Parse
        self._state.evolve.ParseFromString(res.returns[0])

        # Return everything
        return self._state.evolve

    # Transfer Pokemon
    def releasePokemon(self, pokemon):

        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.RELEASE_POKEMON,
            request_message=ReleasePokemonMessage_pb2.ReleasePokemonMessage(
                pokemon_id=pokemon.id
            ).SerializeToString()
        )]

        # Send
        res = self.wrapAndRequest(payload)

        # Parse
        self._state.release.ParseFromString(res.returns[0])

        # Return everything
        return self._state.release

    # Throw away items
    def recycleItem(self, item_id, count):

        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.RECYCLE_INVENTORY_ITEM,
            request_message=RecycleInventoryItemMessage_pb2.RecycleInventoryItemMessage(
                item_id=item_id,
                count=count
            ).SerializeToString()
        )]

        # Send
        res = self.wrapAndRequest(payload)

        # Parse
        self._state.recycle.ParseFromString(res.returns[0])

        # Return everything
        return self._state.recycle

    # set an Egg into an incubator
    def setEgg(self, item, pokemon):

        # Create request
        payload = [Request_pb2.Request(
            request_type=RequestType_pb2.USE_ITEM_EGG_INCUBATOR,
            request_message=UseItemEggIncubatorMessage_pb2.UseItemEggIncubatorMessage(
                item_id=item.id,
                pokemon_id=pokemon.id
            ).SerializeToString()
        )]

        # Send
        res = self.wrapAndRequest(payload)

        # Parse
        self._state.incubator.ParseFromString(res.returns[0])

        # Return everything
        return self._state.incubator

    def setCaughtPokemon(self, *args):
        self.getter.setCaughtPokemon(*args)

    def setPastStop(self, *args):
        self.getter.setPastStop(*args)

    # These act as more logical functions.
    # Might be better to break out seperately
    # Walk over to position in meters
    def walkTo(self, olatitude, olongitude, epsilon=10, step=25):
        # Calculate distance to position
        latitude, longitude, _ = self.getter.getCoordinates()
        dist = closest = Location.getDistance(
            latitude,
            longitude,
            olatitude,
            olongitude
        )

        # Run walk
        divisions = closest / step
        if (abs(divisions) < 1):
            divisions = 1
        dLat = (olatitude - latitude) / divisions
        dLon = (olongitude - longitude) / divisions

        self.logger.info("Walking %f meters. This will take %f seconds..." % (dist, dist / step))
        while dist > epsilon:
            self.logger.debug("%f m -> %f m away", closest - dist, closest)
            newLat = latitude + dLat
            if dLat > 0 and newLat > olatitude:
                latitude = olatitude
            elif dLat < 0 and newLat < olatitude:
                latitude = olatitude
            else:
                latitude = newLat
            newLon = longitude + dLon
            if dLon > 0 and newLon > olongitude:
                longitude = olongitude
            elif dLon < 0 and newLon < olongitude:
                longitude = olongitude
            else:
                longitude = newLon
            self.setCoordinates(
                latitude,
                longitude
            )
            time.sleep(1)
            dist = Location.getDistance(
                latitude,
                longitude,
                olatitude,
                olongitude
            )

    def pause(self):
        self.getter.pause()

    def checkPlayerStats(self):
        return self._state.playerStats

    def checkProfile(self):
        return self._state.profile

    def checkPlayerData(self):
        return self._state.player_data

    def checkAllPokemon(self):
        return self.getter.pokemon.values()

    def checkAllForts(self):
        return self.getter.forts.values()

    def checkAllStops(self):
        return self.getter.stops.values()

    # Check, so we don't have to start another request
    def checkEggs(self):
        return self._state.eggs

    def checkInventory(self):
        return self.getter.inventory

    def checkBadges(self):
        return self._state.badges

    def checkDownloadSettings(self):
        return self._state.settings