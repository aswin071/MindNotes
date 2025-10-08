from django.db import models
from django.utils.translation import gettext_lazy as _
from utils.model_abstracts import Model
from authentication.models import User
"""
REMOVED MODELS (Moved to MongoDB):
- UserDailyPromptSet → DailyPromptSetMongo
- UserPromptResponse → PromptResponseMongo
- PromptFeedback → Can store in MongoDB

KEPT MODELS (Reference Data):
- PromptCategory (reference data)
- DailyPrompt (prompt bank)
- CustomPrompt (user-created prompts)
"""

class PromptCategory(Model):
    """KEEP - Reference data"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'prompt_categories'
        verbose_name_plural = 'prompt categories'
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class DailyPrompt(Model):
    """
    KEEP in PostgreSQL - Prompt bank (curated content)
    """
    
    category = models.ForeignKey(
        PromptCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prompts'
    )
    
    question = models.TextField(unique=True,blank=True,null=True)
    description = models.TextField(blank=True,null=True)
    
    tags = models.JSONField(default=list)
    difficulty = models.CharField(
        max_length=20,
        choices=[('easy', 'Easy'), ('medium', 'Medium'), ('deep', 'Deep')],
        default='medium'
    )
    
    # REMOVED: usage tracking (calculated from MongoDB)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_prompts'
        ordering = ['category', 'difficulty']
        indexes = [
            models.Index(fields=['category', 'is_active']),
        ]
    
    def __str__(self):
        return self.question[:100]


class CustomPrompt(Model):
    """KEEP - User-created prompts (settings data)"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_prompts')
    
    question = models.TextField()
    description = models.TextField(blank=True)
    
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(
        max_length=20,
        choices=[('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')],
        blank=True
    )
    
    # REMOVED: usage stats (calculated from MongoDB)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'custom_prompts'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.question[:50]}"