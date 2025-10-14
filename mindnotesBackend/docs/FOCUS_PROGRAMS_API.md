# Focus Programs API Documentation

## Overview

The Focus Programs feature is the main premium feature of MindNotes. It allows users to enroll in structured focus programs (14-day free, 30-day pro) with daily tasks, focus sessions, reflections, and progress tracking.

## Architecture

### Database Strategy

**PostgreSQL (Relational Data)**:
- `FocusProgram`: Program templates (14-day, 30-day)
- `ProgramDay`: Daily content and structure for each program
- `UserFocusProgram`: User enrollment and basic status tracking

**MongoDB (Dynamic Data)**:
- `FocusSessionMongo`: Real-time focus sessions with pause/resume
- `UserProgramDayMongo`: Daily progress with tasks and reflections
- `ProgramProgressMongo`: Aggregated progress and statistics

### Service Layer

`FocusService` in `core/services.py` handles all business logic:
- Program enrollment with subscription validation
- Daily progress tracking
- Focus session management
- Reflection handling
- Weekly reviews and analytics

### Permission System

- `IsPremiumUser`: Validates active Pro subscription for 30-day programs
- `IsAuthenticated`: All endpoints require authentication
- Enrollment validation ensures users can only access their own data

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/v1/focus/
```

### Authentication
All endpoints require JWT authentication:
```
Authorization: Bearer <access_token>
```

---

## Endpoints Reference

### 1. List Available Programs
**GET** `/programs/`

Returns all focus programs with user's enrollment status.

**Response:**
```json
[
  {
    "id": 1,
    "name": "14-Day Focus Challenge",
    "program_type": "14_day",
    "description": "Build consistent focus habits...",
    "duration_days": 14,
    "objectives": ["Develop daily focus routine", ...],
    "is_pro_only": false,
    "can_access": true,
    "icon": "🎯",
    "color": "#3B82F6",
    "cover_image_url": null,
    "is_enrolled": false,
    "enrollment_id": null,
    "enrollment_status": null,
    "current_day": null
  },
  {
    "id": 2,
    "name": "30-Day Focus Mastery",
    "program_type": "30_day",
    "description": "Transform your productivity...",
    "duration_days": 30,
    "objectives": ["Master deep work techniques", ...],
    "is_pro_only": true,
    "can_access": false,
    "icon": "🚀",
    "color": "#10B981",
    "cover_image_url": null,
    "is_enrolled": false,
    "enrollment_id": null,
    "enrollment_status": null,
    "current_day": null
  }
]
```

**Cache:** 10 minutes

---

### 2. Enroll in Program
**POST** `/programs/enroll/`

Enroll user in a focus program.

**Request Body:**
```json
{
  "program_id": 1
}
```

**Response (Success):**
```json
{
  "enrolled": true,
  "enrollment_id": 123,
  "program_name": "14-Day Focus Challenge",
  "total_days": 14
}
```

**Response (Already Enrolled):**
```json
{
  "enrolled": false,
  "message": "Already enrolled in this program",
  "enrollment_id": 123
}
```

**Errors:**
- `403 Forbidden`: Program requires Pro subscription
- `400 Bad Request`: Invalid program_id

---

### 3. Start Program
**POST** `/programs/start/`

Change program status from "not_started" to "in_progress".

**Request Body:**
```json
{
  "enrollment_id": 123
}
```

**Response:**
```json
{
  "started": true,
  "enrollment_id": 123,
  "current_day": 1
}
```

---

### 4. Get Program Details
**GET** `/programs/{enrollment_id}/`

Get detailed program information with progress and current day info.

**Response:**
```json
{
  "enrollment_id": 123,
  "program": {
    "id": 1,
    "name": "14-Day Focus Challenge",
    "description": "Build consistent focus habits...",
    "duration_days": 14,
    "objectives": [...]
  },
  "status": "in_progress",
  "current_day": 3,
  "started_at": "2025-10-14T10:00:00Z",
  "progress": {
    "days_completed": 2,
    "completion_percentage": 14.3,
    "total_focus_minutes": 75,
    "total_sessions": 3,
    "current_streak": 2,
    "longest_streak": 2,
    "achievements": []
  },
  "current_day_info": {
    "day_number": 3,
    "title": "Day 3: Finding Your Rhythm",
    "description": "Continue building your focus muscle...",
    "focus_duration": 25,
    "tasks": ["Complete morning planning", ...],
    "tips": ["Start with your most important task", ...],
    "reflection_prompts": ["What's the biggest win?", ...],
    "is_completed": false,
    "tasks_progress": {
      "completed": 1,
      "total": 3
    }
  }
}
```

---

### 5. Get Day Details
**GET** `/programs/{enrollment_id}/days/{day_number}/`

Get detailed information for a specific program day with user's progress.

**Response:**
```json
{
  "day_number": 3,
  "title": "Day 3: Finding Your Rhythm",
  "description": "Continue building your focus muscle...",
  "focus_duration": 25,
  "tips": ["Start with your most important task", ...],
  "reflection_prompts": ["What's the biggest win?", ...],
  "user_progress": {
    "is_completed": false,
    "started_at": "2025-10-14T10:00:00Z",
    "completed_at": null,
    "tasks": [
      {
        "text": "Complete morning planning (5 min)",
        "is_completed": true,
        "completed_at": "2025-10-14T10:30:00Z",
        "order": 0
      },
      {
        "text": "Focus session: 25 minutes",
        "is_completed": false,
        "completed_at": null,
        "order": 1
      }
    ],
    "tasks_completed": 1,
    "tasks_total": 3,
    "focus_minutes": 0,
    "target_focus_minutes": 25,
    "reflections": [],
    "difficulty_rating": null,
    "satisfaction_rating": null,
    "notes": ""
  }
}
```

---

### 6. Update Task Status
**POST** `/tasks/update/`

Mark a task as completed or incomplete.

**Request Body:**
```json
{
  "enrollment_id": 123,
  "day_number": 3,
  "task_index": 0,
  "is_completed": true
}
```

**Response:**
```json
{
  "success": true,
  "tasks_completed": 2,
  "tasks_total": 3
}
```

---

### 7. Start Focus Session
**POST** `/sessions/start/`

Start a new focus session for a program day.

**Request Body:**
```json
{
  "enrollment_id": 123,
  "day_number": 3,
  "duration_minutes": 25,
  "session_type": "program"
}
```

**Response:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "started_at": "2025-10-14T11:00:00Z",
  "planned_duration_seconds": 1500,
  "status": "active"
}
```

