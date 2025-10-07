from django.db import models
from django.utils.translation import gettext_lazy as _
from utils.model_abstracts import Model

class DailyPrompt(Model):
    """Daily prompts for journaling"""
    
    text = models.TextField(
        _('prompt text'),
        help_text=_('The prompt question or statement for users')
    )
    scheduled_date = models.DateField(
        _('scheduled date'),
        null=True,
        blank=True,
        help_text=_('Date when this prompt should be displayed')
    )
    
    class Meta:
        db_table = 'daily_prompts'
        verbose_name = _('daily prompt')
        verbose_name_plural = _('daily prompts')
        ordering = ['-created_at']
    
    def __str__(self):
        return self.text[:50]