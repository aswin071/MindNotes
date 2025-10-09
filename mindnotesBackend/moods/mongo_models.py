from mongoengine import Document, fields
from datetime import datetime


class MoodEntryMongo(Document):
    """
    MongoDB model for mood entries (time-series data)
    High write volume, flexible schema for factors
    """
    user_id = fields.IntField(required=True, index=True)
    journal_entry_id = fields.UUIDField()  # Link to journal if exists
    
    # Mood data - Store category_id from PostgreSQL
    category_id = fields.IntField()
    custom_category_id = fields.IntField()
    category_name = fields.StringField()  # Denormalized for fast queries
    emoji = fields.StringField()
    
    # Intensity
    intensity = fields.IntField(min_value=1, max_value=10, required=True)
    
    # Context
    note = fields.StringField()
    
    # Factors - flexible structure
    factors = fields.ListField(fields.DictField())  # [{id: 1, name: "Sleep", value: "good"}]
    
    # Time tracking
    recorded_at = fields.DateTimeField(required=True, index=True)
    created_at = fields.DateTimeField(default=datetime.utcnow)

    is_active = fields.BooleanField(default=False, index=True)
    
    # Additional context (flexible)
    context = fields.DictField()  # Store any additional metadata
    
    meta = {
        'collection': 'mood_entries',
        'indexes': [
            'user_id',
            'recorded_at',
            ('user_id', '-recorded_at'),
            'category_id',
        ],
        'ordering': ['-recorded_at'],
        'strict': False,
    }
    
    def __str__(self):
        return f"{self.user_id} - {self.category_name} ({self.intensity}) - {self.recorded_at.date()}"