**Errors:**
- `400 Bad Request`: User already has an active session

---

### 8. Get Active Session
**GET** `/sessions/active/`

Get user's currently active focus session if any.

**Response (With Active Session):**
```json
{
  "active_session": {
    "session_id": "507f1f77bcf86cd799439011",
    "started_at": "2025-10-14T11:00:00Z",
    "planned_duration_seconds": 1500,
    "status": "active",
    "session_type": "program",
    "program_id": 1,
    "distraction_count": 0
  }
}
```

**Response (No Active Session):**
```json
{
  "active_session": null
}
```

---

### 9. Pause Session
**POST** `/sessions/pause/`

Pause an active focus session.

**Request Body:**
```json
{
  "session_id": "507f1f77bcf86cd799439011"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Session paused"
}
```

---

### 10. Resume Session
**POST** `/sessions/resume/`

Resume a paused session.

**Request Body:**
```json
{
  "session_id": "507f1f77bcf86cd799439011"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Session resumed"
}
```

---

### 11. Add Distraction
**POST** `/sessions/distraction/`

Log a distraction during a session.

**Request Body:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "distraction_note": "Phone notification"
}
```

**Response:**
```json
{
  "success": true,
  "distraction_count": 1
}
```

---

### 12. Complete Session
**POST** `/sessions/complete/`

Complete a focus session and update progress.

**Request Body:**
```json
{
  "session_id": "507f1f77bcf86cd799439011",
  "productivity_rating": 4,
  "notes": "Great session, felt very focused"
}
```

**Response:**
```json
{
  "completed": true,
  "session_id": "507f1f77bcf86cd799439011",
  "actual_duration_minutes": 25,
  "ended_at": "2025-10-14T11:25:00Z"
}
```

**Side Effects:**
- Updates `UserProgramDayMongo` with focus minutes
- Updates `ProgramProgressMongo` with total stats
- Checks if day is complete (tasks + focus + reflection)
- Auto-advances to next day if current day is complete
- Marks program as complete if all days finished

---

### 13. Add Reflection
**POST** `/reflections/add/`

Add a reflection response for a program day.

**Request Body:**
```json
{
  "enrollment_id": 123,
  "day_number": 3,
  "question": "What's the biggest win from today?",
  "answer": "I completed all my tasks without getting distracted!"
}
```

**Response:**
```json
{
  "success": true,
  "reflections_count": 1,
  "day_completed": false
}
```

---

### 14. Get Weekly Review
**GET** `/programs/{enrollment_id}/weekly-review/{week_number}/`

Get weekly review summary for a program.

**Example:** `/programs/123/weekly-review/1/`

**Response:**
```json
{
  "week_number": 1,
  "start_day": 1,
  "end_day": 7,
  "days_completed": 5,
  "total_days": 7,
  "completion_rate": 71.4,
  "total_focus_minutes": 175,
  "average_difficulty": 3.2,
  "average_satisfaction": 4.5,
  "current_streak": 5,
  "achievements_earned": [],
  "summary": ""
}
```

---

### 15. Get Program History
**GET** `/history/`

Get user's all program enrollments (past and present).

**Response:**
```json
[
  {
    "enrollment_id": 123,
    "program_name": "14-Day Focus Challenge",
    "program_type": "14_day",
    "status": "in_progress",
    "started_at": "2025-10-14T10:00:00Z",
    "completed_at": null,
    "current_day": 3,
    "total_days": 14,
    "completion_percentage": 14.3,
    "total_focus_minutes": 75,
    "current_streak": 2
  }
]
```

---

## User Flow Examples

### Complete Flow: Day 1 of 14-Day Program

1. **User sees available programs**
   ```
   GET /programs/
   ```

2. **User enrolls in 14-day program**
   ```
   POST /programs/enroll/
   {"program_id": 1}
   ```

3. **User starts the program**
   ```
   POST /programs/start/
   {"enrollment_id": 123}
   ```

4. **User views Day 1 details**
   ```
   GET /programs/123/days/1/
   ```

5. **User completes task 1**
   ```
   POST /tasks/update/
   {"enrollment_id": 123, "day_number": 1, "task_index": 0, "is_completed": true}
   ```

6. **User starts focus session**
   ```
   POST /sessions/start/
   {"enrollment_id": 123, "day_number": 1, "duration_minutes": 25}
   ```

7. **User logs distraction (optional)**
   ```
   POST /sessions/distraction/
   {"session_id": "abc123", "distraction_note": "Phone call"}
   ```

8. **User completes focus session**
   ```
   POST /sessions/complete/
   {"session_id": "abc123", "productivity_rating": 4}
   ```

9. **User adds reflection**
   ```
   POST /reflections/add/
   {
     "enrollment_id": 123,
     "day_number": 1,
     "question": "What's the biggest win?",
     "answer": "I stayed focused for 25 minutes!"
   }
   ```

10. **System auto-checks if day is complete**
    - If tasks + focus + reflection complete → Day marked as complete
    - User advances to Day 2

---

## Database Models Reference

### PostgreSQL Models

**FocusProgram**:
```python
- name: CharField
- program_type: CharField (14_day, 30_day, custom)
- description: TextField
- duration_days: IntegerField
- objectives: JSONField
- is_pro_only: BooleanField
- icon: CharField
- color: CharField
- cover_image: ImageField
```

**ProgramDay**:
```python
- program: ForeignKey(FocusProgram)
- day_number: IntegerField
- title: CharField
- description: TextField
- focus_duration: IntegerField (minutes)
- tasks: JSONField (list)
- tips: JSONField (list)
- reflection_prompts: JSONField (list)
```

**UserFocusProgram**:
```python
- user: ForeignKey(User)
- program: ForeignKey(FocusProgram)
- status: CharField (not_started, in_progress, paused, completed, abandoned)
- started_at: DateTimeField
- completed_at: DateTimeField
- current_day: IntegerField
- current_streak: IntegerField
- longest_streak: IntegerField
```

### MongoDB Models

**FocusSessionMongo**:
```python
- user_id: IntField
- session_type: StringField (pomodoro, custom, program)
- status: StringField (active, completed, paused, canceled)
- planned_duration_seconds: IntField
- actual_duration_seconds: IntField
- task_description: StringField
- program_id, program_day_id, user_program_id: IntField
- started_at, ended_at: DateTimeField
- pauses: ListField
- distractions: ListField
- productivity_rating: IntField
```

**UserProgramDayMongo**:
```python
- user_id, user_program_id, program_id, program_day_id: IntField
- day_number: IntField
- is_completed: BooleanField
- tasks: ListField(EmbeddedDocument)
- focus_sessions: ListField (session IDs)
- total_focus_minutes: IntField
- reflections: ListField(EmbeddedDocument)
- difficulty_rating, satisfaction_rating: IntField
```

**ProgramProgressMongo**:
```python
- user_id, user_program_id, program_id: IntField
- total_days, days_completed: IntField
- completion_percentage: FloatField
- total_focus_minutes, total_sessions: IntField
- current_streak, longest_streak: IntField
- weekly_summaries: ListField(DictField)
- achievements: ListField(DictField)
```

---

## Testing Commands

### 1. Run Migrations
```bash
cd mindnotesBackend
python manage.py makemigrations
python manage.py migrate
```

### 2. Seed Focus Programs
```bash
python manage.py seed_focus_programs
```

### 3. Create Test User with Pro Subscription
```bash
python manage.py shell
```
```python
from authentication.models import User
from subscriptions.models import Subscription
from django.utils import timezone
from datetime import timedelta

