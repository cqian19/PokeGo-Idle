from pogoAPI.location import Location
from pokedex import pokedex, Rarity, baseEvolution
from pogoAPI.inventory import items
from pogoAPI.custom_exceptions import GeneralPogoException
from mod import Handler
import time

class pokemonHandler(Handler):

    # TODO: Improve pokemon choosing algorithm
    # Grab the nearest pokemon details
    def findBestPokemon(self):
        # Get Map details and print pokemon
        pokemons = self.session.checkAllPokemon()
        if pokemons == []: return
        self.logger.info("Finding Nearby Pokemon:")
        closest = float("Inf")
        best, pokemonBest = -1, None
        latitude, longitude, _ = self.session.getter.getCoordinates()
        self.logger.info("Current pos: %f, %f" % (latitude, longitude))
        seenIds = {}
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
            self.logger.info("%s, %f meters away" % (
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
            self.logger.info("Catching %s:" % pokedex[pokemon.pokemon_data.pokemon_id])
            self.session.walkTo(pokemon.latitude, pokemon.longitude)
            self.logger.info(self.encounterAndCatch(pokemon))

    # Wrap both for ease
    def encounterAndCatch(self, pokemon, thresholdP=0.5, limit=15, delay=2):
        # Start encounter
        print("Encounter start")
        self.logger.debug("Pausing threads to catch pokemon")
        self.session.getter.pause()
        self.session.getReqSession().restart()
        encounter = self.session.encounterPokemon(pokemon)
        # Grab needed data from proto
        chances = encounter.capture_probability.capture_probability
        if not len(chances):
            self.logger.error("Pokemon Inventory may be full")
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
                    self.logger.info("Using a RAZZ_BERRY")
                    self.session.useItemCapture(items.RAZZ_BERRY, pokemon)
                    berried = True
                    time.sleep(delay)
                    continue
                # if no alt ball, there are no balls
                elif altBall == items.UNKNOWN:
                    self.logger.error("No more pokeballs. Stopping pokemon capture.")
                    return;
                else:
                    bestBall = altBall

            # Try to catch it!!
            name = pokedex[pokemon.pokemon_data.pokemon_id]
            self.logger.info("Catch attempt {0} for {1}. {2}% chance to capture".format(count + 1, name, round(chances[bestBall-1]*100, 2)))
            self.logger.info("Using a {0}".format(items[bestBall]))
            attempt = self.session.catchPokemon(pokemon, bestBall)
            time.sleep(delay)

            # Success
            if attempt.status == 1:
                self.logger.info("Caught {0} in {1} attempt(s)!".format(name, count + 1))
                self.session.getter.unpause()
                self.session.setCaughtPokemon(encounter.wild_pokemon, "Caught", attempt.capture_award)
                return attempt

            # CATCH_FLEE is bad news
            if attempt.status == 3:
                self.logger.info("Pokemon has fled.")
                self.logger.info("Possible soft ban.")
                self.session.getter.unpause()
                self.session.setCaughtPokemon(encounter.wild_pokemon, "Fled")
                return attempt

            # Only try up to x attempts
            count += 1
            if count >= limit:
                self.logger.info("Over catch limit. Was unable to catch.")
                self.session.getter.unpause()
                self.session.setCaughtPokemon(encounter.wild_pokemon, "Failed")
                return None

    def cleanPokemon(self, thresholdCP=300):
        self.logger.info("Cleaning out Pokemon...")
        party = self.session.checkInventory().party
        stored = len(party)
        maxStorage = self.session.checkPlayerData().max_pokemon_storage
        self.logger.info("Pokemon storage capacity: {0}/{1}".format(stored, maxStorage))
        if stored/maxStorage < .8: return
        # evolables = [pokedex.PIDGEY, pokedex.RATTATA, pokedex.ZUBAT]
        candies = self.session.checkInventory().candies
        for pokemon in party:
            poke_id = pokemon.pokemon_id
            candy_id = baseEvolution[str(poke_id)]
            evoCandies = pokedex.evolves[poke_id]
            # Evolve all pokemon when possible
            if evoCandies and candies.get(candy_id, 0) >= evoCandies:
                self.logger.info("Evolving %s" % pokedex[pokemon.pokemon_id])
                self.logger.info(self.session.evolvePokemon(pokemon))
                candies[candy_id] -= evoCandies
                poke_id += 1
                time.sleep(.3)
            # If low cp, throw away
            r = pokedex.getRarityById(poke_id)
            if (pokemon.cp < thresholdCP and  r < Rarity.RARE) or r < Rarity.UNCOMMON:
                # Get rid of low CP, low evolve value
                self.logger.info("Releasing %s" % pokedex[pokemon.pokemon_id])
                self.session.releasePokemon(pokemon)
                candies[candy_id] += 1
                time.sleep(.3)
                stored -= 1
            if stored/maxStorage < .8:
                break;