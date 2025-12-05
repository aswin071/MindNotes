# Premium Focus Programs API Documentation

## Overview

This document provides comprehensive API documentation for the three premium Focus Programs:
1. **5-Minute Morning Charge** - Daily morning routine to energize and set intentions
2. **Brain Dump Reset** - Categorize and clear mental clutter
3. **Gratitude Pause** - Deep dive into gratitude practice

## Authentication

All endpoints require JWT authentication via the `Authorization` header:
```
Authorization: Bearer <access_token>
```

## Premium Access & Trial System

### Trial Period
- **Duration**: 7 days from first use
- **Automatic**: Trial starts when user first accesses any premium program
- **Tracking**: Usage counts tracked per program during trial
- **Expiration**: After 7 days, users must subscribe to continue

### Access Check Endpoint

#### GET `/api/v1/focus/premium/access/`

Check user's access to premium programs.

**Response**:
```json
{
  "status": true,
  "message": "Premium access status retrieved",
  "results": {
    "data": {
      "has_access": true,
      "access_type": "trial",  // "paid", "trial", or "expired"
      "trial_info": {
        "is_active": true,
        "trial_started_at": "2025-12-02T10:00:00Z",
        "trial_ends_at": "2025-12-09T10:00:00Z",
        "days_remaining": 5,
        "morning_charge_count": 3,
        "brain_dump_count": 2,
        "gratitude_pause_count": 1,
        "trial_expired": false,
        "converted_to_paid": false
      }
    }
  }
}
```

### Get User Stats

#### GET `/api/v1/focus/premium/stats/`

Get comprehensive statistics across all premium programs.

**Response**:
```json
{
  "status": true,
  "message": "Statistics retrieved successfully",
  "results": {
    "data": {
      "morning_charge": {
        "current_streak": 5,
        "longest_streak": 7,
        "total_sessions": 15,
        "last_activity": "2025-12-02"
      },
      "brain_dump": {
        "current_streak": 3,
        "longest_streak": 5,
        "total_sessions": 10,
        "last_activity": "2025-12-01"
      },
      "gratitude_pause": {
        "current_streak": 2,
        "longest_streak": 4,
        "total_sessions": 8,
        "last_activity": "2025-12-02"
      },
      "total_sessions": 33,
      "first_session_date": "2025-11-15",
      "badges": [
        {
          "name": "Pulse Starter",
          "program_type": "morning_charge",
          "description": "Completed your first Morning Charge",
          "earned_at": "2025-11-15T08:00:00Z"
        }
      ]
    }
  }
}
```

---

## 1. Morning Charge (5 Minutes)

### Flow
1. **Start Session** → 2. **Breathing (1 min)** → 3. **Gratitude (1 min)** → 4. **Affirmation (1 min)** → 5. **Clarity Prompt (1-2 min)** → 6. **Charge Close (30 sec)** → 7. **Complete**

### 1.1 Start Session

#### POST `/api/v1/focus/premium/morning-charge/start/`

Start a new Morning Charge session or get today's existing session.

**Request Body**:
```json
{
  "session_date": "2025-12-02"  // Optional, defaults to today
}
```

**Response**:
```json
{
  "status": true,
  "message": "Morning Charge session started",
  "results": {
    "data": {
      "id": "674d8a1b2c3e4f5g6h7i8j9k",
      "session_date": "2025-12-02",
      "breathing_completed": false,
      "gratitude_text": null,
      "affirmation_text": null,
      "clarity_prompt_answer": null,
      "charge_close_completed": false,
      "is_completed": false,
      "completed_at": null,
      "total_duration_seconds": 0,
      "current_streak": 0,
      "created_at": "2025-12-02T08:00:00Z"
    }
  }
}
```

### 1.2 Complete Breathing

#### POST `/api/v1/focus/premium/morning-charge/breathing/`

Complete the breathing step (1 minute guided breathing).

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "duration_seconds": 60
}
```

### 1.3 Save Gratitude

#### POST `/api/v1/focus/premium/morning-charge/gratitude/`

Save gratitude spark (text or voice note).

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "gratitude_text": "I'm grateful for my family's health",
  "voice_note_url": null  // Optional: URL if voice note uploaded
}
```

**Note**: Either `gratitude_text` or `voice_note_url` must be provided.

### 1.4 Save Affirmation

#### POST `/api/v1/focus/premium/morning-charge/affirmation/`

