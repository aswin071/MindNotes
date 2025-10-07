from pymongo import MongoClient
from django.conf import settings
from functools import lru_cache


@lru_cache(maxsize=1)
def get_mongo_db():
    uri = settings.MONGODB_URI
    if not uri:
        raise RuntimeError('MONGODB_URI not configured')
    client = MongoClient(uri, appname='mindnotes')
    return client[settings.MONGODB_DB_NAME]


