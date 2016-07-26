from geopy.geocoders import GoogleV3
from s2sphere import CellId, LatLng
from custom_exceptions import GeneralPogoException
import gpxpy.geo

# Wrapper for location
class Location(object):
    def __init__(self, locationLookup, geo_key):
        self.geo_key = geo_key
        self.locator = GoogleV3()
        if geo_key:
            self.locator = GoogleV3(api_key=geo_key)

        self.latitude, self.longitude, self.altitude = self.setLocation(locationLookup)

    def __str__(self):
        s = 'Coordinates: {} {} {}'.format(
            self.latitude,
            self.longitude,
            self.altitude
        )
        return s

    @staticmethod
    def getDistance(*coords):
        return gpxpy.geo.haversine_distance(*coords)

    def setLocation(self, search):
        try:
            geo = self.locator.geocode(search)
        except:
            raise GeneralPogoException('Error in Geo Request')
        return geo.latitude, geo.longitude, geo.altitude

    def setCoordinates(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude

    def getCoordinates(self):
        return self.latitude, self.longitude, self.altitude

    def getNeighbors(self, lat, lng):
        origin = CellId.from_lat_lng(LatLng.from_degrees(lat, lng)).parent(15)
        neighbors = {origin.id()}

        edge_neighbors = origin.get_edge_neighbors()
        surrounding_neighbors = [
            edge_neighbors[0],  # North neighbor
            edge_neighbors[0].get_edge_neighbors()[1],  # North-east neighbor
            edge_neighbors[1],  # East neighbor
            edge_neighbors[2].get_edge_neighbors()[1],  # South-east neighbor
            edge_neighbors[2],  # South neighbor
            edge_neighbors[2].get_edge_neighbors()[3],  # South-west neighbor
            edge_neighbors[3],  # West neighbor
            edge_neighbors[0].get_edge_neighbors()[3],  # North-west neighbor
        ]

        for cell in surrounding_neighbors:
            neighbors.add(cell.id())
            for cell2 in cell.get_edge_neighbors():
                neighbors.add(cell2.id())

        return neighbors

    def getCells(self, radius=10, lat=0, lon=0):
        if not lat: lat = self.latitude
        if not lon: lon = self.longitude
        return self.getNeighbors(lat, lon)