Save positive affirmation.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "affirmation_text": "I am focused, calm, and ready to grow today",
  "is_favorite": true  // Optional: mark as favorite for daily repetition
}
```

### 1.5 Save Clarity Prompt

#### POST `/api/v1/focus/premium/morning-charge/clarity/`

Save daily clarity prompt response.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "question": "What's the one thing that will make today great?",
  "answer": "Completing my project presentation"
}
```

### 1.6 Complete Charge Close

#### POST `/api/v1/focus/premium/morning-charge/close/`

Complete the charge close step (30 sec motivational moment).

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k"
}
```

### 1.7 Complete Session

#### POST `/api/v1/focus/premium/morning-charge/complete/`

Complete the entire Morning Charge session and update streaks.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "total_duration_seconds": 300
}
```

**Response**:
```json
{
  "status": true,
  "message": "Morning Charge completed! 5-day streak!",
  "results": {
    "data": {
      "id": "674d8a1b2c3e4f5g6h7i8j9k",
      "session_date": "2025-12-02",
      "breathing_completed": true,
      "gratitude_text": "I'm grateful for my family's health",
      "affirmation_text": "I am focused, calm, and ready to grow today",
      "clarity_prompt_answer": "Completing my project presentation",
      "charge_close_completed": true,
      "is_completed": true,
      "completed_at": "2025-12-02T08:05:30Z",
      "total_duration_seconds": 300,
      "current_streak": 5,
      "created_at": "2025-12-02T08:00:00Z"
    }
  }
}
```

### 1.8 Get Session History

#### GET `/api/v1/focus/premium/morning-charge/history/?limit=30`

Get user's recent Morning Charge sessions.

**Query Parameters**:
- `limit`: Number of sessions to retrieve (default: 30)

### 1.9 Get Today's Session

#### GET `/api/v1/focus/premium/morning-charge/today/`

Get today's session if it exists.

---

## 2. Brain Dump Reset (5 Minutes)

### Flow
1. **Start Session** → 2. **Settle In (1 min)** → 3. **Write Thoughts (2 min)** → 4. **Categorize Thoughts (1 min)** → 5. **Choose Focus Task (30 sec)** → 6. **Close & Breathe (30 sec)** → 7. **Complete**

### 2.1 Get Categories

#### GET `/api/v1/focus/premium/brain-dump/categories/`

Get all available Brain Dump categories for thought categorization.

**Response**:
```json
{
  "status": true,
  "message": "Categories retrieved successfully",
  "results": {
    "data": [
      {
        "id": 1,
        "name": "Actionable Task",
        "icon": "✅",
        "color": "#10B981",
        "description": "Something I can do or complete soon",
        "order": 1
      },
      {
        "id": 2,
        "name": "Thought / Reflection",
        "icon": "💭",
        "color": "#8B5CF6",
        "description": "A feeling, idea, or insight worth journaling on",
        "order": 2
      }
      // ... 8 more categories
    ]
  }
}
```

**All 10 Categories**:
1. ✅ Actionable Task
2. 💭 Thought / Reflection
3. ⚠️ Worry / Anxiety
4. 🗓 Reminder / To-Do Later
5. ❤️ Personal / Relationship
6. 💼 Work / Career
7. 💰 Finance / Money
8. 🧘‍♂️ Health / Mind / Body
9. 🎯 Goal / Dream
10. ❌ Let Go / Not Important

### 2.2 Start Session

#### POST `/api/v1/focus/premium/brain-dump/start/`

Start a new Brain Dump session.

**Request Body**:
```json
{
  "session_date": "2025-12-02"  // Optional
}
```

### 2.3 Complete Settle In

#### POST `/api/v1/focus/premium/brain-dump/settle-in/`

Complete the settle in breathing step (1 min).

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k"
}
```

### 2.4 Add Thoughts

#### POST `/api/v1/focus/premium/brain-dump/thoughts/`

Add thoughts to the brain dump.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "thoughts": [
    {
      "text": "Finish project presentation",
      "category_id": null,
      "category_name": null
    },
    {
      "text": "Call mom about weekend plans",
      "category_id": null,
      "category_name": null
    },
    {
      "text": "Worried about upcoming deadline",
      "category_id": null,
      "category_name": null
    }
  ]
}
```

### 2.5 Save Guided Responses (Optional)

#### POST `/api/v1/focus/premium/brain-dump/guided-responses/`

