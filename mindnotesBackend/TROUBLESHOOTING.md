# Troubleshooting Guide

## Common Issues and Solutions

### 1. UUID Conversion Error (FIXED)

**Error:**
```json
{
    "status": false,
    "message": "Failed to create journal entry",
    "exception_info": "ValidationError (JournalEntryMongo:None) (Could not convert to UUID: badly formed hexadecimal UUID string: ['user_id'])"
}
```

**Root Cause:**
Django's UUID field returns a Python UUID object, but MongoEngine's UUIDField expects explicit UUID type handling.

**Solution:** ✅ Fixed in [core/services.py](core/services.py:68-70)

```python
# Convert user.id to UUID explicitly
user_uuid = user.id if isinstance(user.id, uuid.UUID) else uuid.UUID(str(user.id))

entry = JournalEntryMongo(
    user_id=user_uuid,  # Now properly converted
    ...
)
```

**Testing:**
```bash
# Test the fixed endpoint
curl -X POST http://localhost:8000/api/v1/journals/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Entry",
    "content": "This is a test",
    "entry_type": "text"
  }'
```

---

### 2. Authentication Issues

**Error:**
```json
{
    "detail": "Authentication credentials were not provided."
}
```

**Solution:**
Ensure you include the JWT token in the Authorization header:

```bash
# Wrong
curl -X POST http://localhost:8000/api/v1/journals/create

# Correct
curl -X POST http://localhost:8000/api/v1/journals/create \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

**Get Token:**
```bash
# 1. Login
curl -X POST http://localhost:8000/api/v1/authentication/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"yourpassword"}'

# 2. Copy the "access" token from response
# 3. Use it in subsequent requests
```

---

### 3. Validation Errors

**Error:**
```json
{
    "status": false,
    "message": "Invalid journal entry data",
    "errors": {
        "content": ["Text entries must have content or prompt responses"]
    }
}
```

**Solution:**
Each entry type has specific requirements:

**Text Entries:**
```json
{
    "entry_type": "text",
    "content": "Required for text entries"
}
```

**Voice Entries:**
```json
{
    "entry_type": "voice",
    "voice_notes": [
        {
            "audio_url": "https://cdn.example.com/audio.mp3"
        }
    ]
}
```

**Photo Entries:**
```json
{
    "entry_type": "photo",
    "photos": [
        {
            "image_url": "https://cdn.example.com/photo.jpg"
        }
    ]
}
```

---

### 4. Tag Not Found

**Error:**
```json
{
    "status": false,
    "message": "Tag with this name already exists"
}
```

**Solution:**
Tags are user-specific. Use `tag_names` for auto-creation:

```json
{
    "title": "My Entry",
    "content": "Content here",
    "tag_names": ["gratitude", "mindfulness"]  // Auto-creates if not exist
}
```

Or get existing tag IDs first:
```bash
# Get user's tags
curl -X GET http://localhost:8000/api/v1/journals/tags \
  -H "Authorization: Bearer <token>"

# Use tag IDs
{
    "title": "My Entry",
    "content": "Content here",
    "tag_ids": [1, 2, 3]
}
```

---

### 5. MongoDB Connection Error

**Error:**
```
pymongo.errors.ServerSelectionTimeoutError: localhost:27017: [Errno 111] Connection refused
```

**Solution:**
Ensure MongoDB is running:

```bash
# Check MongoDB status
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Enable MongoDB on boot
sudo systemctl enable mongod
```

**Check connection in settings:**
```python
# mindnotesBackend/utils/mongo.py
from mongoengine import connect

connect(
    db='mindnotes',
    host='localhost',
    port=27017
)
```

---

### 6. Profile Does Not Exist

**Error:**
```
RelatedObjectDoesNotExist: User has no profile
```

**Solution:**
UserProfile should be created automatically via signals. Check:

1. **Verify signals are imported:**
```python
# authentication/apps.py
class AuthenticationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authentication'

    def ready(self):
        import authentication.signals  # Import signals
```

2. **Create profile manually if missing:**
```python
from authentication.models import User, UserProfile

user = User.objects.get(email='user@example.com')
profile = UserProfile.objects.create(user=user)
```

---

### 7. Cache Issues

**Symptom:**
Dashboard shows old data after creating entries

**Solution:**
Cache is automatically invalidated when creating entries. If issues persist:

```python
# Manual cache clear
from django.core.cache import cache

cache.clear()  # Clear all cache

# Or specific keys
cache.delete('dashboard_{user_id}')
cache.delete('profile_stats_{user_id}')
```

---

### 8. File Upload Issues

**Error:**
```json
{
    "errors": {
        "audio_url": ["Enter a valid URL."]
    }
}
```

**Solution:**
The API expects **URLs** not file uploads. Upload flow:

```
1. Frontend uploads file to CDN (S3, Cloudinary)
   ↓
2. CDN returns file URL
   ↓
