from mongoengine import Document, fields
from datetime import datetime


class DailyPromptSetMongo(Document):
    """
    MongoDB model for daily prompt sets
    Regenerated daily, temporary data
    """
    user_id = fields.IntField(required=True, index=True)
    date = fields.DateField(required=True, index=True)
    
    is_active = fields.BooleanField(default=False, index=True)
    # Prompts - Store from PostgreSQL with details
    prompts = fields.ListField(fields.DictField())  # [{id: 1, question: "...", category: "..."}]
    
    # Completion tracking
    completed_prompt_ids = fields.ListField(fields.IntField())
    completed_count = fields.IntField(default=0)
    is_fully_completed = fields.BooleanField(default=False)
    
    # Timestamps
    generated_at = fields.DateTimeField(default=datetime.utcnow)
    last_interaction_at = fields.DateTimeField()
    
    meta = {
        'collection': 'daily_prompt_sets',
        'indexes': [
            'user_id',
            'date',
            'is_active',
            ('user_id', 'date'),  # Compound index for queries
            ('user_id', '-date'),  # For date range queries
            ('user_id', 'is_fully_completed'),  # For streak tracking
            {'fields': ['generated_at'], 'expireAfterSeconds': 7776000},  # TTL: 90 days
        ],
    }
    
    def __str__(self):
        return f"{self.user_id} - {self.date} - {self.completed_count}/{len(self.prompts)}"


class PromptResponseMongo(Document):
    """User responses to prompts - flexible schema"""
    user_id = fields.IntField(required=True, index=True)
    prompt_id = fields.IntField(required=True)  # Reference to PostgreSQL
    daily_set_date = fields.DateField()
    
    # Response
    response = fields.StringField(required=True)
    word_count = fields.IntField(default=0)
    time_spent_seconds = fields.IntField(default=0)
    
    # Context
    mood_at_response = fields.IntField()
    location = fields.DictField()
    
    # Timestamps
    responded_at = fields.DateTimeField(default=datetime.utcnow)

    is_active = fields.BooleanField(default=False)
    
    meta = {
        'collection': 'prompt_responses',
        'indexes': [
            'user_id',
            'prompt_id',
            'is_active',
            'daily_set_date',
            ('user_id', '-responded_at'),  # For user history
            ('user_id', 'prompt_id'),  # For checking duplicates
            ('user_id', 'daily_set_date'),  # For daily responses
            {'fields': ['responded_at'], 'expireAfterSeconds': 31536000},  # TTL: 1 year
        ],
        'ordering': ['-responded_at'],
    }
    
    def __str__(self):
        return f"{self.user_id} - Prompt {self.prompt_id} - {self.responded_at.date()}"
