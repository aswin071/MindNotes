# Profile & Subscription API

This module provides the Profile API endpoints for the MindNotes application. The Profile API aggregates data from both PostgreSQL and MongoDB to provide comprehensive user statistics and information.

## Endpoints

### 1. Get Profile Data
**GET** `/api/v1/subscriptions/profile/`

Returns aggregated profile data for the authenticated user, matching the Profile screen wireframe requirements.

**Authentication:** Required

**Response:** 200 OK

```json
{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "alex@email.com",
    "full_name": "Alex Johnson",
    "avatar": "https://example.com/avatars/user123.jpg",
    "bio": "Daily journaler and mindfulness enthusiast",

    "total_entries": 42,
    "current_streak": 7,
    "longest_streak": 14,
    "total_focus_minutes": 1250,
    "days_using_app": 14,

    "is_pro": false,
    "subscription_plan": "Free Plan",
    "subscription_status": "active",
    "subscription_expires_at": null,

    "timezone": "UTC",
    "language": "en",
    "daily_reminder": true,
    "reminder_time": "20:00:00",
    "email_notifications": true,
    "push_notifications": true,

    "default_entry_privacy": "private",
    "default_focus_duration": 25,
    "mood_tracking_enabled": true,

    "is_verified": true,
    "onboarding_completed": true,
    "created_at": "2025-09-24T10:30:00Z",
    "last_login_at": "2025-10-08T09:41:00Z"
}
```

**Data Sources:**
- `email`, `full_name`, `avatar`, `bio` → PostgreSQL User table
- `total_entries` → MongoDB JournalEntryMongo collection (aggregated count)
- `current_streak` → Calculated from MongoDB journal entries (consecutive days)
- `longest_streak` → PostgreSQL UserProfile table
- `total_focus_minutes` → MongoDB FocusSessionMongo collection (aggregated sum)
- `days_using_app` → Calculated from user creation date
- `subscription_*` → PostgreSQL Subscription table
- Preferences → PostgreSQL User & UserProfile tables

**Caching:** Profile data is cached for 5 minutes to optimize performance.

---

### 2. Invalidate Profile Cache
**POST** `/api/v1/subscriptions/profile/invalidate-cache/`

Invalidate the profile cache after user updates their data.

**Authentication:** Required

**Response:** 200 OK

```json
{
    "message": "Profile cache invalidated successfully"
}
```

**Usage:** Call this endpoint after updating user profile, preferences, or when new journal entries are created to ensure fresh data on next profile fetch.

---

### 3. Get Subscription Details
**GET** `/api/v1/subscriptions/subscriptions/me/`

Returns detailed subscription information for the authenticated user.

**Authentication:** Required

**Response:** 200 OK

```json
{
    "id": 1,
    "plan": "pro_monthly",
    "plan_display_name": "Pro Monthly",
    "status": "active",
    "is_pro": true,
    "started_at": "2025-09-01T00:00:00Z",
    "expires_at": "2025-10-01T00:00:00Z",
    "canceled_at": null,
    "trial_started_at": null,
    "trial_ends_at": null,
    "current_period_start": "2025-09-01T00:00:00Z",
    "current_period_end": "2025-10-01T00:00:00Z",
    "auto_renew": true,
    "days_until_expiry": 23,
    "created_at": "2025-09-01T00:00:00Z",
    "updated_at": "2025-09-01T00:00:00Z"
}
```

---

### 4. Get Payment History
**GET** `/api/v1/subscriptions/subscriptions/payments/`

Returns payment transaction history for the authenticated user.

**Authentication:** Required

**Response:** 200 OK

```json
[
    {
        "id": 1,
        "amount": "9.99",
        "currency": "USD",
        "status": "succeeded",
        "description": "Pro Monthly Subscription",
        "invoice_url": "https://invoice.stripe.com/i/123",
        "receipt_url": "https://receipt.stripe.com/r/456",
        "paid_at": "2025-09-01T00:00:00Z",
        "created_at": "2025-09-01T00:00:00Z"
    }
]
```

