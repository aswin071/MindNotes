from rest_framework import serializers
from journals.models import Tag
from datetime import datetime


class TagSerializer(serializers.ModelSerializer):
    """Serializer for tags (PostgreSQL)"""
    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


# ============ JOURNAL ENTRY SERIALIZERS (MongoDB) ============

class PhotoEmbedSerializer(serializers.Serializer):
    """Serializer for embedded photo data"""
    # image_file = serializers.ImageField(required=False, write_only=True)
    image_url = serializers.ImageField(
        required=False,
        help_text="URL of uploaded image",
        max_length=None,  # No URL length limit
    )
    caption = serializers.CharField(max_length=255, required=False, allow_blank=True)
    order = serializers.IntegerField(default=0)
    width = serializers.IntegerField(required=False, allow_null=True)
    height = serializers.IntegerField(required=False, allow_null=True)
    file_size = serializers.IntegerField(required=False, allow_null=True)

    def validate_image_url(self, value):
        """Validate image file size and type"""
        if hasattr(value, 'size'):
            # File size limits
            MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
            MIN_IMAGE_SIZE = 1024  # 1KB

            if value.size > MAX_IMAGE_SIZE:
                raise serializers.ValidationError(
                    f'Image file too large. Max size is {MAX_IMAGE_SIZE / (1024 * 1024):.1f}MB'
                )

            if value.size < MIN_IMAGE_SIZE:
                raise serializers.ValidationError(
                    f'Image file too small. Min size is {MIN_IMAGE_SIZE / 1024:.1f}KB'
                )

            # Validate image type
            ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp', 'image/heic']
            if hasattr(value, 'content_type'):
                if value.content_type not in ALLOWED_IMAGE_TYPES:
                    raise serializers.ValidationError(
                        'Invalid image type. Allowed types: JPEG, PNG, WebP, HEIC'
                    )

        return value


class VoiceNoteEmbedSerializer(serializers.Serializer):
    """Serializer for embedded voice note data"""
    audio_url = serializers.URLField(required=True, help_text="URL of uploaded audio file")
    duration = serializers.IntegerField(required=False, allow_null=True, help_text="Duration in seconds")
    file_size = serializers.IntegerField(required=False, allow_null=True)
    transcription = serializers.CharField(required=False, allow_blank=True)
    transcription_language = serializers.CharField(default='en', max_length=10)
    is_transcribed = serializers.BooleanField(default=False)

    def validate_audio_url(self, value):
        """Validate audio file size and type"""
        if hasattr(value, 'size'):
            # File size limits for audio
            MAX_AUDIO_SIZE = 50 * 1024 * 1024  # 50MB
            MIN_AUDIO_SIZE = 1024  # 1KB

            if value.size > MAX_AUDIO_SIZE:
                raise serializers.ValidationError(
                    f'Audio file too large. Max size is {MAX_AUDIO_SIZE / (1024 * 1024):.1f}MB'
                )

            if value.size < MIN_AUDIO_SIZE:
                raise serializers.ValidationError(
                    f'Audio file too small. Min size is {MIN_AUDIO_SIZE / 1024:.1f}KB'
                )

            # Validate audio type
            ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 'audio/webm', 'audio/ogg']
            if hasattr(value, 'content_type'):
                if value.content_type not in ALLOWED_AUDIO_TYPES:
                    raise serializers.ValidationError(
                        'Invalid audio type. Allowed types: MP3, WAV, M4A, WebM, OGG'
                    )

        return value


class PromptResponseEmbedSerializer(serializers.Serializer):
    """Serializer for prompt response in journal entry"""
    prompt_id = serializers.IntegerField(required=True)
    question = serializers.CharField(required=True)
    answer = serializers.CharField(required=True)


