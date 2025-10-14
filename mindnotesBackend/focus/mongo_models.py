from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime


class FocusSessionMongo(Document):
    """
    MongoDB model for focus sessions
    Real-time updates, time-series data
    """
    user_id = fields.IntField(required=True, index=True)

    # Session details
    session_type = fields.StringField(
        choices=['pomodoro', 'custom', 'program'],
        default='custom'
    )
    status = fields.StringField(
        choices=['active', 'completed', 'paused', 'canceled'],
        default='active'
    )

    # Durations (in seconds for precision)
    planned_duration_seconds = fields.IntField(required=True)
    actual_duration_seconds = fields.IntField(default=0)

    # Task
    task_description = fields.StringField()

    # Program association (PostgreSQL IDs)
    program_id = fields.IntField()
    program_day_id = fields.IntField()
    user_program_id = fields.IntField()  # Reference to UserFocusProgram

    # Real-time tracking
    started_at = fields.DateTimeField(required=True, index=True)
    ended_at = fields.DateTimeField()
    last_tick_at = fields.DateTimeField()  # For real-time updates

    # Pauses (embedded documents for efficiency)
    pauses = fields.ListField(fields.DictField())  # [{started: datetime, ended: datetime, duration: int}]
    total_pause_duration_seconds = fields.IntField(default=0)

    # Feedback
    productivity_rating = fields.IntField(min_value=1, max_value=5)
    notes = fields.StringField()

    # Distractions logged during session
    distractions = fields.ListField(fields.StringField())
    distraction_count = fields.IntField(default=0)

    # Tags for categorization
    tags = fields.ListField(fields.StringField())

    # Milestones (for gamification)
    milestones = fields.ListField(fields.DictField())

    is_active = fields.BooleanField(default=False, index=True)

    meta = {
        'collection': 'focus_sessions',
        'indexes': [
            'user_id',
            'started_at',
            'status',
            'program_id',
            ('user_id', '-started_at'),
            ('user_id', 'status'),
            ('user_id', 'program_id'),
        ],
        'ordering': ['-started_at'],
    }

    def add_pause(self):
        """Add a pause to the session"""
        pause = {
            'started_at': datetime.utcnow(),
            'ended_at': None,
            'duration_seconds': 0
        }
        self.pauses.append(pause)
        self.save()

    def resume_pause(self):
        """Resume from latest pause"""
        if self.pauses and self.pauses[-1]['ended_at'] is None:
            pause = self.pauses[-1]
            pause['ended_at'] = datetime.utcnow()
            pause['duration_seconds'] = int((pause['ended_at'] - pause['started_at']).total_seconds())
            self.total_pause_duration_seconds += pause['duration_seconds']
            self.save()

    def add_distraction(self, distraction_note: str):
        """Log a distraction during the session"""
        if not self.distractions:
            self.distractions = []
        self.distractions.append(distraction_note)
        self.distraction_count = len(self.distractions)
        self.save()

    def __str__(self):
        return f"{self.user_id} - {self.session_type} - {self.started_at.date()}"


class DailyTaskEmbed(EmbeddedDocument):
    """Embedded document for daily tasks within program days"""
    task_text = fields.StringField(required=True)
    is_completed = fields.BooleanField(default=False)
    completed_at = fields.DateTimeField()
    order = fields.IntField(default=0)


class ReflectionResponseEmbed(EmbeddedDocument):
    """Embedded document for reflection responses"""
    prompt_id = fields.IntField()  # Reference to ProgramDay reflection prompt
    question = fields.StringField(required=True)
    answer = fields.StringField()
    answered_at = fields.DateTimeField()


class UserProgramDayMongo(Document):
    """
    MongoDB model for user's daily program progress
    Stores user's completion status and progress for individual program days
    """
    user_id = fields.IntField(required=True, index=True)
    user_program_id = fields.IntField(required=True, index=True)  # Reference to UserFocusProgram in PostgreSQL
    program_id = fields.IntField(required=True, index=True)  # Reference to FocusProgram
    program_day_id = fields.IntField(required=True, index=True)  # Reference to ProgramDay
    day_number = fields.IntField(required=True)

    # Completion status
    is_completed = fields.BooleanField(default=False, index=True)
    completed_at = fields.DateTimeField()
    started_at = fields.DateTimeField()

    # Daily tasks (embedded)
    tasks = fields.ListField(fields.EmbeddedDocumentField(DailyTaskEmbed))
    tasks_completed_count = fields.IntField(default=0)
    tasks_total_count = fields.IntField(default=0)

    # Focus session tracking
    focus_sessions = fields.ListField(fields.StringField())  # List of FocusSessionMongo IDs
    total_focus_minutes = fields.IntField(default=0)
    target_focus_minutes = fields.IntField(default=0)  # From ProgramDay

    # Reflection responses (embedded)
    reflections = fields.ListField(fields.EmbeddedDocumentField(ReflectionResponseEmbed))
    reflections_completed = fields.BooleanField(default=False)

    # Notes
    notes = fields.StringField()

    # Rating
    difficulty_rating = fields.IntField(min_value=1, max_value=5)
    satisfaction_rating = fields.IntField(min_value=1, max_value=5)

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_program_days',
        'indexes': [
            'user_id',
            'user_program_id',
            'program_id',
            'day_number',
            'is_completed',
            ('user_id', 'program_id'),
            ('user_program_id', 'day_number'),
            ('user_id', 'user_program_id', 'day_number'),
        ],
        'ordering': ['day_number'],
    }

    def mark_task_completed(self, task_index: int):
        """Mark a specific task as completed"""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].is_completed = True
            self.tasks[task_index].completed_at = datetime.utcnow()
            self.tasks_completed_count = sum(1 for task in self.tasks if task.is_completed)
            self.updated_at = datetime.utcnow()
            self.save()

    def add_reflection_response(self, question: str, answer: str, prompt_id: int = None):
        """Add a reflection response"""
        reflection = ReflectionResponseEmbed(
            prompt_id=prompt_id,
            question=question,
            answer=answer,
            answered_at=datetime.utcnow()
        )
        self.reflections.append(reflection)
        self.updated_at = datetime.utcnow()
        self.save()

    def check_completion(self):
        """Check if day is fully completed (tasks + focus + reflection)"""
        tasks_done = self.tasks_completed_count == self.tasks_total_count if self.tasks_total_count > 0 else True
        focus_done = self.total_focus_minutes >= self.target_focus_minutes if self.target_focus_minutes > 0 else True
        reflections_done = len(self.reflections) > 0

        if tasks_done and focus_done and reflections_done and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self.save()
            return True
        return False

    def __str__(self):
        return f"User {self.user_id} - Program {self.program_id} - Day {self.day_number}"


