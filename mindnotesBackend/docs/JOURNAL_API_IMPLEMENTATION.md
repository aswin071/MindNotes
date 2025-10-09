# Journal Creation API Implementation

## Overview

This document details the Journal Creation API for the MindNotes journaling app. These APIs enable users to create journal entries from the Home screen quick actions (Voice, Speak, Photo) as well as full-featured journal entries with all metadata.

## Wireframe Analysis - Home Screen Quick Actions

From the Home Dashboard wireframe, three quick journal entry types are identified:

1. **Voice** 🎤 - Quick voice recording journal
2. **Speak** ✍️ - Speech-to-text journal (quick text entry)
3. **Photo** 📷 - Quick photo journal with optional caption

## API Endpoints

### 1. Quick Journal Entry (Home Screen Actions)

**POST** `/api/v1/journals/quick`

**Purpose:** Rapid journal creation from Home screen quick actions

**Authentication:** Required (JWT)

**Request Body:**

```json
{
  "entry_type": "voice",  // "voice", "text", or "photo"
  "content": "Optional transcription or caption",

  // For voice entries
  "audio_url": "https://cdn.example.com/audio/recording123.mp3",
  "audio_duration": 120,  // seconds

  // For photo entries
  "photo_url": "https://cdn.example.com/photos/image123.jpg",
  "photo_caption": "Beautiful sunset today"
}
```

**Response:** 201 Created

```json
{
  "status": true,
  "message": "Quick voice entry created successfully",
  "results": {
    "data": {
      "id": "507f1f77bcf86cd799439011",
      "entry_type": "voice",
      "content": "Today was amazing...",
      "entry_date": "2025-10-08T14:30:00Z",
      "word_count": 25,
      "created_at": "2025-10-08T14:30:15Z"
    }
  }
}
```

**Use Cases:**

- **Voice Button:** Upload audio to CDN → Call API with `audio_url`
- **Speak Button:** Convert speech-to-text → Call API with `content`
- **Photo Button:** Upload photo to CDN → Call API with `photo_url`

---

### 2. Full Journal Entry Creation

**POST** `/api/v1/journals/create`

**Purpose:** Create comprehensive journal entries with all features

**Authentication:** Required (JWT)

**Request Body:**

```json
{
  "title": "My Reflection on Today",
  "content": "Today I learned about gratitude and mindfulness...",
  "entry_type": "text",  // "text", "voice", "photo", "mixed"
  "privacy": "private",  // "private" or "public"
  "is_favorite": false,

  // Tags (optional - either IDs or names)
  "tag_ids": [1, 2, 3],  // Tag IDs from PostgreSQL
  "tag_names": ["gratitude", "mindfulness"],  // Auto-creates if not exist

  // Location (optional)
  "location_name": "Central Park, NYC",
  "latitude": 40.785091,
  "longitude": -73.968285,

  // Weather (optional)
  "weather": "Sunny",
  "temperature": 72.5,

  // Embedded content (optional)
  "photos": [
    {
      "image_url": "https://cdn.example.com/photos/sunset.jpg",
      "caption": "Beautiful sunset",
      "order": 0,
      "width": 1920,
      "height": 1080
    }
  ],
  "voice_notes": [
    {
      "audio_url": "https://cdn.example.com/audio/note1.mp3",
      "duration": 180,
      "transcription": "Transcribed text here",
      "is_transcribed": true
    }
  ],
  "prompt_responses": [
    {
      "prompt_id": 42,
      "question": "What are you grateful for?",
      "answer": "I'm grateful for my family and health"
    }
  ],

  // Backdating (optional)
  "entry_date": "2025-10-07T20:00:00Z"
}
```

**Response:** 201 Created

