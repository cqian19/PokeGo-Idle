from pogoAPI.location import Location
from pokedex import pokedex, Rarity
from pogoAPI.inventory import items
from pogoAPI.custom_exceptions import GeneralPogoException
from mod import Handler
import logging
import time

class pokemonHandler(Handler):

    # Grab the nearest pokemon details
    def findBestPokemon(self):
        # Get Map details and print pokemon
        logging.info("Finding Nearby Pokemon:")
        cellsList = self.session.checkMapObjects()
        closest = float("Inf")
        best = -1
        pokemonBest = None
        latitude, longitude, _ = self.session.getter.getCoordinates()
        logging.info("Current pos: %f, %f" % (latitude, longitude))
        seenIds = {}
        for cells in cellsList:
            for cell in cells.map_cells:
                # Heap in pokemon protos where we have long + lat
                pokemons = [p for p in cell.wild_pokemons] + [p for p in cell.catchable_pokemons]
                for pokemon in pokemons:
                    if pokemon.encounter_id in seenIds: continue
                    seenIds[pokemon.encounter_id] = True
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
            self.session.walkTo(pokemon.latitude, pokemon.longitude)
            logging.info(self.encounterAndCatch(pokemon))

    # Wrap both for ease
    def encounterAndCatch(self, pokemon, thresholdP=0.5, limit=5, delay=2):
        # Start encounter
        encounter = self.session.encounterPokemon(pokemon)
        # Grab needed data from proto
        chances = encounter.capture_probability.capture_probability
        if not len(chances):
            logging.error("Pokemon Inventory may be full")
            return

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
            for i in range(len(chances)):
                j = i + 1
                if j in bag:
                    if not altBall:
                        altBall = j
                    if chances[i] > thresholdP:
                        bestBall = j
                        break

            # If we can't determine a ball, try a berry
            # or use a lower class ball
            if bestBall == items.UNKNOWN:
                if altBall != items.UNKNOWN and not berried and items.RAZZ_BERRY in bag and bag[items.RAZZ_BERRY]:
                    logging.info("Using a RAZZ_BERRY")
                    self.session.useItemCapture(items.RAZZ_BERRY, pokemon)
                    berried = True
                    time.sleep(delay)
                    continue
                # if no alt ball, there are no balls
                elif altBall == items.UNKNOWN:
                    logging.error("No more pokeballs. Stopping pokemon capture.")
                    return;
                else:
                    bestBall = altBall

            # Try to catch it!!
            name = pokedex[pokemon.pokemon_data.pokemon_id]
            logging.info("Catch attempt {0} for {1}. {2}% chance to capture".format(count + 1, name, round(chances[bestBall-1]*100, 2)))
            logging.info("Using a {0}".format(items[bestBall]))
            attempt = self.session.catchPokemon(pokemon, bestBall)
            time.sleep(delay)

            # Success or run away
            if attempt.status == 1:
                logging.info("Caught {0} in {1} attempt(s)!".format(name, count + 1))
                return attempt

            # CATCH_FLEE is bad news
            if attempt.status == 3:
                logging.info("Possible soft ban.")
                return attempt

            # Only try up to x attempts
            count += 1
            if count >= limit:
                logging.info("Over catch limit. Was unable to catch.")
                return None

    def cleanPokemon(self, thresholdCP=250):
        logging.info("Cleaning out Pokemon...")
        party = self.session.checkInventory().party
        stored = len(party)
        maxStorage = self.session.checkPlayerData().max_pokemon_storage
        logging.info("Pokemon storage capacity: {0}/{1}".format(stored, maxStorage))
        if stored/maxStorage < .8: return
        if stored/maxStorage > .95: thresholdCP += 150
        # evolables = [pokedex.PIDGEY, pokedex.RATTATA, pokedex.ZUBAT]
        candies = self.session.checkInventory().candies
        for pokemon in party:
            id = pokemon.pokemon_id
            r = pokedex.getRarityById(id)
            evoCandies = pokedex.evolves[id]
            # Evolve all pokemon when possible
            if id in candies and pokemon.cp > thresholdCP and evoCandies and candies[id] >= evoCandies:
                logging.info("Evolving %s" % pokedex[pokemon.pokemon_id])
                logging.info(self.session.evolvePokemon(pokemon))
                time.sleep(.1)
            # If low cp, throw away
            if (pokemon.cp < thresholdCP and  r < Rarity.RARE) or r < Rarity.UNCOMMON:
                # Get rid of low CP, low evolve value
                logging.info("Releasing %s" % pokedex[pokemon.pokemon_id])
                self.session.releasePokemon(pokemon)
                time.sleep(.1)