from mongoengine import Document, fields
from datetime import datetime


class DailyPromptSetMongo(Document):
    """
    MongoDB model for daily prompt sets
    Regenerated daily, temporary data
    """
    user_id = fields.IntField(required=True, index=True)
    date = fields.DateField(required=True, index=True)
    
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
            ('user_id', 'date'),
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
    responded_at = fields.DateTimeField(default=datetime.utcnow, index=True)
    
    meta = {
        'collection': 'prompt_responses',
        'indexes': [
            'user_id',
            'prompt_id',
            'responded_at',
            ('user_id', '-responded_at'),
        ],
        'ordering': ['-responded_at'],
    }
    
    def __str__(self):
        return f"{self.user_id} - Prompt {self.prompt_id} - {self.responded_at.date()}"