class JournalEntryCreateSerializer(serializers.Serializer):
    """
    Serializer for creating journal entries in MongoDB
    Supports all entry types: text, voice, photo, mixed
    """
    # Core fields
    title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Entry title (optional)"
    )
    content = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Entry text content"
    )
    entry_type = serializers.ChoiceField(
        choices=['text', 'voice', 'photo', 'mixed'],
        default='text',
        help_text="Type of entry"
    )

    # Metadata
    entry_date = serializers.DateTimeField(
        required=False,
        help_text="Entry date (defaults to now, can backdate)"
    )
    privacy = serializers.ChoiceField(
        choices=['private', 'public'],
        default='private'
    )
    is_favorite = serializers.BooleanField(default=False)

    # Tags (stored as IDs in MongoDB, but accept names here)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of tag IDs from PostgreSQL"
    )
    tag_names = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="List of tag names (will auto-create if not exist)"
    )

    # Location
    location_name = serializers.CharField(max_length=255, required=False, allow_blank=True)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True)

    # Weather
    weather = serializers.CharField(max_length=50, required=False, allow_blank=True)
    temperature = serializers.FloatField(required=False, allow_null=True)

    # Embedded documents
    photos = PhotoEmbedSerializer(many=True, required=False)
    voice_notes = VoiceNoteEmbedSerializer(many=True, required=False)
    prompt_responses = PromptResponseEmbedSerializer(many=True, required=False)

    def validate(self, data):
        """Validate journal entry data"""
        entry_type = data.get('entry_type', 'text')

        # Validate based on entry type
        if entry_type == 'text':
            if not data.get('content') and not data.get('prompt_responses'):
                raise serializers.ValidationError({
                    'content': 'Text entries must have content or prompt responses'
                })

        elif entry_type == 'voice':
            if not data.get('voice_notes'):
                raise serializers.ValidationError({
                    'voice_notes': 'Voice entries must have at least one voice note'
                })

        elif entry_type == 'photo':
            if not data.get('photos'):
                raise serializers.ValidationError({
                    'photos': 'Photo entries must have at least one photo'
                })

        # Set default entry_date if not provided
        if 'entry_date' not in data:
            data['entry_date'] = datetime.utcnow()

        return data

    def validate_tag_names(self, value):
        """Validate tag names"""
        if value:
            for tag_name in value:
                if len(tag_name) > 50:
                    raise serializers.ValidationError(f'Tag name "{tag_name}" is too long (max 50 characters)')
        return value


class JournalEntryResponseSerializer(serializers.Serializer):
    """Serializer for journal entry response"""
    id = serializers.CharField(read_only=True)
    user_id = serializers.UUIDField(read_only=True)

    # Core fields
    title = serializers.CharField()
    content = serializers.CharField()
    entry_type = serializers.CharField()

    # Metadata
    entry_date = serializers.DateTimeField()
    privacy = serializers.CharField()
    is_favorite = serializers.BooleanField()
    is_archived = serializers.BooleanField()

    # Tags
    tag_ids = serializers.ListField(child=serializers.IntegerField())
    tags = TagSerializer(many=True, read_only=True)

    # Location
    location_name = serializers.CharField()
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6, allow_null=True)

    # Weather
    weather = serializers.CharField()
    temperature = serializers.FloatField(allow_null=True)

    # Statistics
    word_count = serializers.IntegerField()
    character_count = serializers.IntegerField()
    reading_time_minutes = serializers.IntegerField()

    # Embedded documents
    photos = PhotoEmbedSerializer(many=True)
    voice_notes = VoiceNoteEmbedSerializer(many=True)
    prompt_responses = PromptResponseEmbedSerializer(many=True)

    # Timestamps
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class QuickJournalSerializer(serializers.Serializer):
    """
    Simplified serializer for quick journal entries from Home screen
    (Voice, Speak, Photo quick actions)
    """
    content = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Quick journal content"
    )
    entry_type = serializers.ChoiceField(
        choices=['text', 'voice', 'photo'],
        required=True,
        help_text="Quick entry type: voice, text (speak), or photo"
    )

    # For voice entries
    audio_url = serializers.URLField(
        required=False,
        help_text="URL of voice recording (for voice type)"
    )
    audio_duration = serializers.IntegerField(required=False)

    # For photo entries
    photo_url = serializers.URLField(
        required=False,
        help_text="URL of photo (for photo type)"
    )
    photo_caption = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255
    )

    def validate(self, data):
        """Validate quick journal based on type"""
        entry_type = data.get('entry_type')

        if entry_type == 'voice':
            if not data.get('audio_url'):
                raise serializers.ValidationError({
                    'audio_url': 'Voice entries require audio_url'
                })

        elif entry_type == 'photo':
            if not data.get('photo_url'):
                raise serializers.ValidationError({
                    'photo_url': 'Photo entries require photo_url'
                })

        elif entry_type == 'text':
            if not data.get('content'):
                raise serializers.ValidationError({
                    'content': 'Text entries require content'
                })

        return data



