from authentication.models import *
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.conf import settings

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    class Meta:
        model = UserProfile
        fields = [
            'default_entry_privacy', 'default_focus_duration', 'focus_sound_enabled',
            'mood_tracking_enabled', 'total_entries', 'current_streak', 'longest_streak',
            'total_focus_minutes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['total_entries', 'current_streak', 'longest_streak', 'total_focus_minutes']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    profile = UserProfileSerializer(read_only=True)
    is_pro = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'full_name', 'phone_number', 'avatar', 'bio', 'dob', 'gender',
            'timezone', 'language', 'email_notifications', 'push_notifications',
            'daily_reminder', 'reminder_time', 'is_verified', 'onboarding_completed',
            'onboarding_step', 'created_at', 'last_login_at', 'profile', 'is_pro'
        ]
        read_only_fields = ['id', 'is_verified', 'created_at', 'last_login_at']
    
    def get_is_pro(self, obj):
        """Check if user has active pro subscription"""
        if hasattr(obj, 'subscription'):
            return obj.subscription.is_pro()
        return False


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration with onboarding fields (single password field)"""
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    onboarding_answers = serializers.DictField(required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.ChoiceField(required=False, choices=User.GENDER_CHOICES)

    class Meta:
        model = User
        fields = ['email', 'password', 'full_name', 'dob', 'gender', 'onboarding_answers']
    
    def validate(self, attrs):
        # Additional custom validations can go here
        return attrs
    
    def create(self, validated_data):
        onboarding_answers = validated_data.pop('onboarding_answers', {})
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data.get('full_name', ''),
            dob=validated_data.get('dob'),
            gender=validated_data.get('gender', ''),
        )
        # Create user profile
        profile = UserProfile.objects.create(user=user)
        if onboarding_answers:
            profile.onboarding_answers = onboarding_answers
            profile.save(update_fields=['onboarding_answers'])
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials.')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
        else:
            raise serializers.ValidationError('Must include email and password.')
        
        attrs['user'] = user
        return attrs


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for changing password (single new_password field)"""
    
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
    
    def validate(self, attrs):
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for confirming password reset"""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords don't match."})
        return attrs


class UserStreakSerializer(serializers.ModelSerializer):
    """Serializer for user streaks"""
    
    class Meta:
        model = UserStreak
        fields = ['date', 'has_entry']


class UserDeviceSerializer(serializers.ModelSerializer):
    """Serializer for user devices"""
    
    class Meta:
        model = UserDevice
        fields = ['id', 'device_type', 'device_token', 'device_name', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'full_name', 'phone_number', 'avatar', 'bio', 'dob', 'gender', 'timezone', 'language',
            'email_notifications', 'push_notifications', 'daily_reminder', 'reminder_time'
        ]


class GoogleAuthSerializer(serializers.Serializer):
    """Validate Google ID token and return user info."""
    id_token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token_str = attrs.get('id_token')
        if not token_str:
            raise serializers.ValidationError('id_token is required')
        try:
            # Verify the integrity of the token and its audience
            idinfo = id_token.verify_oauth2_token(
                token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID or None,
            )
            if idinfo.get('iss') not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Invalid issuer')
        except Exception as exc:
            raise serializers.ValidationError(f'Invalid Google token: {exc}')

        email = idinfo.get('email')
        email_verified = idinfo.get('email_verified', False)
        full_name = idinfo.get('name') or ''
        picture = idinfo.get('picture')

        if not email or not email_verified:
            raise serializers.ValidationError('Email not verified with Google')

        attrs['google'] = {
            'email': email,
            'full_name': full_name,
            'picture': picture,
            'sub': idinfo.get('sub'),
        }
        return attrs


class SignupWithGoogleSerializer(GoogleAuthSerializer):
    """Google signup that also accepts onboarding fields"""
    onboarding_answers = serializers.DictField(required=False)
    dob = serializers.DateField(required=False)
    gender = serializers.ChoiceField(required=False, choices=User.GENDER_CHOICES)