# Create user
user = User.objects.create_user(
    email='testuser@example.com',
    password='testpass123',
    first_name='Test',
    last_name='User'
)

# Create Pro subscription
Subscription.objects.create(
    user=user,
    plan='pro_monthly',
    status='active',
    started_at=timezone.now(),
    expires_at=timezone.now() + timedelta(days=30)
)
```

### 4. Get JWT Token
```bash
curl -X POST http://localhost:8000/api/v1/authentication/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"testuser@example.com","password":"testpass123"}'
```

### 5. Test API Endpoints
```bash
# List programs
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/focus/programs/

# Enroll in program
curl -X POST http://localhost:8000/api/v1/focus/programs/enroll/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"program_id":1}'

# Start program
curl -X POST http://localhost:8000/api/v1/focus/programs/start/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"enrollment_id":1}'

# Get program details
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/focus/programs/1/
```

---

## Performance Considerations

1. **Caching**: Program list cached for 10 minutes per user
2. **Indexes**: MongoDB models have compound indexes for efficient queries
3. **Pagination**: History endpoint may need pagination for users with many enrollments
4. **Real-time**: Consider WebSocket for live session timer updates (future enhancement)

---

## Future Enhancements

- [ ] WebSocket support for real-time session updates
- [ ] Social features (share progress, leaderboards)
- [ ] Custom program creation
- [ ] AI-powered insights and recommendations
- [ ] Integration with calendar apps
- [ ] Mobile push notifications for session reminders
- [ ] Gamification badges and achievements system
- [ ] Export focus statistics and reports

---

**Last Updated:** 2025-10-14  
**Version:** 1.0.0  
**Status:** Ready for Testing ✅


