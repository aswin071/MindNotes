from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Tag

User = get_user_model()


# Predefined system tags that are auto-created for each new user
PREDEFINED_TAGS = [
    # Emotions & Feelings
    {'name': 'Grateful', 'color': '#10B981'},
    {'name': 'Happy', 'color': '#F59E0B'},
    {'name': 'Sad', 'color': '#6366F1'},
    {'name': 'Anxious', 'color': '#8B5CF6'},
    {'name': 'Excited', 'color': '#EC4899'},
    {'name': 'Calm', 'color': '#06B6D4'},
    {'name': 'Stressed', 'color': '#EF4444'},

    # Life Categories
    {'name': 'Work', 'color': '#3B82F6'},
    {'name': 'Personal', 'color': '#8B5CF6'},
    {'name': 'Family', 'color': '#EC4899'},
    {'name': 'Health', 'color': '#10B981'},
    {'name': 'Travel', 'color': '#06B6D4'},
    {'name': 'Learning', 'color': '#8B5CF6'},

    # Activities
    {'name': 'Achievement', 'color': '#10B981'},
    {'name': 'Goal', 'color': '#F59E0B'},
    {'name': 'Reflection', 'color': '#6366F1'},
    {'name': 'Dream', 'color': '#EC4899'},
    {'name': 'Idea', 'color': '#FBBF24'},

    # Well-being
    {'name': 'Meditation', 'color': '#8B5CF6'},
    {'name': 'Gratitude', 'color': '#10B981'},

    # Special
    {'name': 'Important', 'color': '#EF4444'},
]


@receiver(post_save, sender=User)
def create_default_tags(sender, instance, created, **kwargs):
    """
    Automatically create predefined tags when a new user registers.
    This ensures tags are immediately available for journal creation.
    """
    if created:
        # Bulk create tags for better performance
        tags_to_create = [
            Tag(
                user=instance,
                name=tag_data['name'],
                color=tag_data['color']
            )
            for tag_data in PREDEFINED_TAGS
        ]

        Tag.objects.bulk_create(tags_to_create, ignore_conflicts=True)
