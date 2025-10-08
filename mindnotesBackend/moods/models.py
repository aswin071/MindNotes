from django.db import models
from django.utils.translation import gettext_lazy as _
from authentication.models import User
from utils.model_abstracts import Model


"""
REMOVED MODELS (Moved to MongoDB):
- MoodEntry → MoodEntryMongo (time-series data)
- MoodPattern → Stored in MongoDB analytics
- MoodInsight → Stored in MongoDB analytics
- UserMoodFactor → Can be stored in MongoDB as flexible data

KEPT MODELS (Reference Data):
- MoodCategory (reference data, rarely changes)
- CustomMoodCategory (user settings)
- MoodFactor (reference data)
"""


class MoodCategory(Model):
    """
    KEEP in PostgreSQL - System reference data
    Rarely changes, used for lookups
    """
    
    name = models.CharField(max_length=50, unique=True, db_index=True)
    emoji = models.CharField(max_length=10)
    color = models.CharField(max_length=7)
    description = models.TextField(blank=True)
    
    is_system = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mood_categories'
        verbose_name_plural = 'mood categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        return f"{self.emoji} {self.name}"


class CustomMoodCategory(Model):
    """
    KEEP in PostgreSQL - User-specific reference data
    Pro feature, limited quantity per user
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_moods')
    
    name = models.CharField(max_length=50)
    emoji = models.CharField(max_length=10)
    color = models.CharField(max_length=7, default='#3B82F6')
    description = models.TextField(blank=True)
    
    # NEW: Add usage tracking
    usage_count = models.IntegerField(default=0)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'custom_mood_categories'
        unique_together = ['user', 'name']
        ordering = ['name']
        indexes = [
            models.Index(fields=['user', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.name}"


class MoodFactor(Model):
    """
    KEEP in PostgreSQL - System reference data
    """
    
    FACTOR_TYPES = [
        ('sleep', 'Sleep'),
        ('exercise', 'Exercise'),
        ('social', 'Social Interaction'),
        ('work', 'Work/Productivity'),
        ('weather', 'Weather'),
        ('health', 'Physical Health'),
        ('stress', 'Stress Level'),
        ('diet', 'Diet/Nutrition'),
        ('medication', 'Medication'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    factor_type = models.CharField(max_length=20, choices=FACTOR_TYPES)
    icon = models.CharField(max_length=50, blank=True)
    
    is_system = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'mood_factors'
        ordering = ['name']
    
    def __str__(self):
        return self.name

