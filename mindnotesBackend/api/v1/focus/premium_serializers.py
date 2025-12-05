"""
Serializers for Premium Focus Programs
- 5-Minute Morning Charge
- Brain Dump Reset
- Gratitude Pause
"""

from rest_framework import serializers
from focus.models import BrainDumpCategory


# ============================================
# COMMON SERIALIZERS
# ============================================

class PremiumAccessSerializer(serializers.Serializer):
    """Serializer for premium access information"""
    has_access = serializers.BooleanField()
    access_type = serializers.CharField()  # 'paid', 'trial', 'expired'
    trial_info = serializers.DictField()


class BrainDumpCategorySerializer(serializers.ModelSerializer):
    """Serializer for Brain Dump categories"""

    class Meta:
        model = BrainDumpCategory
        fields = ['id', 'name', 'icon', 'color', 'description', 'order']


class PremiumProgramStatsSerializer(serializers.Serializer):
    """Serializer for user's premium program statistics"""
    morning_charge = serializers.DictField()
    brain_dump = serializers.DictField()
    gratitude_pause = serializers.DictField()
    total_sessions = serializers.IntegerField()
    first_session_date = serializers.DateField(allow_null=True)
    badges = serializers.ListField()


# ============================================
# MORNING CHARGE SERIALIZERS
# ============================================

class MorningChargeStartSerializer(serializers.Serializer):
    """Serializer for starting a Morning Charge session"""
    session_date = serializers.DateField(required=False, allow_null=True)


class MorningChargeBreathingSerializer(serializers.Serializer):
    """Serializer for completing breathing step"""
    session_id = serializers.CharField(required=True)
    duration_seconds = serializers.IntegerField(required=True, min_value=0)


class MorningChargeGratitudeSerializer(serializers.Serializer):
    """Serializer for gratitude spark"""
    session_id = serializers.CharField(required=True)
    gratitude_text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    voice_note_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    def validate(self, data):
        if not data.get('gratitude_text') and not data.get('voice_note_url'):
            raise serializers.ValidationError("Either gratitude_text or voice_note_url is required")
        return data


class MorningChargeAffirmationSerializer(serializers.Serializer):
    """Serializer for positive affirmation"""
    session_id = serializers.CharField(required=True)
    affirmation_text = serializers.CharField(required=True, max_length=500)
    is_favorite = serializers.BooleanField(default=False)


class MorningChargeClaritySerializer(serializers.Serializer):
    """Serializer for daily clarity prompt"""
    session_id = serializers.CharField(required=True)
    question = serializers.CharField(required=True, max_length=500)
    answer = serializers.CharField(required=True, max_length=1000)


class MorningChargeCloseSerializer(serializers.Serializer):
    """Serializer for charge close"""
    session_id = serializers.CharField(required=True)


class MorningChargeCompleteSerializer(serializers.Serializer):
    """Serializer for completing the entire session"""
    session_id = serializers.CharField(required=True)
    total_duration_seconds = serializers.IntegerField(required=True, min_value=0)


class MorningChargeSessionResponseSerializer(serializers.Serializer):
    """Response serializer for Morning Charge session"""
    id = serializers.CharField()
    session_date = serializers.DateField()
    breathing_completed = serializers.BooleanField()
    gratitude_text = serializers.CharField(allow_null=True)
    gratitude_voice_note_url = serializers.CharField(allow_null=True)
    affirmation_text = serializers.CharField(allow_null=True)
    affirmation_is_favorite = serializers.BooleanField()
    clarity_prompt_question = serializers.CharField(allow_null=True)
    clarity_prompt_answer = serializers.CharField(allow_null=True)
    charge_close_completed = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    total_duration_seconds = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    created_at = serializers.DateTimeField()


# ============================================
# BRAIN DUMP SERIALIZERS
# ============================================

class BrainDumpStartSerializer(serializers.Serializer):
    """Serializer for starting a Brain Dump session"""
    session_date = serializers.DateField(required=False, allow_null=True)


