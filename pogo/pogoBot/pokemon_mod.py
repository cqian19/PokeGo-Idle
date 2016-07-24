import logging
from pogoAPI.location import Location


class pokemonHandler():

    def __init__(self, session):
        self.session = session

    # Grab the nearest pokemon details
    def findClosestPokemon(self):
        # Get Map details and print pokemon
        logging.info("Printing Nearby Pokemon:")
        closest = float("Inf")
        pokemonBest = None
        latitude, longitude, _ = self.session.getCoordinates()
        pokemon = self.session.getAllPokemon()
        pokemonBest = min(pokemon,
                          key=lambda p:
                            Location.getDistance(
                                latitude,
                                longitude,
                                pokemon.latitude,
                                pokemon.longitude
                            )
                          )
        return pokemonBest


    # Catch a pokemon at a given point
    def walkAndCatch(self, pokemon):
        if pokemon:
            logging.info("Catching nearest pokemon:")
            self.session.walkTo(pokemon.latitude, pokemon.longitude)
            logging.info(self.session.encounterAndCatch(pokemon))