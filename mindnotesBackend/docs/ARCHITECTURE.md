# MindNotes Architecture

## Project Structure Separation

### Django Apps (Business Logic Layer)
Located in `mindnotesBackend/`

**Purpose**: Core business logic, database models, and admin interfaces

```
app_name/
├── models.py           # PostgreSQL models (Django ORM)
├── mongo_models.py     # MongoDB models (MongoEngine)
├── admin.py            # Django admin configuration
├── apps.py             # App configuration
├── tests.py            # Unit tests
├── views.py            # Minimal views (if needed)
└── migrations/         # Database migrations
```

**Apps**:
- `authentication/` - User auth, profiles, devices
- `journals/` - Journal entries (PostgreSQL metadata)
- `prompts/` - Daily prompts
- `moods/` - Mood tracking
- `focus/` - Focus sessions (PostgreSQL programs)
- `subscriptions/` - Payment and plans
- `exports/` - Data export (PostgreSQL jobs)
- `analytics/` - Analytics models

### API Layer (Presentation Layer)
Located in `api/v1/`

**Purpose**: REST API endpoints, serialization, and request handling

```
api/v1/app_name/
├── views.py           # API ViewSets and views
├── serializers.py     # DRF serializers
└── urls.py            # API routing
```

**Structure**:
- `api/v1/authentication/` - Auth endpoints
- `api/v1/journals/` - Journal CRUD + MongoDB content
- `api/v1/prompts/` - Prompt endpoints
- `api/v1/moods/` - Mood tracking API
- `api/v1/focus/` - Focus session API + MongoDB real-time
- `api/v1/subscriptions/` - Subscription API
- `api/v1/exports/` - Export API + MongoDB content
- `api/v1/analytics/` - Analytics endpoints

### Shared Utilities
- `core/` - Middleware, permissions, exceptions, utils
- `helpers/` - Common helper functions
- `utils/` - Database utilities (mongo.py, model_abstracts.py)

## Database Strategy

### PostgreSQL (Primary)
- User accounts and authentication
- Relational data (programs, subscriptions)
- Metadata and references

### MongoDB (Secondary)
- Large unstructured content (journal entries, exports)
- Real-time data (focus sessions)
- Time-series data (mood logs)

## Key Principles

1. **Separation of Concerns**: Apps handle logic, API handles presentation
2. **DRY**: Serializers and API logic only in api/v1/
3. **Scalability**: Clear boundaries for microservices migration
4. **Maintainability**: Single responsibility per module
