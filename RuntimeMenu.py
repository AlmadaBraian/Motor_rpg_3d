class RuntimeMenu:

    def __init__(self):

        self._index = 0

        self.visible = False

        self.title = ""

        self.items = []

        self.index = 0

        self.x = 100
        self.y = 100

        self.w = 8

        self.on_select = None
        self.on_cancel = None

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):

        self._index = value