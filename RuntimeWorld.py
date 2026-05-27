from PlayerRuntime import PlayerRuntime


class RuntimeWorld:
    def __init__(self):
        self.grid = []
        self.assets = {}
        self.sprites = {}
        self.main_actor = None
        self.runtime_party_actors = []
        