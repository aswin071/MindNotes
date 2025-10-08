# Hybrid Database Setup Guide

This guide explains how to set up and use the hybrid PostgreSQL + MongoDB architecture for MindNotes.

## Overview

The MindNotes application uses a hybrid database architecture:
- **PostgreSQL**: For relational data requiring ACID transactions (users, subscriptions, reference data)
- **MongoDB**: For document-oriented data with high write volume (journal entries, mood tracking, focus sessions)

## Architecture Benefits

### PostgreSQL (Relational Data)
- ✅ ACID transactions for payments and subscriptions
- ✅ Complex joins for user relationships
- ✅ Referential integrity with foreign keys
- ✅ Proven authentication and user management
- ✅ Financial reporting and aggregations

### MongoDB (Document Data)
- ✅ Schema flexibility for varying entry types
- ✅ High write volume for real-time focus tracking
- ✅ Nested documents for complex data structures
- ✅ Time-series data optimization
- ✅ Horizontal scaling for millions of entries
- ✅ Rich text search capabilities

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The following packages are required:
- `mongoengine==0.27.0` - ODM for MongoDB
- `pymongo==4.10.1` - MongoDB driver
- `djongo==1.3.6` - Django MongoDB connector

### 2. Environment Variables

Create a `.env` file with the following variables:

```env
# PostgreSQL Configuration
POSTGRES_DB=mindnotes
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# MongoDB Configuration
MONGODB_DB=mindnotes
MONGODB_HOST=localhost
MONGODB_PORT=27017
MONGODB_USER=
MONGODB_PASSWORD=
MONGODB_URI=mongodb://localhost:27017/mindnotes
```

### 3. Database Setup

#### PostgreSQL
```bash
# Create database
createdb mindnotes

# Run migrations
python manage.py migrate
```

#### MongoDB
```bash
# Start MongoDB (if using Docker)
docker run -d --name mongodb -p 27017:27017 mongo:7

# Or install MongoDB locally
# Follow MongoDB installation guide for your OS
```

### 4. Initialize MongoDB Indexes

```bash
python manage.py init_mongodb
```

This command will:
- Create all necessary indexes for optimal performance
- Verify MongoDB connection
- Show database statistics (with `--stats` flag)

## Data Flow Examples

### 1. Creating a Journal Entry

```python
from core.services import JournalService
from datetime import datetime

# Data flows: Client → PostgreSQL (validate user) → MongoDB (store entry)
journal_data = {
    'title': 'My Day',
    'content': 'Today was amazing!',
    'entry_type': 'text',
    'tag_ids': [1, 2],  # PostgreSQL Tag IDs
    'photos': [{'image_url': '/media/photo.jpg', 'caption': 'Sunset'}]
}

entry = JournalService.create_journal_entry(user, journal_data)
```

### 2. Real-time Focus Session Updates

```python
from core.services import FocusService

# High-frequency updates go directly to MongoDB
session = FocusService.create_focus_session(user, session_data)

# Real-time tick updates (every second)
for i in range(1500):  # 25 minutes
    FocusService.update_session_tick(session.id, user, i)
    time.sleep(1)
```

### 3. Subscription Check

```python
# Authorization always goes through PostgreSQL
user_subscription = user.subscription
if user_subscription.plan.entry_limit > user.profile.total_entries:
    # Allow journal entry creation
    pass
```

## MongoDB Collections

### Journal Entries (`journal_entries`)
- Stores actual entry content and metadata
- Embedded photos, voice notes, and prompt responses
- Full-text search indexes on content and title
- Compound indexes for user + date queries

### Mood Entries (`mood_entries`)
- Time-series mood tracking data
- Flexible factors structure
- Optimized for date range queries

### Focus Sessions (`focus_sessions`)
- Real-time session tracking
- Embedded pause data
- Optimized for active session queries

### Daily Prompt Sets (`daily_prompt_sets`)
- Temporary daily prompt collections
- Completion tracking
- Auto-cleanup after date passes

### User Analytics (`user_analytics`)
- Pre-aggregated dashboard data
- Updated via background tasks
- Fast dashboard loading