class ProgramProgressMongo(Document):
    """
    MongoDB model for aggregated program progress
    Stores weekly summaries and overall program statistics
    """
    user_id = fields.IntField(required=True, index=True)
    user_program_id = fields.IntField(required=True, index=True, unique=True)
    program_id = fields.IntField(required=True, index=True)

    # Overall progress
    total_days = fields.IntField(required=True)
    days_completed = fields.IntField(default=0)
    completion_percentage = fields.FloatField(default=0.0)

    # Focus statistics
    total_focus_minutes = fields.IntField(default=0)
    total_sessions = fields.IntField(default=0)
    average_session_length = fields.IntField(default=0)

    # Streak tracking
    current_streak = fields.IntField(default=0)
    longest_streak = fields.IntField(default=0)
    last_activity_date = fields.DateField()

    # Weekly summaries (embedded as dictionaries)
    # Structure: [{week: 1, days_completed: 5, focus_minutes: 150, summary: "Great week!"}]
    weekly_summaries = fields.ListField(fields.DictField())

    # Achievements/badges earned
    achievements = fields.ListField(fields.DictField())  # [{name: "First Week", earned_at: datetime}]

    # Overall ratings
    overall_difficulty = fields.FloatField()  # Average difficulty rating
    overall_satisfaction = fields.FloatField()  # Average satisfaction rating

    # Timestamps
    started_at = fields.DateTimeField()
    last_updated_at = fields.DateTimeField(default=datetime.utcnow)
    completed_at = fields.DateTimeField()

    meta = {
        'collection': 'program_progress',
        'indexes': [
            'user_id',
            'user_program_id',
            'program_id',
            ('user_id', 'program_id'),
        ],
    }

    def update_progress(self):
        """Recalculate and update progress statistics"""
        if self.total_days > 0:
            self.completion_percentage = (self.days_completed / self.total_days) * 100

        if self.total_sessions > 0:
            self.average_session_length = self.total_focus_minutes // self.total_sessions

        self.last_updated_at = datetime.utcnow()
        self.save()

    def add_weekly_summary(self, week_number: int, days_completed: int, focus_minutes: int, summary: str = ""):
        """Add or update weekly summary"""
        weekly_summary = {
            'week': week_number,
            'days_completed': days_completed,
            'focus_minutes': focus_minutes,
            'summary': summary,
            'created_at': datetime.utcnow()
        }

        # Check if week summary already exists
        existing_index = next((i for i, ws in enumerate(self.weekly_summaries) if ws['week'] == week_number), None)

        if existing_index is not None:
            self.weekly_summaries[existing_index] = weekly_summary
        else:
            self.weekly_summaries.append(weekly_summary)

        self.last_updated_at = datetime.utcnow()
        self.save()

    def add_achievement(self, achievement_name: str, description: str = ""):
        """Add an achievement/badge"""
        achievement = {
            'name': achievement_name,
            'description': description,
            'earned_at': datetime.utcnow()
        }

        # Check if achievement already exists
        if not any(ach['name'] == achievement_name for ach in self.achievements):
            self.achievements.append(achievement)
            self.save()

    def update_streak(self, is_active_today: bool):
        """Update streak information"""
        today = datetime.utcnow().date()

        if is_active_today:
            if self.last_activity_date:
                days_diff = (today - self.last_activity_date).days

                if days_diff == 1:
                    # Consecutive day
                    self.current_streak += 1
                elif days_diff > 1:
                    # Streak broken
                    self.current_streak = 1
                # If days_diff == 0, same day, don't increment
            else:
                # First activity
                self.current_streak = 1

            self.last_activity_date = today

            # Update longest streak
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak

            self.save()

    def __str__(self):
        return f"Progress for User {self.user_id} - Program {self.program_id}"
