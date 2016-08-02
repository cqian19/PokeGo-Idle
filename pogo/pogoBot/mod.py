class Handler():

    def __init__(self, session, logger):
        self.session = session
        self.logger = logger

    def setSession(self, session):
        self.session = session