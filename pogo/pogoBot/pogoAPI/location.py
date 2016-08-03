import math

import geocoder
import gpxpy.geo
from geopy import Point, distance
from s2sphere import CellId, LatLng

from .custom_exceptions import GeneralPogoException


# Wrapper for location
class Location(object):
    def __init__(self, locationLookup, geo_key):
        self.geo_key = geo_key
        self.setLocation(locationLookup)

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

    def getFortDistance(self, fort):
        lat, lng ,alt = self.getCoordinates()
        return self.getDistance(lat, lng, fort.latitude, fort.longitude)

    def setLocation(self, search):
        providers = ['google', 'osm', 'arcgis', 'freegeoip']
        for p in providers:
            geo = getattr(geocoder, p)(search)
            if geo.lat is not None and geo.lng is not None:
                elev = geocoder.elevation(geo.latlng)
                self.latitude, self.longitude, self.altitude = geo.lat, geo.lng, elev.meters
                return self.latitude, self.longitude, self.altitude
        raise GeneralPogoException("Location could not be found")

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

    def getCells(self, lat=0, lon=0):
        if not lat: lat = self.latitude
        if not lon: lon = self.longitude
        return self.getNeighbors(lat, lon)

    def getAllSteps(self, radius=150):
        distPerStep = 150
        radius = max(radius, distPerStep)
        steps = math.ceil(radius/distPerStep)
        start = list(self.getCoordinates()[:2])
        lat, lon = start
        origin = Point(lat, lon)
        allSteps = [start]
        angleBetween = 60
        for s in range(1, steps + 1):
            for d in range(0, 360, int(angleBetween/min(s, 2))):
                destination = distance.VincentyDistance(meters=s*distPerStep).destination(origin, d)
                allSteps.append([destination.latitude, destination.longitude])
        return allSteps
