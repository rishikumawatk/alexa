from tinydb import TinyDB
from singleton import singleton

@singleton
class DBHandler(TinyDB):
    pass
