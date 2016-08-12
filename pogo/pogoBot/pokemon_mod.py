import time

from .mod import Handler
from .pogoAPI.pokedex import pokedex, Rarity, baseEvolution
from .pogoAPI.inventory import items
from .pogoAPI.location import Location


class pokemonHandler(Handler):

    EVOLVABLES = [pokedex.ZUBAT, pokedex.PIDGEY, pokedex.WEEDLE, pokedex.CATERPIE, pokedex.SPEAROW]
    # TODO: Improve pokemon choosing algorithm
    # Grab the nearest pokemon details
    def findBestPokemon(self):
        # Get Map details and print pokemon
        pokemons = self.session.checkAllPokemon()
        if not pokemons: return
        self.logger.info("Finding Nearby Pokemon:")
        closest = float("Inf")
        best, pokemonBest = -1, None
        latitude, longitude, _ = self.session.getter.getCoordinates()
        self.logger.info("Current pos: %f, %f" % (latitude, longitude))
        seenIds = set()
        for pokemon in pokemons:
            if pokemon['encounter_id'] in seenIds: continue
            seenIds.add(pokemon['encounter_id'])
            # Normalize the ID from different protos
            pokemonId = pokemon['pokemon_data']['pokemon_id']

            # Find distance to pokemon
            dist = Location.getDistance(
                latitude,
                longitude,
                pokemon['latitude'],
                pokemon['longitude']
            )
            # Log the pokemon found
            self.logger.info("%s, %f meters away" % (
                pokedex[pokemonId],
                dist
            ))
            rarity = pokedex.getRarityById(pokemonId)
            # Greedy for rarest
            if rarity >= Rarity.VERY_RARE and rarity > best:
                pokemonBest = pokemon
                best = rarity
                closest = dist
            elif best != -1 and rarity == best and dist < closest:
                pokemonBest = pokemon
                closest = dist
            # Greedy for closest of low rarity
            elif best == -1 and dist < closest:
                pokemonBest = pokemon
                closest = dist
        return pokemonBest

    # Catch a pokemon at a given point
    def walkAndCatch(self, pokemon):
        if pokemon:
            self.logger.info("Catching %s:" % pokedex[pokemon['pokemon_data']['pokemon_id']])
            for i in self.session.walkTo(pokemon['latitude'], pokemon['longitude']):
                yield # Yield after every step for stops
            self.logger.info(self.encounterAndCatch(pokemon))

    # Wrap both for ease
    def encounterAndCatch(self, pokemon, thresholdP=0.35, limit=7, delay=1):
        print("Encounter start")
        self.logger.debug("Pausing threads to catch pokemon")
        self.session.getter.pause()
        time.sleep(1)
        self.session.getReqSession().pauseExec()
        encounter = self.session.encounterPokemon(pokemon)
        catchInfo = encounter.get('capture_probability')
        if not catchInfo:
            self.logger.error("Pokemon Inventory may be full")
            self.logger.error("Pokemon may also have disappeared")
            self.session.setCaughtPokemon(pokemon, "Failed")
            return
        balls, chances = catchInfo['pokeball_type'], catchInfo['capture_probability']
        bag = self.session.checkInventory().bag
        # Have we used a razz berry yet?
        berried = False
        # Attempt catch
        for count in range(limit):
            # If we can't determine a ball, try a berry
            # or use a lower class ball
            bestBall = items.UNKNOWN
            altBall = items.UNKNOWN
            # Check for balls and see if we pass
            # wanted threshold
            for ball, chance in zip(balls, chances):
                if bag.get(ball):
                    altBall = ball
                    if chance > thresholdP:
                        bestBall = ball
                        break
            if bestBall == items.UNKNOWN:
                if altBall != items.UNKNOWN and not berried and bag.get(items.RAZZ_BERRY):
                    self.logger.info("Using a RAZZ_BERRY")
                    self.session.useItemCapture(items.RAZZ_BERRY, pokemon)
                    berried = True
                    time.sleep(delay)
                    continue
                # if no alt ball, there are no balls
                elif altBall == items.UNKNOWN:
                    self.logger.error("No more pokeballs. Stopping pokemon capture.")
                    return
                else:
                    bestBall = altBall

            # Try to catch it!!
            name = pokedex[pokemon['pokemon_data']['pokemon_id']]
            self.logger.info("Catch attempt {0} for {1}. {2}% chance to capture".format(count + 1, name, round(chances[bestBall-1]*100, 2)))
            self.logger.info("Using a {0}".format(items[bestBall]))
            time.sleep(.3)
            attempt = self.session.catchPokemon(pokemon, bestBall)
            bag[bestBall] = int(bag[bestBall]) - 1
            status = attempt.get('status', 0)
            if status == 0:
                self.session.getter.unpause()
                self.session.getReqSession().restart()
                self.logger.error("Error catching {0}".format(name))
                return
            # Success
            elif status == 1:
                self.logger.info("Caught {0} in {1} attempt(s)!".format(name, count + 1))
                self.endEncounter(encounter, "Caught", attempt['capture_award'])
                return attempt
            elif status == 2:
                self.logger.info("{0} has escaped from the pokeball!".format(name))
            # CATCH_FLEE is bad news
            elif status == 3:
                self.logger.info("Pokemon has fled.")
                self.logger.info("Possible soft ban.")
                self.endEncounter(encounter, "Fled")
                return attempt
    # Only try up to x attempts
        self.logger.info("Over catch limit. Was unable to catch.")
        self.endEncounter(encounter, "Failed")
        return None

    def endEncounter(self, encounter, status, award=None):
        poke = encounter['wild_pokemon']
        self.session.getReqSession().restart()
        self.session.getter.unpause()
        self.session.setCaughtPokemon(poke, status, award)

    def calcIV(self, poke):
        at = poke.get('individual_attack', 0)
        de = poke.get('individual_defense', 0)
        sta = poke.get('individual_stamina', 0)
        return 100 * (at + de + sta)/45

    def cleanPokemon(self, thresholdCP=800, thresholdIV=90):
        self.logger.info("Cleaning out Pokemon...")
        party = self.session.checkInventory().party
        stored, maxStorage = self.session.getter.getPokemonCapacity()
        self.logger.info("Pokemon storage capacity: {0}/{1}".format(stored, maxStorage))
        if stored/maxStorage < .8: return
        candies = self.session.checkInventory().candies
        for pokemon in party:
            iv = self.calcIV(pokemon)
            poke_id = pokemon['pokemon_id']
            candy_id = baseEvolution[str(poke_id)]
            evoCandies = pokedex.evolves[poke_id]
            # Evolve pokemon when possible
            if poke_id in self.EVOLVABLES or\
                iv > thresholdIV and evoCandies and candies.get(candy_id, 0) >= evoCandies:
                self.logger.info("Evolving %s" % pokedex[poke_id])
                self.logger.info(self.session.evolvePokemon(pokemon))
                candies[candy_id] -= evoCandies
                poke_id += 1
                time.sleep(.5)
                continue
            # If low cp, throw away
            r = pokedex.getRarityById(poke_id)
            if iv < thresholdIV and pokemon['cp'] < thresholdCP and r <= Rarity.RARE or r <= Rarity.UNCOMMON:
                # Get rid of low CP, low evolve value
                self.logger.info("Releasing %s" % pokedex[poke_id])
                self.session.releasePokemon(pokemon)
                candies[candy_id] += 1
                time.sleep(.5)
                stored -= 1
            if stored/maxStorage < .8:
                break