class BrainDumpSettleInSerializer(serializers.Serializer):
    """Serializer for settle in step"""
    session_id = serializers.CharField(required=True)


class BrainDumpThoughtSerializer(serializers.Serializer):
    """Serializer for individual thoughts"""
    text = serializers.CharField(required=True, max_length=1000)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    category_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class BrainDumpAddThoughtsSerializer(serializers.Serializer):
    """Serializer for adding thoughts"""
    session_id = serializers.CharField(required=True)
    thoughts = serializers.ListField(
        child=BrainDumpThoughtSerializer(),
        min_length=1,
        max_length=50
    )


class BrainDumpGuidedResponsesSerializer(serializers.Serializer):
    """Serializer for guided question responses"""
    session_id = serializers.CharField(required=True)
    response_1 = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=1000)
    response_2 = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=1000)
    response_3 = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=1000)


class CategorizedThoughtSerializer(serializers.Serializer):
    """Serializer for categorizing a thought"""
    index = serializers.IntegerField(required=True, min_value=0)
    category_id = serializers.IntegerField(required=True)
    category_name = serializers.CharField(required=True)


class BrainDumpCategorizeSerializer(serializers.Serializer):
    """Serializer for categorizing thoughts"""
    session_id = serializers.CharField(required=True)
    categorized_thoughts = serializers.ListField(
        child=CategorizedThoughtSerializer(),
        min_length=1
    )


class BrainDumpChooseTaskSerializer(serializers.Serializer):
    """Serializer for choosing focus task"""
    session_id = serializers.CharField(required=True)
    task_text = serializers.CharField(required=True, max_length=1000)
    task_category_id = serializers.IntegerField(required=True)


class BrainDumpCloseBreatheSerializer(serializers.Serializer):
    """Serializer for close and breathe step"""
    session_id = serializers.CharField(required=True)


class BrainDumpCompleteSerializer(serializers.Serializer):
    """Serializer for completing the entire session"""
    session_id = serializers.CharField(required=True)
    total_duration_seconds = serializers.IntegerField(required=True, min_value=0)


class BrainDumpSessionResponseSerializer(serializers.Serializer):
    """Response serializer for Brain Dump session"""
    id = serializers.CharField()
    session_date = serializers.DateField()
    settle_in_completed = serializers.BooleanField()
    total_thoughts_count = serializers.IntegerField()
    categorize_completed = serializers.BooleanField()
    category_distribution = serializers.DictField()
    chosen_task_text = serializers.CharField(allow_null=True)
    chosen_task_category_id = serializers.IntegerField(allow_null=True)
    close_breathe_completed = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    total_duration_seconds = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class BrainDumpThoughtResponseSerializer(serializers.Serializer):
    """Response serializer for individual thought"""
    thought_text = serializers.CharField()
    category_id = serializers.IntegerField(allow_null=True)
    category_name = serializers.CharField(allow_null=True)
    order = serializers.IntegerField()


class BrainDumpSessionDetailSerializer(serializers.Serializer):
    """Detailed response serializer for Brain Dump session"""
    id = serializers.CharField()
    session_date = serializers.DateField()
    settle_in_completed = serializers.BooleanField()
    dump_thoughts = serializers.ListField(child=BrainDumpThoughtResponseSerializer())
    total_thoughts_count = serializers.IntegerField()
    guided_question_1_response = serializers.CharField(allow_null=True)
    guided_question_2_response = serializers.CharField(allow_null=True)
    guided_question_3_response = serializers.CharField(allow_null=True)
    categorize_completed = serializers.BooleanField()
    category_distribution = serializers.DictField()
    chosen_task_text = serializers.CharField(allow_null=True)
    chosen_task_category_id = serializers.IntegerField(allow_null=True)
    close_breathe_completed = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    total_duration_seconds = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    created_at = serializers.DateTimeField()


# ============================================
# GRATITUDE PAUSE SERIALIZERS
# ============================================

