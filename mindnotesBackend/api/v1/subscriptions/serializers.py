from rest_framework import serializers
from subscriptions.models import Subscription, SubscriptionFeature, PaymentHistory


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscription information"""

    plan_display_name = serializers.CharField(source='get_plan_display_name', read_only=True)
    is_pro = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id', 'plan', 'plan_display_name', 'status', 'is_pro',
            'started_at', 'expires_at', 'canceled_at',
            'trial_started_at', 'trial_ends_at',
            'current_period_start', 'current_period_end',
            'auto_renew', 'days_until_expiry',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_is_pro(self, obj):
        return obj.is_pro()

    def get_days_until_expiry(self, obj):
        return obj.days_until_expiry()


class SubscriptionFeatureSerializer(serializers.ModelSerializer):
    """Serializer for subscription features"""

    class Meta:
        model = SubscriptionFeature
        fields = ['id', 'plan', 'feature_key', 'feature_name', 'feature_value', 'is_enabled']


class PaymentHistorySerializer(serializers.ModelSerializer):
    """Serializer for payment history"""

    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'amount', 'currency', 'status',
            'description', 'invoice_url', 'receipt_url',
            'paid_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ProfileStatsSerializer(serializers.Serializer):
    """
    Serializer for Profile screen data
    Aggregates data from multiple sources (PostgreSQL + MongoDB)
    """

    # User Info
    user_id = serializers.UUIDField(read_only=True)
    email = serializers.EmailField(read_only=True)
    full_name = serializers.CharField(read_only=True)
    avatar = serializers.URLField(read_only=True, allow_null=True)
    bio = serializers.CharField(read_only=True, allow_blank=True)

    # Statistics - From MongoDB & PostgreSQL
    total_entries = serializers.IntegerField(read_only=True)
    current_streak = serializers.IntegerField(read_only=True)
    longest_streak = serializers.IntegerField(read_only=True)
    total_focus_minutes = serializers.IntegerField(read_only=True)
    days_using_app = serializers.IntegerField(read_only=True)

    # Subscription Info
    is_pro = serializers.BooleanField(read_only=True)
    subscription_plan = serializers.CharField(read_only=True)
    subscription_status = serializers.CharField(read_only=True)
    subscription_expires_at = serializers.DateTimeField(read_only=True, allow_null=True)

    # Preferences
    timezone = serializers.CharField(read_only=True)
    language = serializers.CharField(read_only=True)
    daily_reminder = serializers.BooleanField(read_only=True)
    reminder_time = serializers.CharField(read_only=True, allow_null=True)
    email_notifications = serializers.BooleanField(read_only=True)
    push_notifications = serializers.BooleanField(read_only=True)

    # Profile Settings
    default_entry_privacy = serializers.CharField(read_only=True)
    default_focus_duration = serializers.IntegerField(read_only=True)
    mood_tracking_enabled = serializers.BooleanField(read_only=True)

    # Account Info
    is_verified = serializers.BooleanField(read_only=True)
    onboarding_completed = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    last_login_at = serializers.DateTimeField(read_only=True, allow_null=True)
