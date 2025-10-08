from mongoengine import Document, fields
from datetime import datetime


class UserAnalyticsMongo(Document):
    """
    Pre-aggregated analytics data for fast dashboard loading
    Updated periodically via Celery tasks
    """
    user_id = fields.IntField(required=True, unique=True, index=True)
    
    # Journal statistics
    total_entries = fields.IntField(default=0)
    total_words = fields.IntField(default=0)
    total_photos = fields.IntField(default=0)
    total_voice_notes = fields.IntField(default=0)
    
    # Streaks
    current_streak = fields.IntField(default=0)
    longest_streak = fields.IntField(default=0)
    
    # Time-based stats
    entries_this_week = fields.IntField(default=0)
    entries_this_month = fields.IntField(default=0)
    entries_this_year = fields.IntField(default=0)
    
    # Mood analytics
    average_mood_intensity = fields.FloatField(default=0)
    mood_distribution = fields.DictField()  # {mood_name: count}
    most_common_mood = fields.StringField()
    
    # Focus analytics
    total_focus_minutes = fields.IntField(default=0)
    total_focus_sessions = fields.IntField(default=0)
    average_session_duration = fields.IntField(default=0)
    
    # Trends
    mood_trend = fields.StringField(choices=['improving', 'stable', 'declining'])
    productivity_trend = fields.StringField(choices=['improving', 'stable', 'declining'])
    
    # Last calculated
    last_calculated_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'user_analytics',
        'indexes': ['user_id'],
    }
    
    def __str__(self):
        return f"{self.user_id} - Analytics"


class DailyActivityLogMongo(Document):
    """
    Daily activity aggregation for calendar view
    """
    user_id = fields.IntField(required=True, index=True)
    date = fields.DateField(required=True, index=True)
    
    # Activity counts
    journal_entries_count = fields.IntField(default=0)
    mood_entries_count = fields.IntField(default=0)
    focus_sessions_count = fields.IntField(default=0)
    prompt_responses_count = fields.IntField(default=0)
    
    # Aggregated data
    total_words_written = fields.IntField(default=0)
    total_focus_minutes = fields.IntField(default=0)
    average_mood_intensity = fields.FloatField()
    
    # Flags
    has_journal_entry = fields.BooleanField(default=False)
    has_mood_entry = fields.BooleanField(default=False)
    has_focus_session = fields.BooleanField(default=False)
    
    meta = {
        'collection': 'daily_activity_logs',
        'indexes': [
            'user_id',
            'date',
            ('user_id', 'date'),
        ],
    }
    
    def __str__(self):
        return f"{self.user_id} - {self.date} - Activity Log"
