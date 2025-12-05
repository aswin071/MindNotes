"""
Management command to seed premium program data:
- Brain Dump categories
- Affirmation templates (optional)
- Clarity prompts (optional)
"""

from django.core.management.base import BaseCommand
from focus.models import BrainDumpCategory


class Command(BaseCommand):
    help = 'Seed premium program reference data (Brain Dump categories, etc.)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting to seed premium program data...'))

        # Seed Brain Dump Categories
        self.seed_brain_dump_categories()

        self.stdout.write(self.style.SUCCESS('Successfully seeded all premium program data!'))

    def seed_brain_dump_categories(self):
        """Seed the 10 Brain Dump categories"""
        self.stdout.write('Seeding Brain Dump categories...')

        categories = [
            {
                'name': 'Actionable Task',
                'icon': '✅',
                'color': '#10B981',  # Green
                'description': 'Something I can do or complete soon',
                'order': 1,
            },
            {
                'name': 'Thought / Reflection',
                'icon': '💭',
                'color': '#8B5CF6',  # Purple
                'description': 'A feeling, idea, or insight worth journaling on',
                'order': 2,
            },
            {
                'name': 'Worry / Anxiety',
                'icon': '⚠️',
                'color': '#F59E0B',  # Amber
                'description': 'Something that\'s mentally heavy or uncertain',
                'order': 3,
            },
            {
                'name': 'Reminder / To-Do Later',
                'icon': '🗓',
                'color': '#3B82F6',  # Blue
                'description': 'Needs to be done, but not urgent today',
                'order': 4,
            },
            {
                'name': 'Personal / Relationship',
                'icon': '❤️',
                'color': '#EC4899',  # Pink
                'description': 'Related to people, emotions, or connections',
                'order': 5,
            },
            {
                'name': 'Work / Career',
                'icon': '💼',
                'color': '#6366F1',  # Indigo
                'description': 'Related to job, projects, or professional goals',
                'order': 6,
            },
            {
                'name': 'Finance / Money',
                'icon': '💰',
                'color': '#059669',  # Emerald
                'description': 'Bills, expenses, or financial concerns',
                'order': 7,
            },
            {
                'name': 'Health / Mind / Body',
                'icon': '🧘‍♂️',
                'color': '#14B8A6',  # Teal
                'description': 'Physical or mental well-being thoughts',
                'order': 8,
            },
            {
                'name': 'Goal / Dream',
                'icon': '🎯',
                'color': '#F97316',  # Orange
                'description': 'Something I want to achieve in the future',
                'order': 9,
            },
            {
                'name': 'Let Go / Not Important',
                'icon': '❌',
                'color': '#6B7280',  # Gray
                'description': 'Doesn\'t need action; release it',
                'order': 10,
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories:
            category, created = BrainDumpCategory.objects.update_or_create(
                name=cat_data['name'],
                defaults={
                    'icon': cat_data['icon'],
                    'color': cat_data['color'],
                    'description': cat_data['description'],
                    'order': cat_data['order'],
                    'is_system': True,
                }
            )

            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {category.name}'))
            else:
                updated_count += 1
                self.stdout.write(f'  → Updated: {category.name}')

        self.stdout.write(self.style.SUCCESS(
            f'Brain Dump categories: {created_count} created, {updated_count} updated'
        ))
