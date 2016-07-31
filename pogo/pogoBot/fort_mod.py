from pogoAPI.location import Location
from mod import Handler
import time

class fortHandler(Handler):

    lastStops = {}
    close = 30 # Testing within spin distance
    # Basic solution to spinning all forts.
    # Since traveling salesman problem, not
    # true solution. But at least you get
    # those step in
    def sortCloseForts(self):
        # Sort nearest forts (pokestop)
        stops = self.session.checkUnspinnedStops()
        if stops == self.lastStops: return
        self.logger.info("Sorting Nearest Forts")
        latitude, longitude, _ = self.session.getter.getCoordinates()
        ordered_forts = []
        for fort in stops:
            dist = Location.getDistance(
                latitude,
                longitude,
                fort.latitude,
                fort.longitude
            )
            if dist <= self.close:
                ordered_forts.append({'distance': dist, 'fort': fort})

        ordered_forts = sorted(ordered_forts, key=lambda k: k['distance'])
        return [instance['fort'] for instance in ordered_forts]

    # Find the fort closest to user
    def findClosestFort(self):
        # Find nearest fort (pokestop)
        self.logger.info("Finding Nearest Fort:")
        return self.sortCloseForts()[0]

    def spinAll(self, forts):
        for f in forts:
            self.spin(f)

    def spin(self, fort):
        fortResponse = self.session.getter.getFortSearch(fort)
        print(fortResponse)
        if fortResponse.result == 1:
            self.session.setPastStop(fort, fortResponse)
        time.sleep(.5)

    # Walk to fort and spin
    def walkAndSpin(self, fort):
        # No fort, demo == over
        if fort:
            self.logger.info("Spinning a Fort:")
            # Walk over
            self.session.walkTo(fort.latitude, fort.longitude)
            # Give it a spin
            self.spin(fort)

    # Walk and spin everywhere
    def walkAndSpinMany(self, forts):
        for fort in forts:
            self.walkAndSpin(fort)