3. Send URL to journal API
```

**Example:**
```javascript
// 1. Upload to CDN
const formData = new FormData();
formData.append('file', audioBlob);

const uploadResponse = await fetch('https://api.cloudinary.com/...', {
    method: 'POST',
    body: formData
});

const { secure_url } = await uploadResponse.json();

// 2. Create journal entry with URL
await fetch('/api/v1/journals/quick', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        entry_type: 'voice',
        audio_url: secure_url  // URL from CDN
    })
});
```

---

### 9. CORS Issues (Frontend)

**Error in Browser:**
```
Access to fetch at 'http://localhost:8000' has been blocked by CORS policy
```

**Solution:**
Install and configure django-cors-headers:

```bash
pip install django-cors-headers
```

```python
# settings.py
INSTALLED_APPS = [
    'corsheaders',
    ...
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    ...
]

# Development
CORS_ALLOW_ALL_ORIGINS = True

# Production
CORS_ALLOWED_ORIGINS = [
    "https://app.mindnotes.com",
    "https://mindnotes.com",
]
```

---

### 10. Empty Response Data

**Issue:**
```json
{
    "status": true,
    "message": "Entries retrieved successfully",
    "results": {
        "data": []
    }
}
```

**Solution:**
No entries exist yet. Create some:

```bash
# Create test entry
curl -X POST http://localhost:8000/api/v1/journals/create \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Entry",
    "content": "My first journal entry!",
    "entry_type": "text"
  }'
```

---

## Debugging Tips

### 1. Enable Debug Mode

```python
# settings.py
DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

### 2. Check Server Logs

```bash
# Run server with verbose output
python manage.py runserver

# Watch for errors in terminal
```

### 3. Test with Postman/Insomnia

Instead of curl, use GUI tools:
- Postman: https://www.postman.com/
- Insomnia: https://insomnia.rest/

Import this collection:
```json
{
    "name": "MindNotes API",
    "requests": [
        {
            "name": "Create Quick Journal",
            "method": "POST",
            "url": "{{base_url}}/journals/quick",
            "headers": {
                "Authorization": "Bearer {{token}}"
            },
            "body": {
                "entry_type": "text",
                "content": "Test entry"
            }
        }
    ]
}
```

### 4. Check Database Directly

**PostgreSQL:**
```bash
python manage.py dbshell

# Check users
SELECT id, email FROM users;

# Check tags
SELECT id, user_id, name FROM tags;
```

**MongoDB:**
```bash
mongo

use mindnotes

# Check collections
show collections

# Check entries
db.journal_entries.find().limit(5).pretty()

# Count user entries
db.journal_entries.countDocuments({user_id: UUID("...")})
```

---

## Getting Help

### 1. Check Documentation
- [JOURNAL_API_IMPLEMENTATION.md](JOURNAL_API_IMPLEMENTATION.md)
- [DASHBOARD_API_IMPLEMENTATION.md](DASHBOARD_API_IMPLEMENTATION.md)
- [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)

### 2. Test Script
Run the automated test script:
```bash
python test_journal_api.py
```

### 3. Common Checklist

Before reporting an issue, verify:
- [ ] Server is running (`python manage.py runserver`)
- [ ] MongoDB is running (`sudo systemctl status mongod`)
- [ ] You have a valid JWT token
- [ ] Token is included in Authorization header
- [ ] Request body is valid JSON
- [ ] Required fields are provided
- [ ] URLs (not files) are sent for media

---

## Quick Fixes

### Reset Everything
```bash
# 1. Stop server (Ctrl+C)

# 2. Reset database
python manage.py flush --no-input

# 3. Run migrations
python manage.py migrate

# 4. Create superuser
python manage.py createsuperuser

# 5. Start server
python manage.py runserver
```

### Clear Cache
```bash
python manage.py shell

>>> from django.core.cache import cache
>>> cache.clear()
>>> exit()
```

### Rebuild MongoDB Indexes
```bash
mongo

use mindnotes

db.journal_entries.createIndex({user_id: 1, entry_date: -1})
db.journal_entries.createIndex({user_id: 1, is_favorite: 1})
```

---

## Status Checks

### Health Check Script

```python
# check_health.py
import requests

BASE_URL = "http://localhost:8000"

print("=== System Health Check ===\n")

# 1. Server responding
try:
    response = requests.get(f"{BASE_URL}/admin/")
    print("✅ Server is running")
except:
    print("❌ Server is NOT running")

# 2. MongoDB
try:
    from mongoengine import connect
    connect('mindnotes', host='localhost', port=27017)
    print("✅ MongoDB is connected")
except:
    print("❌ MongoDB is NOT connected")

# 3. PostgreSQL
try:
    import psycopg2
    # Check connection
    print("✅ PostgreSQL is connected")
except:
    print("❌ PostgreSQL is NOT connected")

print("\n=== Health Check Complete ===")
```

Run it:
```bash
python check_health.py
```

---

**Last Updated:** 2025-10-08
**Version:** 1.0.0
