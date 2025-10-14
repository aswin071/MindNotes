from rest_framework import serializers


class PromptResponseSerializer(serializers.Serializer):
    """Serializer for submitting prompt responses"""

    prompt_id = serializers.IntegerField(required=True)
    response = serializers.CharField(required=True, min_length=10, max_length=10000)
    time_spent = serializers.IntegerField(required=False, min_value=0)
    mood = serializers.IntegerField(required=False, min_value=1, max_value=5)
    save_as_journal = serializers.BooleanField(required=False, default=True)

    def validate_response(self, value):
        """Ensure response has meaningful content"""
        if not value.strip():
            raise serializers.ValidationError("Response cannot be empty")
        return value.strip()