```json
{
  "status": true,
  "message": "Journal entry created successfully",
  "results": {
    "data": {
      "id": "507f1f77bcf86cd799439011",
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "My Reflection on Today",
      "content": "Today I learned about...",
      "entry_type": "text",
      "entry_date": "2025-10-07T20:00:00Z",
      "privacy": "private",
      "is_favorite": false,
      "is_archived": false,
      "tag_ids": [1, 2, 3],
      "tags": [
        {"id": 1, "name": "gratitude", "color": "#10B981"},
        {"id": 2, "name": "mindfulness", "color": "#3B82F6"}
      ],
      "location_name": "Central Park, NYC",
      "weather": "Sunny",
      "word_count": 152,
      "character_count": 892,
      "reading_time_minutes": 1,
      "photos_count": 1,
      "voice_notes_count": 1,
      "created_at": "2025-10-08T14:30:15Z"
    }
  }
}
```

---

### 3. List Journal Entries

**GET** `/api/v1/journals/list`

**Purpose:** Get paginated list of user's journal entries

**Authentication:** Required (JWT)

**Query Parameters:**

```
?page=1
&limit=20
&entry_type=text
&is_favorite=true
&tag_ids=1,2,3
&date_from=2025-10-01
&date_to=2025-10-08
```

**Response:** 200 OK

```json
{
  "status": true,
  "message": "Entries retrieved successfully",
  "results": {
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 42,
      "pages": 3,
      "has_next": true,
      "has_prev": false
    },
    "data": [
      {
        "id": "507f1f77bcf86cd799439011",
        "title": "My Reflection",
        "content": "Today I learned...",
        "entry_type": "text",
        "entry_date": "2025-10-08T14:30:00Z",
        "is_favorite": false,
        "tags": [
          {"id": 1, "name": "gratitude", "color": "#10B981"}
        ],
        "word_count": 152,
        "photos_count": 0,
        "created_at": "2025-10-08T14:30:15Z"
      }
    ]
  }
}
```

---

### 4. Create Tag

**POST** `/api/v1/journals/tags/create`

**Purpose:** Create a new tag for organizing entries

**Authentication:** Required (JWT)

**Request Body:**

```json
{
  "name": "gratitude",
  "color": "#10B981"  // Hex color (optional, defaults to #3B82F6)
}
```

**Response:** 201 Created

```json
{
  "status": true,
  "message": "Tag created successfully",
  "results": {
    "data": {
      "id": 1,
      "name": "gratitude",
      "color": "#10B981",
      "created_at": "2025-10-08T14:30:15Z",
      "updated_at": "2025-10-08T14:30:15Z"
    }
  }
}
```

---

### 5. List Tags

**GET** `/api/v1/journals/tags`

**Purpose:** Get all tags for authenticated user

**Authentication:** Required (JWT)

**Response:** 200 OK

```json
{
  "status": true,
  "message": "Tags retrieved successfully",
  "results": {
    "data": [
      {
        "id": 1,
        "name": "gratitude",
        "color": "#10B981",
        "created_at": "2025-10-08T14:30:15Z",
        "updated_at": "2025-10-08T14:30:15Z"
      },
      {
        "id": 2,
        "name": "mindfulness",
        "color": "#3B82F6",
        "created_at": "2025-10-08T14:30:15Z",
        "updated_at": "2025-10-08T14:30:15Z"
      }
    ]
  }
}
```

---

## Implementation Details

### Service Layer

The `JournalService` in [core/services.py](core/services.py:22-135) handles the business logic:

```python
JournalService.create_journal_entry(user, data)
```

**Responsibilities:**
1. Validate and process tag IDs/names
2. Create embedded documents (photos, voice notes, prompts)
3. Save to MongoDB JournalEntryMongo collection
4. Update user statistics in PostgreSQL (total_entries)
5. Calculate word count, character count, reading time
6. Return created entry

### Serializers

**[api/v1/journals/serializers.py](api/v1/journals/serializers.py)**

1. **QuickJournalSerializer** (Lines 185-241)
   - Simplified for quick entries
   - Validates based on entry_type
   - Requires appropriate URL field for each type

2. **JournalEntryCreateSerializer** (Lines 43-138)
   - Comprehensive validation for full entries
   - Supports all entry types and metadata
   - Handles tag creation via names

3. **TagSerializer** (Lines 6-11)
   - PostgreSQL tag CRUD operations

### Views

**[api/v1/journals/views.py](api/v1/journals/views.py)**

