from pymongo import MongoClient
from django.conf import settings
from functools import lru_cache
import mongoengine


@lru_cache(maxsize=1)
def get_mongo_db():
    """
    Get MongoDB database connection using pymongo
    For direct MongoDB operations when MongoEngine is not suitable
    """
    # Use MongoEngine's existing connection instead of creating new client
    from mongoengine.connection import get_db
    try:
        return get_db()
    except Exception:
        # Fallback to creating new connection
        uri = settings.MONGODB_URI
        if not uri:
            raise RuntimeError('MONGODB_URI not configured')
        client = MongoClient(uri, appname='mindnotes', retryWrites=True, w='majority')
        return client[settings.MONGODB_DB_NAME]


def get_mongo_collection(collection_name: str):
    """
    Get a specific MongoDB collection
    """
    db = get_mongo_db()
    return db[collection_name]


def ensure_mongo_indexes():
    """
    Ensure MongoDB indexes are created
    This should be called during application startup
    """
    try:
        # Import all MongoDB models to ensure they're registered
        from journals.mongo_models import JournalEntryMongo
        from moods.mongo_models import MoodEntryMongo
        from focus.mongo_models import FocusSessionMongo
        from prompts.mongo_models import DailyPromptSetMongo, PromptResponseMongo
        from analytics.mongo_models import UserAnalyticsMongo, DailyActivityLogMongo
        from exports.mongo_models import ExportRequestMongo

        # Create indexes for all models
        # Note: ensure_indexes() uses the existing MongoEngine connection
        JournalEntryMongo.ensure_indexes()
        MoodEntryMongo.ensure_indexes()
        FocusSessionMongo.ensure_indexes()
        DailyPromptSetMongo.ensure_indexes()
        PromptResponseMongo.ensure_indexes()
        UserAnalyticsMongo.ensure_indexes()
        DailyActivityLogMongo.ensure_indexes()
        ExportRequestMongo.ensure_indexes()

        print("✅ MongoDB indexes created successfully!")
    except Exception as e:
        print(f"⚠️  Warning: Could not create MongoDB indexes: {e}")
        print("   The application will continue, but database performance may be affected.")
        # Don't raise - allow app to continue even if index creation fails


def get_mongo_stats():
    """
    Get MongoDB database statistics
    """
    try:
        db = get_mongo_db()
        stats = db.command("dbStats")
        return {
            'collections': stats.get('collections', 0),
            'data_size': stats.get('dataSize', 0),
            'storage_size': stats.get('storageSize', 0),
            'indexes': stats.get('indexes', 0),
            'index_size': stats.get('indexSize', 0)
        }
    except Exception as e:
        return {'error': str(e)}



