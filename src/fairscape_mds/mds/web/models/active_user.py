class ActiveUser:
    def __init__(self, id: str = ""):
        self._id = id

    def get_id(self):
        return self._id

    def set_id(self, id):
        self._id = id