---

## Architecture

### Hybrid Database Design

The Profile API demonstrates the power of MindNotes' hybrid database architecture:

**PostgreSQL (Relational):**
- User authentication and profile data
- Subscription plans and payment records
- User preferences and settings
- Referential integrity for critical data

**MongoDB (NoSQL):**
- Journal entries (high write volume, flexible schema)
- Focus sessions (real-time updates, time-series data)
- Mood entries (flexible factors and context)
- Analytics and activity logs

### Service Layer

The `ProfileService` in `core/services.py` handles the complex data aggregation:

```python
ProfileService.get_profile_stats(user)
```

This service:
1. Queries PostgreSQL for user profile and subscription data
2. Aggregates statistics from MongoDB collections
3. Calculates streaks based on journal entry dates
4. Returns a unified data structure for the serializer

### Performance Optimization

1. **Caching:** Profile data cached for 5 minutes
2. **Selective Queries:** MongoDB queries use `.only()` for projection
3. **Indexing:** Compound indexes on `(user_id, -entry_date)` in MongoDB
4. **Lazy Loading:** Statistics calculated on-demand

---

## Models

### Subscription Model (PostgreSQL)

```python
class Subscription(Model):
    user = OneToOneField(User)
    plan = CharField(choices=['free', 'pro_monthly', 'pro_yearly'])
    status = CharField(choices=['active', 'canceled', 'expired', 'trial'])
    started_at = DateTimeField()
    expires_at = DateTimeField(null=True)
    # ... payment gateway fields
```

**Methods:**
- `is_pro()` - Check if user has active pro subscription
- `get_plan_display_name()` - Get user-friendly plan name
- `days_until_expiry()` - Calculate days until expiration

---

## Frontend Integration

### Example Usage (React Native / TypeScript)

```typescript
// Fetch profile data
const fetchProfile = async () => {
  const response = await fetch(
    'https://api.mindnotes.app/api/v1/subscriptions/profile/',
    {
      headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
      }
    }
  );

  const profileData = await response.json();
  return profileData;
};

// Invalidate cache after profile update
const invalidateProfileCache = async () => {
  await fetch(
    'https://api.mindnotes.app/api/v1/subscriptions/profile/invalidate-cache/',
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${accessToken}`,
      }
    }
  );
};
```

### Profile Screen Components

The API response maps directly to the Profile wireframe:

```typescript
interface ProfileData {
  // Header Section
  email: string;
  full_name: string;
  avatar: string | null;

  // Stats Section
  total_entries: number;      // "42 Entries"
  current_streak: number;     // "🔥 7 Streak"
  days_using_app: number;     // "14 Days"

  // Subscription Section
  is_pro: boolean;
  subscription_plan: string;  // "Free Plan"

  // ... other fields
}
```

---

## Future Enhancements

1. **Real-time Updates:** WebSocket support for live streak updates
2. **Achievements:** Gamification badges and milestones
3. **Social Features:** Public profiles and friend streaks
4. **Export Analytics:** Detailed usage reports
5. **Subscription Management:** Upgrade/downgrade flows via Stripe

---

## Testing

Run tests for the Profile API:

```bash
python manage.py test api.v1.subscriptions
```

---

## Notes for Senior Developers

### Scalability Considerations

1. **Database Sharding:** MongoDB collections are designed for horizontal sharding by `user_id`
2. **Read Replicas:** Heavy aggregation queries can be directed to read replicas
3. **CDN for Avatars:** User avatars should be served from CDN (S3 + CloudFront)
4. **Background Jobs:** Streak calculations can be moved to Celery tasks for large datasets

### Why This Architecture?

- **Separation of Concerns:** Transactional data in PostgreSQL, time-series in MongoDB
- **Query Optimization:** MongoDB excels at aggregations and flexible queries
- **Data Integrity:** PostgreSQL ensures ACID compliance for payments and subscriptions
- **Future-Proof:** Easy to scale individual components independently