If user struggles to start, save guided question responses.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "response_1": "Work deadlines are taking most of my mental space",
  "response_2": "I keep postponing my exercise routine",
  "response_3": "I keep replaying yesterday's meeting in my head"
}
```

### 2.6 Categorize Thoughts

#### POST `/api/v1/focus/premium/brain-dump/categorize/`

Categorize each thought.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "categorized_thoughts": [
    {
      "index": 0,
      "category_id": 1,
      "category_name": "Actionable Task"
    },
    {
      "index": 1,
      "category_id": 5,
      "category_name": "Personal / Relationship"
    },
    {
      "index": 2,
      "category_id": 3,
      "category_name": "Worry / Anxiety"
    }
  ]
}
```

### 2.7 Choose Focus Task

#### POST `/api/v1/focus/premium/brain-dump/choose-task/`

Choose one actionable task to focus on today.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "task_text": "Finish project presentation",
  "task_category_id": 1
}
```

### 2.8 Complete Close & Breathe

#### POST `/api/v1/focus/premium/brain-dump/close-breathe/`

Complete the closing breathing step.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k"
}
```

### 2.9 Complete Session

#### POST `/api/v1/focus/premium/brain-dump/complete/`

Complete the entire Brain Dump session.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "total_duration_seconds": 300
}
```

**Response**:
```json
{
  "status": true,
  "message": "Brain Dump completed! You cleared 8 thoughts. 3-day streak!",
  "results": {
    "data": {
      "id": "674d8a1b2c3e4f5g6h7i8j9k",
      "session_date": "2025-12-02",
      "total_thoughts_count": 8,
      "category_distribution": {
        "1": 3,  // 3 actionable tasks
        "3": 2,  // 2 worries
        "5": 3   // 3 personal items
      },
      "chosen_task_text": "Finish project presentation",
      "is_completed": true,
      "current_streak": 3,
      "total_duration_seconds": 300
    }
  }
}
```

### 2.10 Get Session History

#### GET `/api/v1/focus/premium/brain-dump/history/?limit=30`

Get user's recent Brain Dump sessions.

### 2.11 Get Today's Session

#### GET `/api/v1/focus/premium/brain-dump/today/`

Get today's session if it exists.

---

## 3. Gratitude Pause (5 Minutes)

### Flow
1. **Start Session** → 2. **Arrive (30 sec)** → 3. **List Three Gratitudes (1.5 min)** → 4. **Deep Dive on One (2 min)** → 5. **Express It (30 sec)** → 6. **Anchor (30 sec)** → 7. **Complete**

### 3.1 Start Session

#### POST `/api/v1/focus/premium/gratitude-pause/start/`

Start a new Gratitude Pause session.

**Request Body**:
```json
{
  "session_date": "2025-12-02"  // Optional
}
```

### 3.2 Complete Arrive

#### POST `/api/v1/focus/premium/gratitude-pause/arrive/`

Complete the arrive breathing step (30 sec).

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k"
}
```

### 3.3 Save Three Gratitudes

#### POST `/api/v1/focus/premium/gratitude-pause/three-gratitudes/`

Save three things you're grateful for.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "gratitude_1": "A kind message from a friend",
  "gratitude_2": "Morning coffee in peace",
  "gratitude_3": "A quiet moment to myself"
}
```

### 3.4 Save Deep Dive

#### POST `/api/v1/focus/premium/gratitude-pause/deep-dive/`

Deep dive into one selected gratitude with 5 prompts.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "selected_index": 1,  // Which gratitude (1, 2, or 3)
  "precise": "The text message from Sarah checking on me this morning",
  "why_matters": "It reminded me that I have people who care, especially when I've been stressed",
  "who_made_possible": "Sarah, my friend who always remembers to reach out",
  "sensory_moment": "I felt warmth in my chest when I read it, smiled, and felt less alone",
  "gratitude_line": "I'm grateful for Sarah's thoughtfulness because it reminds me I'm not alone in tough times"
}
```

**Deep Dive Prompts**:
1. **precise**: "What exactly are you grateful for?"
2. **why_matters**: "How did this help your day, mood, or stress?"
3. **who_made_possible**: "Who or what made this possible?"
4. **sensory_moment**: "Close your eyes: what did you see/hear/feel?"
5. **gratitude_line**: "Complete: I'm grateful for ___ because ___"

### 3.5 Save Expression

#### POST `/api/v1/focus/premium/gratitude-pause/expression/`

