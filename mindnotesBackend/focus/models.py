from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from authentication.models import User
from utils.model_abstracts import Model


class FocusProgram(Model):
    """Pre-defined focus programs (14-day, 30-day)"""
    
    PROGRAM_TYPES = [
        ('14_day', '14-Day Program'),
        ('30_day', '30-Day Program'),
        ('custom', 'Custom Program'),
    ]
    
    name = models.CharField(max_length=100)
    program_type = models.CharField(max_length=20, choices=PROGRAM_TYPES)
    description = models.TextField()
    
    duration_days = models.IntegerField()
    
    # Program details
    objectives = models.JSONField(default=list)
    daily_tasks = models.JSONField(default=list)
    
    # Requirements
    is_pro_only = models.BooleanField(default=True)
    
    # Display
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#3B82F6')
    cover_image = models.ImageField(upload_to='focus_programs/', null=True, blank=True)
    
    order = models.IntegerField(default=0)
    
    class Meta:
        db_table = 'focus_programs'
        ordering = ['order', 'duration_days']
    
    def __str__(self):
        return self.name


class ProgramDay(Model):
    """Individual day content within a focus program"""
    
    program = models.ForeignKey(FocusProgram, on_delete=models.CASCADE, related_name='days')
    
    day_number = models.IntegerField()
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Daily content
    focus_duration = models.IntegerField(help_text='Recommended focus time in minutes')
    tasks = models.JSONField(default=list)
    tips = models.JSONField(default=list)
    
    # Reflections
    reflection_prompts = models.JSONField(default=list)
    
    class Meta:
        db_table = 'program_days'
        unique_together = ['program', 'day_number']
        ordering = ['program', 'day_number']
    
    def __str__(self):
        return f"{self.program.name} - Day {self.day_number}"


class FocusPause(Model):
    """Track pauses within focus sessions"""
    
    session = models.ForeignKey('FocusSession', on_delete=models.CASCADE, related_name='pauses')
    
    paused_at = models.DateTimeField(auto_now_add=True)
    resumed_at = models.DateTimeField(null=True, blank=True)
    pause_duration = models.IntegerField(default=0, help_text='Pause duration in seconds')
    
    reason = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'focus_pauses'
        ordering = ['paused_at']
    
    def __str__(self):
        return f"Pause in session {self.session.id}"


class FocusGoal(Model):
    """User's focus goals and targets"""
    
    GOAL_TYPES = [
        ('daily', 'Daily Goal'),
        ('weekly', 'Weekly Goal'),
        ('monthly', 'Monthly Goal'),
        ('custom', 'Custom Goal'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_goals')
    
    goal_type = models.CharField(max_length=20, choices=GOAL_TYPES)
    target_minutes = models.IntegerField(help_text='Target focus minutes')
    
    # Time period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Progress
    current_minutes = models.IntegerField(default=0)
    is_achieved = models.BooleanField(default=False)
    achieved_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = 'focus_goals'
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['user', 'goal_type', '-start_date']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.goal_type} - {self.target_minutes}min"
    
    def progress_percentage(self):
        """Calculate goal completion percentage"""
        if self.target_minutes == 0:
            return 0
        return min(100, (self.current_minutes / self.target_minutes) * 100)


class UserFocusProgram(Model):
    """User's participation in focus programs"""
    
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_focus_programs')
    program = models.ForeignKey(FocusProgram, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    
    current_day = models.IntegerField(default=1)
    
    # Progress tracking
    total_focus_minutes = models.IntegerField(default=0)
    days_completed = models.IntegerField(default=0)
    completion_percentage = models.FloatField(default=0.0)
    
    # Streak
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    class Meta:
        db_table = 'user_focus_programs'
        unique_together = ['user', 'program', 'started_at']
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.program.name} ({self.status})"


class UserProgramDay(Model):
    """User's completion status for individual program days"""
    
    user_program = models.ForeignKey(
        UserFocusProgram,
        on_delete=models.CASCADE,
        related_name='day_completions'
    )
    program_day = models.ForeignKey(ProgramDay, on_delete=models.CASCADE)
    
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # User's focus session for this day
    focus_minutes = models.IntegerField(default=0)
    
    # User's reflections
    reflection_responses = models.JSONField(default=dict)
    notes = models.TextField(blank=True)
    
    # Rating
    difficulty_rating = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    class Meta:
        db_table = 'user_program_days'
        unique_together = ['user_program', 'program_day']
        ordering = ['program_day__day_number']
    
    def __str__(self):
        return f"{self.user_program.user.email} - Day {self.program_day.day_number}"


class FocusSession(Model):
    """Individual focus/timer sessions"""
    
    SESSION_TYPES = [
        ('pomodoro', 'Pomodoro'),
        ('custom', 'Custom Duration'),
        ('program', 'Program Session'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('canceled', 'Canceled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='focus_sessions')
    
    session_type = models.CharField(max_length=20, choices=SESSION_TYPES, default='custom')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    
    program_day = models.ForeignKey(ProgramDay, on_delete=models.SET_NULL, null=True, blank=True)
    user_program = models.ForeignKey(UserFocusProgram, on_delete=models.SET_NULL, null=True, blank=True)    
    class Meta:
        db_table = 'focus_sessions'
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['user', '-start_time']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.session_type} ({self.status})"