"""from pgoapi.pgoapi.protos.POGOProtos import Networking
from Networking.Responses_pb2 import CatchPokemonResponse_pb2
from Networking.Responses import CheckAwardedBadgesResponse_pb2
from Networking.Responses import DownloadSettingsResponse_pb2
from Networking.Responses import EncounterResponse_pb2
from Networking.Responses import EvolvePokemonResponse_pb2
from Networking.Responses import FortDetailsResponse_pb2
from Networking.Responses import FortSearchResponse_pb2
from Networking.Responses import GetHatchedEggsResponse_pb2
from Networking.Responses import GetInventoryResponse_pb2
from Networking.Responses import GetMapObjectsResponse_pb2
from Networking.Responses import GetPlayerResponse_pb2
from Networking.Responses import RecycleInventoryItemResponse_pb2
from Networking.Responses import ReleasePokemonResponse_pb2
from Networking.Responses import UseItemCaptureResponse_pb2
from Networking.Responses import UseItemEggIncubatorResponse_pb2"""


class State(object):
    def __init__(self):
        self.profile = None
        self.player_data = self.profile.player_data
        self.eggs = None
        self.inventory = None
        self.badges = None
        self.settings = None
        self.mapObjects =  None
        self.fortSearch = None
        self.fortDetails = None
        self.encounter = None
        self.catch = None
        self.itemCapture = None
        self.evolve = None
        self.release = None
        self.recycle = None
        self.incubator = None
        self.playerStats = None