Choose and save an expression action.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "action": "send_thank_you",  // Options: send_thank_you, leave_note, helpful_act, reminder_later, skipped
  "notes": "Will text Sarah to say thank you"
}
```

### 3.6 Complete Anchor

#### POST `/api/v1/focus/premium/gratitude-pause/anchor/`

Complete the anchor breathing step (30 sec).

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k"
}
```

### 3.7 Complete Session

#### POST `/api/v1/focus/premium/gratitude-pause/complete/`

Complete the entire Gratitude Pause session.

**Request Body**:
```json
{
  "session_id": "674d8a1b2c3e4f5g6h7i8j9k",
  "total_duration_seconds": 300
}
```

**Response**:
```json
{
  "status": true,
  "message": "Gratitude Pause completed! 7-day streak!",
  "results": {
    "data": {
      "id": "674d8a1b2c3e4f5g6h7i8j9k",
      "session_date": "2025-12-02",
      "gratitude_1": "A kind message from a friend",
      "selected_gratitude_text": "A kind message from a friend",
      "deep_dive_5_gratitude_line": "I'm grateful for Sarah's thoughtfulness because it reminds me I'm not alone",
      "expression_action": "send_thank_you",
      "is_completed": true,
      "current_streak": 7,
      "total_duration_seconds": 300
    }
  }
}
```

### 3.8 Get Session History

#### GET `/api/v1/focus/premium/gratitude-pause/history/?limit=30`

Get user's recent Gratitude Pause sessions.

### 3.9 Get Today's Session

#### GET `/api/v1/focus/premium/gratitude-pause/today/`

Get today's session if it exists.

---

## Streak System & Badges

### Streaks
- Tracked per program independently
- Updated automatically on session completion
- Current streak resets if more than 1 day gap
- Longest streak recorded for all time

### Badges

#### Morning Charge Badges
- **Pulse Starter**: First session
- **Steady Beat**: 7-day streak
- **Flow Charger**: 30-day streak
- **Morning Warrior**: 100-day streak

#### Brain Dump Badges
- **Mind Declutterer**: 3-day streak
- **Clear Thinker**: 7-day streak
- **Mental Organizer**: 30-day streak

#### Gratitude Pause Badges
- **Gratitude Beginner**: First session
- **Thankful Heart**: 7-day streak
- **Gratitude Master**: 30-day streak

---

## Error Responses

### 403 Forbidden - Access Denied
```json
{
  "status": false,
  "message": "Your trial has expired. Please subscribe to continue.",
  "errors": {
    "error": "Premium access required"
  }
}
```

### 404 Not Found - Session Not Found
```json
{
  "status": false,
  "message": "Session not found",
  "errors": {
    "error": "Session with given ID does not exist"
  }
}
```

### 400 Bad Request - Validation Error
```json
{
  "status": false,
  "message": "Invalid input",
  "errors": {
    "gratitude_text": ["This field is required."]
  }
}
```

---

## Implementation Notes

### Database Architecture
- **PostgreSQL**: Reference data (categories, trial tracking)
- **MongoDB**: Session data (time-series, flexible schema)
- **Service Layer**: Coordinates between both databases

### Security
- JWT authentication required for all endpoints
- User ownership verified on all operations
- Premium access checked before starting sessions

### Performance
- Categories cached for 1 hour
- Streak calculations optimized with MongoDB indexes
- Session lookups indexed by user_id and date

---

## Setup Instructions

### 1. Run Migrations
```bash
python manage.py migrate focus
```

### 2. Seed Reference Data
```bash
python manage.py seed_premium_programs
```

### 3. Create MongoDB Indexes
MongoDB indexes are created automatically via MongoEngine meta definitions.

### 4. Test Premium Access
```bash
curl -X GET http://localhost:8000/api/v1/focus/premium/access/ \
  -H "Authorization: Bearer <your_token>"
```

---

## Future Enhancements

1. **Affirmation Library**: Pre-built affirmations users can choose from
2. **Clarity Prompt Rotation**: Daily rotating prompts
3. **Export Features**: Export brain dump history as PDF/CSV
4. **Social Sharing**: Share gratitude quotes to social media
5. **Reminder Notifications**: Push notifications for daily practice
6. **Analytics Dashboard**: Visual insights into patterns and progress
7. **AI Insights**: Smart categorization suggestions for brain dump
8. **Voice Recording**: Direct voice note recording in-app for morning charge gratitude

---

## Support

For issues or questions, please create an issue in the GitHub repository or contact the development team.