1. **QuickJournalCreateView** (Lines 107-200)
   - Simplified endpoint for quick actions
   - Auto-formats data based on type
   - Defaults to private privacy

2. **JournalCreateView** (Lines 18-104)
   - Full-featured entry creation
   - Supports all metadata fields
   - Tag resolution and attachment

3. **JournalListView** (Lines 294-386)
   - Paginated MongoDB queries
   - Multiple filter options
   - Content preview (200 chars)

### Cache Invalidation

After creating a journal entry, the following caches are cleared:

```python
cache.delete(f'dashboard_{user.id}')  # Updates entry count
cache.delete(f'profile_stats_{user.id}')  # Updates statistics
```

This ensures fresh data on next dashboard/profile fetch.

---

## User Flow Examples

### Quick Voice Journal

```typescript
// 1. Record audio
const audioBlob = await recordAudio();

// 2. Upload to CDN
const audioUrl = await uploadToCDN(audioBlob);

// 3. Create journal entry
const response = await fetch('/api/v1/journals/quick', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    entry_type: 'voice',
    audio_url: audioUrl,
    audio_duration: 120
  })
});

const result = await response.json();
// result.results.data.id contains the entry ID
```

### Quick Photo Journal

```typescript
// 1. Capture/select photo
const photoBlob = await capturePhoto();

// 2. Upload to CDN
const photoUrl = await uploadToCDN(photoBlob);

// 3. Create journal entry
const response = await fetch('/api/v1/journals/quick', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    entry_type: 'photo',
    photo_url: photoUrl,
    photo_caption: 'Beautiful sunset today'
  })
});
```

### Quick Text Journal (Speak)

```typescript
// 1. Convert speech to text
const text = await speechToText();

// 2. Create journal entry
const response = await fetch('/api/v1/journals/quick', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    entry_type: 'text',
    content: text
  })
});
```

### Full Journal Entry

```typescript
// Create comprehensive entry
const response = await fetch('/api/v1/journals/create', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My Reflection',
    content: 'Today was an amazing day...',
    entry_type: 'text',
    tag_names: ['gratitude', 'mindfulness'],
    is_favorite: true,
    location_name: 'Central Park',
    weather: 'Sunny',
    temperature: 72.5
  })
});
```

---

## Validation Rules

### Quick Journal

| Field | Required | Validation |
|-------|----------|------------|
| entry_type | Yes | Must be 'voice', 'text', or 'photo' |
| audio_url | Conditional | Required if type='voice' |
| photo_url | Conditional | Required if type='photo' |
| content | Conditional | Required if type='text' |

### Full Journal Entry

| Field | Required | Validation |
|-------|----------|------------|
| entry_type | No | Defaults to 'text' |
| content | Conditional | Required for text entries |
| photos | Conditional | Required for photo entries (min 1) |
| voice_notes | Conditional | Required for voice entries (min 1) |
| privacy | No | Defaults to 'private' |
| tag_names | No | Max 50 chars per tag name |

---

## Database Strategy

### PostgreSQL (Tags)
- User-specific tags with colors
- Fast lookups and relational integrity
- Unique constraint: (user, name)

### MongoDB (Entries)
- Flexible schema for different entry types
- Embedded documents for photos/voice
- Full-text search support
- Time-series optimized indexes

**Indexes:**
```javascript
{user_id: 1, -entry_date: 1}  // Compound index
{user_id: 1, is_favorite: 1}   // Favorites filter
{$text: {content: 1, title: 1}}  // Full-text search
```

---

## Error Handling

### Common Errors

**400 Bad Request - Missing Required Fields**
```json
{
  "status": false,
  "message": "Invalid quick journal data",
  "errors": {
    "audio_url": "Voice entries require audio_url"
  }
}
```

**400 Bad Request - Duplicate Tag**
```json
{
  "status": false,
  "message": "Duplicate tag name",
  "errors": {
    "name": "Tag with this name already exists"
  }
}
```

**500 Internal Server Error**
```json
{
  "status": false,
  "message": "Failed to create journal entry",
  "exception_info": "MongoError: Connection timeout"
}
```

