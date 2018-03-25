from flask import Flask
from flask_ask import Ask, statement
from tinydb import Query
from DBHandler import DBHandler as TinyDB
from config import LTM_DATA_TABLE, DB_PATH, LAST_TIME_MOVED

app = Flask(__name__)
ask = Ask(app, '/')
db = TinyDB(DB_PATH, default_table=LTM_DATA_TABLE)
ltm = Query()

@ask.intent('LastTimeMovedIntent')
def ltm_check():
    if db.search(ltm.last_time_moved.exists()):
        ltm_status = db.get(doc_id=1)

        return statement("The last time you moved was {}"
                         .format(ltm_status[LAST_TIME_MOVED]))
    else:
        return statement("I'm sorry. Walabot is offline. Please try again.")
