from rest_framework import serializers
from focus.models import FocusProgram, ProgramDay, UserFocusProgram


class FocusProgramSerializer(serializers.ModelSerializer):
    """Serializer for Focus Program list"""
    can_access = serializers.BooleanField(read_only=True)
    is_enrolled = serializers.BooleanField(read_only=True)
    enrollment_id = serializers.IntegerField(read_only=True, allow_null=True)
    enrollment_status = serializers.CharField(read_only=True, allow_null=True)
    current_day = serializers.IntegerField(read_only=True, allow_null=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = FocusProgram
        fields = [
            'id', 'name', 'program_type', 'description', 'duration_days',
            'objectives', 'is_pro_only', 'can_access', 'icon', 'color',
            'cover_image_url', 'is_enrolled', 'enrollment_id', 
            'enrollment_status', 'current_day'
        ]

    def get_cover_image_url(self, obj):
        if hasattr(obj, 'cover_image') and obj.cover_image:
            return obj.cover_image.url
        return None


class ProgramDaySerializer(serializers.ModelSerializer):
    """Serializer for Program Day details"""
    
    class Meta:
        model = ProgramDay
        fields = [
            'id', 'day_number', 'title', 'description',
            'focus_duration', 'tasks', 'tips', 'reflection_prompts'
        ]


class EnrollProgramSerializer(serializers.Serializer):
    """Serializer for enrolling in a program"""
    program_id = serializers.IntegerField(required=True)

    def validate_program_id(self, value):
        if not FocusProgram.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Program not found or inactive")
        return value


class StartProgramSerializer(serializers.Serializer):
    """Serializer for starting a program"""
    enrollment_id = serializers.IntegerField(required=True)


class TaskStatusSerializer(serializers.Serializer):
    """Serializer for updating task status"""
    enrollment_id = serializers.IntegerField(required=True)
    day_number = serializers.IntegerField(required=True, min_value=1)
    task_index = serializers.IntegerField(required=True, min_value=0)
    is_completed = serializers.BooleanField(required=True)


class StartFocusSessionSerializer(serializers.Serializer):
    """Serializer for starting a focus session"""
    enrollment_id = serializers.IntegerField(required=True)
    day_number = serializers.IntegerField(required=True, min_value=1)
    duration_minutes = serializers.IntegerField(required=True, min_value=1, max_value=180)
    session_type = serializers.ChoiceField(
        choices=['pomodoro', 'custom', 'program'],
        default='program'
    )
    task_description = serializers.CharField(required=False, allow_blank=True, max_length=500)


class CompleteFocusSessionSerializer(serializers.Serializer):
    """Serializer for completing a focus session"""
    session_id = serializers.CharField(required=True)
    productivity_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class AddReflectionSerializer(serializers.Serializer):
    """Serializer for adding reflection response"""
    enrollment_id = serializers.IntegerField(required=True)
    day_number = serializers.IntegerField(required=True, min_value=1)
    question = serializers.CharField(required=True)
    answer = serializers.CharField(required=True)


class ProgramProgressSerializer(serializers.Serializer):
    """Serializer for program progress"""
    enrollment_id = serializers.IntegerField(read_only=True)
    program = serializers.DictField(read_only=True)
    status = serializers.CharField(read_only=True)
    current_day = serializers.IntegerField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    progress = serializers.DictField(read_only=True)
    current_day_info = serializers.DictField(read_only=True, allow_null=True)


class DayDetailsSerializer(serializers.Serializer):
    """Serializer for day details with user progress"""
    day_number = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)
    focus_duration = serializers.IntegerField(read_only=True)
    tips = serializers.ListField(read_only=True)
    reflection_prompts = serializers.ListField(read_only=True)
    user_progress = serializers.DictField(read_only=True)


class WeeklyReviewSerializer(serializers.Serializer):
    """Serializer for weekly review"""
    week_number = serializers.IntegerField(read_only=True)
    start_day = serializers.IntegerField(read_only=True)
    end_day = serializers.IntegerField(read_only=True)
    days_completed = serializers.IntegerField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    completion_rate = serializers.FloatField(read_only=True)
    total_focus_minutes = serializers.IntegerField(read_only=True)
    average_difficulty = serializers.FloatField(read_only=True, allow_null=True)
    average_satisfaction = serializers.FloatField(read_only=True, allow_null=True)
    current_streak = serializers.IntegerField(read_only=True)
    achievements_earned = serializers.ListField(read_only=True)
    summary = serializers.CharField(read_only=True, allow_blank=True)


class ProgramHistorySerializer(serializers.Serializer):
    """Serializer for program history"""
    enrollment_id = serializers.IntegerField(read_only=True)
    program_name = serializers.CharField(read_only=True)
    program_type = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, allow_null=True)
    current_day = serializers.IntegerField(read_only=True)
    total_days = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.FloatField(read_only=True)
    total_focus_minutes = serializers.IntegerField(read_only=True)
    current_streak = serializers.IntegerField(read_only=True)


class FocusSessionSerializer(serializers.Serializer):
    """Serializer for focus session data"""
    session_id = serializers.CharField(read_only=True)
    started_at = serializers.DateTimeField(read_only=True)
    ended_at = serializers.DateTimeField(read_only=True, allow_null=True)
    planned_duration_seconds = serializers.IntegerField(read_only=True)
    actual_duration_seconds = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    session_type = serializers.CharField(read_only=True)
    productivity_rating = serializers.IntegerField(read_only=True, allow_null=True)
    notes = serializers.CharField(read_only=True, allow_blank=True)


class PauseSessionSerializer(serializers.Serializer):
    """Serializer for pausing a session"""
    session_id = serializers.CharField(required=True)


class ResumeSessionSerializer(serializers.Serializer):
    """Serializer for resuming a paused session"""
    session_id = serializers.CharField(required=True)


class AddDistractionSerializer(serializers.Serializer):
    """Serializer for logging distractions"""
    session_id = serializers.CharField(required=True)
    distraction_note = serializers.CharField(required=True, max_length=500)