---

## Performance Considerations

### File Upload Strategy

**DON'T:**
```
❌ Upload files directly to API
❌ Store files in MongoDB
❌ Base64 encode large files
```

**DO:**
```
✅ Upload to CDN (S3, Cloudinary) first
✅ Send only URLs to API
✅ Use presigned URLs for security
```

### Recommended Flow:

1. **Frontend:** Request presigned URL from backend
2. **Frontend:** Upload file directly to S3/CDN
3. **Frontend:** Get file URL from CDN
4. **Frontend:** Send URL to journal API
5. **Backend:** Store URL in MongoDB

### Optimization Tips

```python
# ✅ Efficient - Query only needed fields
entries = JournalEntryMongo.objects(user_id=user.id).only(
    'title', 'entry_date', 'entry_type'
)

# ❌ Inefficient - Loads entire documents
entries = JournalEntryMongo.objects(user_id=user.id)
```

---

## Security Considerations

### User Isolation

All endpoints enforce user-specific data:

```python
# ✅ Correct - User can only access their data
entries = JournalEntryMongo.objects(user_id=request.user.id)

# ❌ Incorrect - Would expose all users' data
entries = JournalEntryMongo.objects.all()
```

### File URL Validation

```python
# Validate CDN domain
allowed_cdn_domains = ['cdn.mindnotes.com', 's3.amazonaws.com']
url_domain = urlparse(audio_url).netloc
if url_domain not in allowed_cdn_domains:
    raise ValidationError('Invalid CDN domain')
```

---

## Testing

### Manual Testing

```bash
# 1. Quick voice entry
curl -X POST http://localhost:8000/api/v1/journals/quick \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "voice",
    "audio_url": "https://cdn.example.com/audio/test.mp3"
  }'

# 2. Quick text entry
curl -X POST http://localhost:8000/api/v1/journals/quick \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "entry_type": "text",
    "content": "Today was amazing!"
  }'

# 3. List entries
curl -X GET 'http://localhost:8000/api/v1/journals/list?page=1&limit=10' \
  -H "Authorization: Bearer <token>"
```

---

## Files Created/Modified

### New Files:
1. [api/v1/journals/serializers.py](api/v1/journals/serializers.py) - Journal and tag serializers (245 lines)
2. [api/v1/journals/views.py](api/v1/journals/views.py) - Journal CRUD views (387 lines)
3. [api/v1/journals/urls.py](api/v1/journals/urls.py) - URL routing (20 lines)
4. [JOURNAL_API_IMPLEMENTATION.md](JOURNAL_API_IMPLEMENTATION.md) - This documentation

### Modified Files:
1. [core/services.py](core/services.py) - JournalService already exists (lines 22-135)

---

## Next Steps

### 1. File Upload Service

Create a separate endpoint for getting presigned URLs:

```python
# POST /api/v1/uploads/presigned-url
{
  "file_type": "audio",  // "audio", "image"
  "content_type": "audio/mp3"
}

# Response:
{
  "upload_url": "https://s3.amazonaws.com/...",
  "file_url": "https://cdn.mindnotes.com/audio/abc123.mp3"
}
```

### 2. Transcription Service

Integrate speech-to-text for voice entries:

```python
# After voice entry creation, trigger async transcription
transcribe_audio.delay(entry_id, audio_url)
```

### 3. Search Functionality

```python
# GET /api/v1/journals/search?q=gratitude
# Full-text search in MongoDB
```

---

## Summary

✅ **Quick Journal API** - Fast entry creation from Home screen
✅ **Full Journal API** - Comprehensive entries with all metadata
✅ **Tag Management** - Create and list user tags
✅ **List & Filter** - Paginated entries with multiple filters
✅ **User Isolation** - All data is user-specific
✅ **Cache Invalidation** - Auto-updates dashboard statistics
✅ **Error Handling** - Consistent error responses
✅ **Custom Response Format** - Using helpers/common.py

**Production Ready:** ✅
**Scalable:** ✅
**User-Friendly:** ✅
**Well-Documented:** ✅
