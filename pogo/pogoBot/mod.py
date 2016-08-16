class Handler():

    def __init__(self, session, logger, config):
        self.session = session
        self.logger = logger
        self.config = config

    def setSession(self, session):
        self.session = session