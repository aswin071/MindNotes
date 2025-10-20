from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime
import uuid


class PhotoEmbed(EmbeddedDocument):
    """Embedded photo data in journal entry"""
    id = fields.UUIDField(default=uuid.uuid4, primary_key=True)
    image_url = fields.StringField(required=True)
    caption = fields.StringField(max_length=255)
    order = fields.IntField(default=0)
    width = fields.IntField()
    height = fields.IntField()
    file_size = fields.IntField()
    uploaded_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {'strict': False}


class VoiceNoteEmbed(EmbeddedDocument):
    """Embedded voice note data"""
    id = fields.UUIDField(default=uuid.uuid4, primary_key=True)
    audio_url = fields.StringField(required=True)
    duration = fields.IntField()  # seconds
    file_size = fields.IntField()  # bytes
    transcription = fields.StringField()
    transcription_language = fields.StringField(default='en')
    is_transcribed = fields.BooleanField(default=False)
    uploaded_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {'strict': False}


class PromptResponseEmbed(EmbeddedDocument):
    """Embedded prompt response"""
    prompt_id = fields.IntField()  # Reference to PostgreSQL DailyPrompt
    question = fields.StringField(required=True)
    answer = fields.StringField(required=True)
    word_count = fields.IntField(default=0)
    answered_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {'strict': False}


class JournalEntryMongo(Document):
    """
    MongoDB model for journal entries
    Stores the actual entry content and nested data
    """
    # Link to PostgreSQL user (PostgreSQL User.id is BigAutoField/Integer)
    user_id = fields.IntField(required=True, index=True)
    
    # Entry content
    title = fields.StringField(max_length=255)
    content = fields.StringField()
    entry_type = fields.StringField(
        choices=['text', 'voice', 'photo', 'mixed'],
        default='text'
    )
    
    # Metadata
    entry_date = fields.DateTimeField(required=True, index=True)
    privacy = fields.StringField(choices=['private', 'public'], default='private')
    is_favorite = fields.BooleanField(default=False, index=True)
    is_archived = fields.BooleanField(default=False, index=True)
    is_active = fields.BooleanField(default=False, index=True)
    
    # Tags - Store IDs from PostgreSQL
    tag_ids = fields.ListField(fields.IntField())
    
    # Location
    location_name = fields.StringField()
    latitude = fields.DecimalField(precision=2)
    longitude = fields.DecimalField(precision=2)
    
    # Weather
    weather = fields.StringField()
    temperature = fields.FloatField()
    
    # Statistics
    word_count = fields.IntField(default=0)
    character_count = fields.IntField(default=0)
    reading_time_minutes = fields.IntField(default=0)
    
    # Embedded documents
    photos = fields.ListField(fields.EmbeddedDocumentField(PhotoEmbed))
    voice_notes = fields.ListField(fields.EmbeddedDocumentField(VoiceNoteEmbed))
    prompt_responses = fields.ListField(fields.EmbeddedDocumentField(PromptResponseEmbed))
    
    # Version control
    version = fields.IntField(default=1)
    edit_history = fields.ListField(fields.DictField())
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow, index=True)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'journal_entries',
        'db_alias': 'default',  # Use the default MongoDB connection
        'indexes': [
            'user_id',
            'entry_date',
            'is_favorite',
            ('user_id', '-entry_date'),  # Compound index
            {
                'fields': ['$content', '$title'],  # Text search
                'default_language': 'english',
                'weights': {'content': 10, 'title': 5}
            }
        ],
        'ordering': ['-entry_date'],
        'strict': False,  # Allow dynamic fields
    }
    
    def save(self, *args, **kwargs):
        # Auto-update word count and timestamps
        if self.content:
            self.word_count = len(self.content.split())
            self.character_count = len(self.content)
            self.reading_time_minutes = max(1, self.word_count // 200)
        
        self.updated_at = datetime.utcnow()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user_id} - {self.entry_date.date()}"
