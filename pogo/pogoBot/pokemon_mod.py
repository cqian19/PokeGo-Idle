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
        pokemons = self.session.getAllPokemon()
        for pokemon in pokemons:
                # Log the pokemon found
                logging.info("%i at %f,%f" % (
                    pokemon.pokemon_data.pokemon_id,
                    pokemon.latitude,
                    pokemon.longitude
                ))

                # Fins distance to pokemon
                dist = Location.getDistance(
                    latitude,
                    longitude,
                    pokemon.latitude,
                    pokemon.longitude
                )

                # Greedy for closest
                if dist < closest:
                    pokemonBest = pokemon
                    closest = dist
        return pokemonBest


    # Catch a pokemon at a given point
    def walkAndCatch(self, pokemon):
        if pokemon:
            logging.info("Catching nearest pokemon:")
            self.session.walkTo(pokemon.latitude, pokemon.longitude)
            logging.info(self.session.encounterAndCatch(pokemon))