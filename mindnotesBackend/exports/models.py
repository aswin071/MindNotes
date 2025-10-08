from django.db import models
from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import User
from utils.model_abstracts import Model
import uuid

"""
MODIFIED:
- ExportRequest: Keep metadata in PostgreSQL, processing data in MongoDB
- WeeklyReview: Can move to MongoDB or keep
- ScheduledExport: Keep in PostgreSQL
"""
# Create your models here.


class ExportRequest(Model):
    """
    MODIFIED: Keep request metadata, actual data processing in MongoDB
    """
    
    EXPORT_TYPES = [
        ('pdf', 'PDF'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('markdown', 'Markdown'),
    ]
    
    EXPORT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='export_requests')
    
    export_type = models.CharField(max_length=20, choices=EXPORT_TYPES)
    status = models.CharField(max_length=20, choices=EXPORT_STATUS, default='pending')
    
    # Filter parameters (stored for reference)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    include_photos = models.BooleanField(default=True)
    include_voice_notes = models.BooleanField(default=False)
    include_mood_data = models.BooleanField(default=True)
    include_focus_data = models.BooleanField(default=True)
    
    # Output file reference
    file = models.FileField(upload_to='exports/%Y/%m/', null=True, blank=True)
    file_size = models.BigIntegerField(null=True, blank=True)
    
    # Metadata
    total_entries = models.IntegerField(default=0)
    processing_time_seconds = models.IntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'export_requests'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.export_type} - {self.status}"


class ScheduledExport(Model):
    """KEEP in PostgreSQL - Scheduling configuration"""
    
    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scheduled_exports')
    
    export_type = models.CharField(max_length=20, choices=ExportRequest.EXPORT_TYPES)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    
    include_photos = models.BooleanField(default=True)
    include_voice_notes = models.BooleanField(default=False)
    include_mood_data = models.BooleanField(default=True)
    include_focus_data = models.BooleanField(default=True)
    
    send_email = models.BooleanField(default=True)
    email_address = models.EmailField(blank=True)
    
    next_run_at = models.DateTimeField()
    last_run_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'scheduled_exports'
        ordering = ['next_run_at']
        indexes = [
            models.Index(fields=['next_run_at', 'is_active']),
        ]