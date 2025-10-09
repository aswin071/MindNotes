from mongoengine import Document, fields
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
            ('user_id', '-started_at'),
            ('user_id', 'status'),
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
            pause['duration_seconds'] = (pause['ended_at'] - pause['started_at']).seconds
            self.total_pause_duration_seconds += pause['duration_seconds']
            self.save()
    
    def __str__(self):
        return f"{self.user_id} - {self.session_type} - {self.started_at.date()}"
