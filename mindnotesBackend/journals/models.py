from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
from authentication.models import User
from utils.model_abstracts import Model
import uuid


"""
REMOVED MODELS (Moved to MongoDB):
- JournalEntry → JournalEntryMongo
- JournalPhoto → Embedded in JournalEntryMongo
- JournalVoiceNote → Embedded in JournalEntryMongo
- JournalPromptResponse → Embedded in JournalEntryMongo
- EntryTemplate → Can move to MongoDB or keep (keeping for now)

KEPT MODELS:
- Tag (needs PostgreSQL for user relationships and fast lookups)
"""

class Tag(Model):
    """Tags for categorizing journal entries"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tags', db_index=True)
    name = models.CharField(max_length=50, db_index=True)
    color = models.CharField(max_length=7, default='#3B82F6')  # Hex color
    class Meta:
        db_table = 'tags'
        unique_together = ['user', 'name']
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'name']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


# class JournalEntry(Model):
#     """Main journal entry model supporting text, voice, and photos"""
    
#     ENTRY_TYPES = [
#         ('text', 'Text'),
#         ('voice', 'Voice'),
#         ('photo', 'Photo'),
#         ('mixed', 'Mixed'),
#     ]
    
#     PRIVACY_CHOICES = [
#         ('private', 'Private'),
#         ('public', 'Public'),
#     ]
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='journal_entries')
    
#     # Entry content
#     title = models.CharField(max_length=255, blank=True)
#     content = models.TextField(blank=True)
#     entry_type = models.CharField(max_length=20, choices=ENTRY_TYPES, default='text')
    
#     # Metadata
#     entry_date = models.DateTimeField()  # User can backdate entries
#     privacy = models.CharField(max_length=20, choices=PRIVACY_CHOICES, default='private')
#     is_favorite = models.BooleanField(default=False)
#     is_archived = models.BooleanField(default=False)
    
#     # Relationships
#     tags = models.ManyToManyField(Tag, related_name='journal_entries', blank=True)
    
#     # Location (optional)
#     location_name = models.CharField(max_length=255, blank=True)
#     latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
#     longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
#     # Weather data (optional)
#     weather = models.CharField(max_length=50, blank=True)
#     temperature = models.FloatField(null=True, blank=True)
    
#     # Statistics
#     word_count = models.IntegerField(default=0)
#     character_count = models.IntegerField(default=0)   
#     class Meta:
#         db_table = 'journal_entries'
#         verbose_name = _('journal entry')
#         verbose_name_plural = _('journal entries')
#         ordering = ['-entry_date']
#         indexes = [
#             models.Index(fields=['user', '-entry_date']),
#             models.Index(fields=['user', 'is_favorite']),
#             models.Index(fields=['user', 'is_archived']),
#         ]
    
#     def __str__(self):
#         return f"{self.user.email} - {self.entry_date.date()}"
    
#     def save(self, *args, **kwargs):
#         # Auto-calculate word and character count
#         if self.content:
#             self.word_count = len(self.content.split())
#             self.character_count = len(self.content)
#         super().save(*args, **kwargs)


# class JournalPhoto(Model):
#     """Photos attached to journal entries"""
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='photos')
    
#     image = models.ImageField(
#         upload_to='journal_entries/photos/%Y/%m/%d/',
#         validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'heic'])]
#     )
#     caption = models.CharField(max_length=255, blank=True)
#     order = models.IntegerField(default=0)
    
#     # Image metadata
#     width = models.IntegerField(null=True, blank=True)
#     height = models.IntegerField(null=True, blank=True)
#     file_size = models.IntegerField(null=True, blank=True)
    
#     class Meta:
#         db_table = 'journal_photos'
#         ordering = ['order', 'created_at']
#         indexes = [
#             models.Index(fields=['entry', 'order']),
#         ]
    
#     def __str__(self):
#         return f"Photo for {self.entry.id}"


# class JournalVoiceNote(Model):
#     """Voice notes attached to journal entries"""
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='voice_notes')
    
#     audio_file = models.FileField(
#         upload_to='journal_entries/voice/%Y/%m/%d/',
#         validators=[FileExtensionValidator(allowed_extensions=['mp3', 'wav', 'm4a', 'ogg'])]
#     )
    
#     # Audio metadata
#     duration = models.IntegerField(help_text='Duration in seconds')
#     file_size = models.IntegerField(help_text='File size in bytes')
    
#     # Transcription
#     transcription = models.TextField(blank=True)
#     transcription_language = models.CharField(max_length=10, default='en')
#     is_transcribed = models.BooleanField(default=False)  
#     class Meta:
#         db_table = 'journal_voice_notes'
#         ordering = ['created_at']
    
#     def __str__(self):
#         return f"Voice note for {self.entry.id}"


# class JournalPromptResponse(Model):
#     """Responses to daily prompts within journal entries"""
    
#     entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='prompt_responses')
#     prompt = models.ForeignKey('prompts.DailyPrompt', on_delete=models.SET_NULL, null=True)
    
#     question = models.TextField()  # Store the question for historical reference
#     answer = models.TextField()
#     class Meta:
#         db_table = 'journal_prompt_responses'
#         ordering = ['created_at']
    
#     def __str__(self):
#         return f"Response to prompt in {self.entry.id}"


class EntryTemplate(Model):
    """Reusable templates for journal entries"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entry_templates', db_index=True)

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    content = models.TextField()

    # Usage statistics
    usage_count = models.IntegerField(default=0, db_index=True)


    class Meta:
        db_table = 'entry_templates'
        ordering = ['-usage_count', 'name']
        indexes = [
            models.Index(fields=['user', '-usage_count']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"