class GratitudePauseStartSerializer(serializers.Serializer):
    """Serializer for starting a Gratitude Pause session"""
    session_date = serializers.DateField(required=False, allow_null=True)


class GratitudePauseArriveSerializer(serializers.Serializer):
    """Serializer for arrive step"""
    session_id = serializers.CharField(required=True)


class GratitudePauseThreeGratitudesSerializer(serializers.Serializer):
    """Serializer for listing three gratitudes"""
    session_id = serializers.CharField(required=True)
    gratitude_1 = serializers.CharField(required=True, max_length=500)
    gratitude_2 = serializers.CharField(required=True, max_length=500)
    gratitude_3 = serializers.CharField(required=True, max_length=500)


class GratitudePauseDeepDiveSerializer(serializers.Serializer):
    """Serializer for deep dive responses"""
    session_id = serializers.CharField(required=True)
    selected_index = serializers.IntegerField(required=True, min_value=1, max_value=3)
    precise = serializers.CharField(required=True, max_length=500)
    why_matters = serializers.CharField(required=True, max_length=1000)
    who_made_possible = serializers.CharField(required=True, max_length=500)
    sensory_moment = serializers.CharField(required=True, max_length=1000)
    gratitude_line = serializers.CharField(required=True, max_length=500)


class GratitudePauseExpressionSerializer(serializers.Serializer):
    """Serializer for expression action"""
    session_id = serializers.CharField(required=True)
    action = serializers.ChoiceField(
        choices=['send_thank_you', 'leave_note', 'helpful_act', 'reminder_later', 'skipped'],
        required=True
    )
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True, max_length=1000)


class GratitudePauseAnchorSerializer(serializers.Serializer):
    """Serializer for anchor step"""
    session_id = serializers.CharField(required=True)


class GratitudePauseCompleteSerializer(serializers.Serializer):
    """Serializer for completing the entire session"""
    session_id = serializers.CharField(required=True)
    total_duration_seconds = serializers.IntegerField(required=True, min_value=0)


class GratitudePauseSessionResponseSerializer(serializers.Serializer):
    """Response serializer for Gratitude Pause session"""
    id = serializers.CharField()
    session_date = serializers.DateField()
    arrive_completed = serializers.BooleanField()
    gratitude_1 = serializers.CharField(allow_null=True)
    gratitude_2 = serializers.CharField(allow_null=True)
    gratitude_3 = serializers.CharField(allow_null=True)
    selected_gratitude_index = serializers.IntegerField(allow_null=True)
    selected_gratitude_text = serializers.CharField(allow_null=True)
    deep_dive_5_gratitude_line = serializers.CharField(allow_null=True)
    expression_action = serializers.CharField(allow_null=True)
    anchor_completed = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    total_duration_seconds = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class GratitudePauseSessionDetailSerializer(serializers.Serializer):
    """Detailed response serializer for Gratitude Pause session"""
    id = serializers.CharField()
    session_date = serializers.DateField()
    arrive_completed = serializers.BooleanField()
    gratitude_1 = serializers.CharField(allow_null=True)
    gratitude_2 = serializers.CharField(allow_null=True)
    gratitude_3 = serializers.CharField(allow_null=True)
    selected_gratitude_index = serializers.IntegerField(allow_null=True)
    selected_gratitude_text = serializers.CharField(allow_null=True)
    deep_dive_1_precise = serializers.CharField(allow_null=True)
    deep_dive_2_why_matters = serializers.CharField(allow_null=True)
    deep_dive_3_who_made_possible = serializers.CharField(allow_null=True)
    deep_dive_4_sensory_moment = serializers.CharField(allow_null=True)
    deep_dive_5_gratitude_line = serializers.CharField(allow_null=True)
    expression_action = serializers.CharField(allow_null=True)
    expression_notes = serializers.CharField(allow_null=True)
    anchor_completed = serializers.BooleanField()
    is_completed = serializers.BooleanField()
    completed_at = serializers.DateTimeField(allow_null=True)
    total_duration_seconds = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    created_at = serializers.DateTimeField()
