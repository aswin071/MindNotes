from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from journals.models import Tag

User = get_user_model()


class Command(BaseCommand):
    help = 'Seeds predefined tags for all users or a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of specific user to seed tags for (optional)',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Seed tags for all existing users',
        )

    def handle(self, *args, **options):
        # Predefined tags with categories
        predefined_tags = [
            # Emotions & Feelings
            {'name': 'Grateful', 'color': '#10B981'},  # Green
            {'name': 'Happy', 'color': '#F59E0B'},  # Amber
            {'name': 'Sad', 'color': '#6366F1'},  # Indigo
            {'name': 'Anxious', 'color': '#8B5CF6'},  # Purple
            {'name': 'Excited', 'color': '#EC4899'},  # Pink
            {'name': 'Calm', 'color': '#06B6D4'},  # Cyan
            {'name': 'Stressed', 'color': '#EF4444'},  # Red
            {'name': 'Inspired', 'color': '#FBBF24'},  # Yellow
            {'name': 'Lonely', 'color': '#6B7280'},  # Gray
            {'name': 'Confident', 'color': '#14B8A6'},  # Teal

            # Life Categories
            {'name': 'Work', 'color': '#3B82F6'},  # Blue
            {'name': 'Personal', 'color': '#8B5CF6'},  # Purple
            {'name': 'Family', 'color': '#EC4899'},  # Pink
            {'name': 'Relationships', 'color': '#EF4444'},  # Red
            {'name': 'Health', 'color': '#10B981'},  # Green
            {'name': 'Fitness', 'color': '#14B8A6'},  # Teal
            {'name': 'Travel', 'color': '#06B6D4'},  # Cyan
            {'name': 'Hobby', 'color': '#F59E0B'},  # Amber
            {'name': 'Learning', 'color': '#8B5CF6'},  # Purple
            {'name': 'Finance', 'color': '#10B981'},  # Green

            # Activities & Events
            {'name': 'Meeting', 'color': '#3B82F6'},  # Blue
            {'name': 'Achievement', 'color': '#10B981'},  # Green
            {'name': 'Goal', 'color': '#F59E0B'},  # Amber
            {'name': 'Challenge', 'color': '#EF4444'},  # Red
            {'name': 'Milestone', 'color': '#8B5CF6'},  # Purple
            {'name': 'Reflection', 'color': '#6366F1'},  # Indigo
            {'name': 'Dream', 'color': '#EC4899'},  # Pink
            {'name': 'Memory', 'color': '#06B6D4'},  # Cyan
            {'name': 'Idea', 'color': '#FBBF24'},  # Yellow
            {'name': 'Project', 'color': '#14B8A6'},  # Teal

            # Well-being & Self-care
            {'name': 'Meditation', 'color': '#8B5CF6'},  # Purple
            {'name': 'Self-care', 'color': '#EC4899'},  # Pink
            {'name': 'Gratitude', 'color': '#10B981'},  # Green
            {'name': 'Mindfulness', 'color': '#06B6D4'},  # Cyan
            {'name': 'Therapy', 'color': '#6366F1'},  # Indigo

            # Special
            {'name': 'Important', 'color': '#EF4444'},  # Red
            {'name': 'Review', 'color': '#F59E0B'},  # Amber
            {'name': 'Planning', 'color': '#3B82F6'},  # Blue
            {'name': 'Question', 'color': '#8B5CF6'},  # Purple
            {'name': 'Breakthrough', 'color': '#10B981'},  # Green
        ]

        users_to_seed = []

        # Determine which users to seed
        if options['user_email']:
            try:
                user = User.objects.get(email=options['user_email'])
                users_to_seed = [user]
                self.stdout.write(f"Seeding tags for user: {user.email}")
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"User with email '{options['user_email']}' not found")
                )
                return
        elif options['all_users']:
            users_to_seed = User.objects.all()
            self.stdout.write(f"Seeding tags for {users_to_seed.count()} users")
        else:
            self.stdout.write(
                self.style.ERROR('Please specify either --user-email or --all-users')
            )
            return

        # Seed tags for selected users
        total_created = 0
        total_skipped = 0

        for user in users_to_seed:
            self.stdout.write(f"\nProcessing user: {user.email}")

            for tag_data in predefined_tags:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_data['name'],
                    defaults={'color': tag_data['color']}
                )

                if created:
                    total_created += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"  ✓ Created tag: {tag_data['name']}")
                    )
                else:
                    total_skipped += 1
                    self.stdout.write(
                        self.style.WARNING(f"  - Skipped (exists): {tag_data['name']}")
                    )

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write(
            self.style.SUCCESS(
                f"\nSeeding completed!\n"
                f"Total tags created: {total_created}\n"
                f"Total tags skipped: {total_skipped}\n"
                f"Users processed: {len(users_to_seed)}"
            )
        )


#python manage.py seed_tags --all-users