### Daily Activity Logs (`daily_activity_logs`)
- Calendar view aggregations
- Daily activity summaries
- Optimized for date range queries

## Service Layer Usage

### Journal Operations

```python
from core.services import JournalService

# Create entry
entry = JournalService.create_journal_entry(user, data)

# Search entries
results = JournalService.search_entries(user, "search query")

# Get filtered entries
entries = JournalService.get_user_entries(user, {
    'date_from': datetime(2024, 1, 1),
    'is_favorite': True
})
```

### Mood Operations

```python
from core.services import MoodService

# Create mood entry
mood = MoodService.create_mood_entry(user, {
    'category_id': 1,
    'intensity': 8,
    'factors': [{'name': 'Sleep', 'value': 'good'}]
})

# Get mood history
moods = MoodService.get_user_moods(user, {
    'date_from': week_ago
})
```

### Focus Operations

```python
from core.services import FocusService

# Create session
session = FocusService.create_focus_session(user, {
    'session_type': 'pomodoro',
    'planned_duration_seconds': 1500
})

# Real-time updates
FocusService.update_session_tick(session.id, user, duration)

# Complete session
FocusService.complete_session(session.id, user, {
    'productivity_rating': 4
})
```

## Performance Considerations

### Indexing Strategy
- **User ID**: Primary index for all collections
- **Date fields**: Time-series queries
- **Compound indexes**: User + date for common queries
- **Text indexes**: Full-text search on journal content

### Query Optimization
- Use `user_id` filter on all MongoDB queries
- Leverage compound indexes for complex queries
- Cache frequently accessed PostgreSQL data
- Use aggregation pipelines for analytics

### Scaling Considerations
- MongoDB sharding by user_id for horizontal scaling
- Read replicas for analytics queries
- Connection pooling for high concurrency
- Background tasks for data aggregation

## Monitoring and Maintenance

### Health Checks
```python
from utils.mongo import get_mongo_stats

# Check MongoDB health
stats = get_mongo_stats()
print(f"Collections: {stats['collections']}")
print(f"Data size: {stats['data_size']} bytes")
```

### Index Maintenance
```bash
# Rebuild indexes if needed
python manage.py init_mongodb
```

### Data Cleanup
- Daily prompt sets: Auto-cleanup after 30 days
- Export requests: Cleanup after 7 days
- Analytics: Keep aggregated data, archive raw data

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Check MongoDB is running
   - Verify connection string in settings
   - Check firewall/network access

2. **Index Creation Failed**
   - Ensure MongoDB has write permissions
   - Check disk space
   - Verify collection names don't conflict

3. **Performance Issues**
   - Check index usage with MongoDB profiler
   - Optimize query patterns
   - Consider connection pooling

### Debug Commands

```bash
# Check MongoDB connection
python manage.py init_mongodb --stats

# Django shell for testing
python manage.py shell
>>> from utils.mongo import get_mongo_db
>>> db = get_mongo_db()
>>> db.list_collection_names()
```

## Security Considerations

- Use MongoDB authentication in production
- Encrypt sensitive data at rest
- Implement proper access controls
- Regular security updates
- Monitor for unusual access patterns

## Backup Strategy

### PostgreSQL
- Regular pg_dump backups
- Point-in-time recovery
- Replication for high availability

### MongoDB
- Regular mongodump backups
- Oplog for point-in-time recovery
- Replica sets for high availability

## Migration Strategy

When migrating from single database:

1. **Phase 1**: Set up hybrid architecture alongside existing system
2. **Phase 2**: Migrate new data to appropriate database
3. **Phase 3**: Migrate historical data in batches
4. **Phase 4**: Update application code to use service layer
5. **Phase 5**: Decommission old database

## Example Usage

See `examples/hybrid_usage.py` for comprehensive examples of:
- Creating journal entries with embedded data
- Real-time focus session tracking
- Mood tracking with flexible factors
- Analytics data aggregation
- Export request processing

## Support

For issues or questions:
1. Check this documentation
2. Review example code
3. Check MongoDB and PostgreSQL logs
4. Use Django debug toolbar for query analysis
