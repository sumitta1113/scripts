from pymongo import MongoClient
import pytz
import datetime

# connect MongoDB
client = MongoClient('mongodb://Jack-school-sys:AjG2ru7FqtZjack@61.91.202.5:27017/school_system?authMechanism=DEFAULT&authSource=admin')
db = client['school_system']
collection = db['time_crons']
doc = collection.find_one()

# เวลาใน MongoDB
for key, time_value in doc.items():
    if isinstance(time_value, datetime.datetime):
        print(f"{key}: {time_value} (tzinfo={time_value.tzinfo})")
