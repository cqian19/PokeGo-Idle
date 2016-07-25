from pogoAPI.location import Location
from pokedex import pokedex
from pogoAPI.inventory import items
from pogoApi.custom_exceptions import GeneralPogoException
import logging
import time


class pokemonHandler():
    def __init__(self, session):
        self.session = session

    # Grab the nearest pokemon details
    def findBestPokemon(session):
        # Get Map details and print pokemon
        logging.info("Finding Nearby Pokemon:")
        cells = session.getMapObjects()
        closest = float("Inf")
        best = -1
        pokemonBest = None
        latitude, longitude, _ = session.getCoordinates()
        logging.info("Current pos: %f, %f" % (latitude, longitude))
        for cell in cells.map_cells:
            # Heap in pokemon protos where we have long + lat
            pokemons = [p for p in cell.wild_pokemons] + [p for p in cell.catchable_pokemons]
            for pokemon in pokemons:
                # Normalize the ID from different protos
                pokemonId = getattr(pokemon, "pokemon_id", None)
                if not pokemonId:
                    pokemonId = pokemon.pokemon_data.pokemon_id

                # Find distance to pokemon
                dist = Location.getDistance(
                    latitude,
                    longitude,
                    pokemon.latitude,
                    pokemon.longitude
                )

                # Log the pokemon found
                logging.info("%s, %f meters away" % (
                    pokedex[pokemonId],
                    dist
                ))

                rarity = pokedex.getRarityById(pokemonId)
                # Greedy for rarest
                if rarity > best:
                    pokemonBest = pokemon
                    best = rarity
                    closest = dist
                # Greedy for closest of same rarity
                elif rarity == best and dist < closest:
                    pokemonBest = pokemon
                    closest = dist
        return pokemonBest

    # Catch a pokemon at a given point
    def walkAndCatch(self, pokemon):
        if pokemon:
            logging.info("Catching %s:" % pokedex[pokemon.pokemon_data.pokemon_id])
            self.session.walkTo(pokemon.latitude, pokemon.longitude, step=3.2)
            logging.info(self.encounterAndCatch(pokemon))

    # Wrap both for ease
    def encounterAndCatch(self, pokemon, thresholdP=0.5, limit=5, delay=2):
        # Start encounter
        encounter = self.session.encounterPokemon(pokemon)

        # Grab needed data from proto
        chances = encounter.capture_probability.capture_probability
        balls = encounter.capture_probability.pokeball_type
        bag = self.session.checkInventory().bag

        # Have we used a razz berry yet?
        berried = False

        # Make sure we aren't oer limit
        count = 0

        # Attempt catch
        while True:
            bestBall = items.UNKNOWN
            altBall = items.UNKNOWN

            # Check for balls and see if we pass
            # wanted threshold
            for i in range(len(balls)):
                if balls[i] in bag:
                    altBall = balls[i]
                    if chances[i] > thresholdP:
                        bestBall = balls[i]
                        break

            # If we can't determine a ball, try a berry
            # or use a lower class ball
            if bestBall == items.UNKNOWN:
                if not berried and items.RAZZ_BERRY in bag and bag[items.RAZZ_BERRY]:
                    logging.info("Using a RAZZ_BERRY")
                    self.session.useItemCapture(items.RAZZ_BERRY, pokemon)
                    berried = True
                    time.sleep(delay)
                    continue

                # if no alt ball, there are no balls
                elif altBall == items.UNKNOWN:
                    raise GeneralPogoException("Out of usable balls")
                else:
                    bestBall = altBall

            # Try to catch it!!
            logging.info("Using a %s" % items[bestBall])
            attempt = self.session.catchPokemon(pokemon, bestBall)
            time.sleep(delay)

            # Success or run away
            if attempt.status == 1:
                return attempt

            # CATCH_FLEE is bad news
            if attempt.status == 3:
                logging.info("Possible soft ban.")
                return attempt

            # Only try up to x attempts
            count += 1
            if count >= limit:
                logging.info("Over catch limit")
                return None

    def cleanPokemon(self, thresholdCP=50):
        logging.info("Cleaning out Pokemon...")
        party = self.session.checkInventory().party
        evolables = [pokedex.PIDGEY, pokedex.RATTATA, pokedex.ZUBAT]
        toEvolve = {evolve: [] for evolve in evolables}
        for pokemon in party:
            # If low cp, throw away
            if pokemon.cp < thresholdCP:
                # It makes more sense to evolve some,
                # than throw away
                if pokemon.pokemon_id in evolables:
                    toEvolve[pokemon.pokemon_id].append(pokemon)
                    continue

                # Get rid of low CP, low evolve value
                logging.info("Releasing %s" % pokedex[pokemon.pokemon_id])
                self.session.releasePokemon(pokemon)

        # Evolve those we want
        for evolve in evolables:
            candies = self.session.checkInventory().candies[evolve]
            pokemons = toEvolve[evolve]
            # release for optimal candies
            while candies // pokedex.evolves[evolve] < len(pokemons):
                pokemon = pokemons.pop()
                logging.info("Releasing %s" % pokedex[pokemon.pokemon_id])
                self.session.releasePokemon(pokemon)
                time.sleep(1)
                candies += 1

            # evolve remainder
            for pokemon in pokemons:
                logging.info("Evolving %s" % pokedex[pokemon.pokemon_id])
                logging.info(self.session.evolvePokemon(pokemon))
                time.sleep(1)
                self.session.releasePokemon(pokemon)
                time.sleep(1)