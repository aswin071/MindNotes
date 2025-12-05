from django.core.management.base import BaseCommand
from focus.models import FocusProgram, ProgramDay, ProgramStep


class Command(BaseCommand):
    help = 'Seed the Morning Charge 5-Minute Morning Ritual program'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Morning Charge program...')

        # Create Morning Charge Program
        program, created = FocusProgram.objects.get_or_create(
            program_type='morning_ritual',
            defaults={
                'name': 'Morning Charge',
                'description': 'Your 5-Minute Morning Ritual. Start each day with intention, gratitude, and clarity.',
                'duration_days': 30,
                'objectives': [
                    'Start with Intention - Wake up mindfully with guided breathing and gratitude',
                    'Build Your Momentum - Daily affirmations and clarity prompts to set your focus',
                    'Track Your Progress - Build streaks, unlock badges, and watch your growth'
                ],
                'daily_tasks': [],  # Not used for ritual programs
                'is_pro_only': False,
                'icon': '☀️',
                'color': '#F97316',  # Orange/peach color from UI
                'order': 0  # Show first in list
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {program.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Program already exists: {program.name}'))
            # Update existing program
            program.name = 'Morning Charge'
            program.description = 'Your 5-Minute Morning Ritual. Start each day with intention, gratitude, and clarity.'
            program.objectives = [
                'Start with Intention - Wake up mindfully with guided breathing and gratitude',
                'Build Your Momentum - Daily affirmations and clarity prompts to set your focus',
                'Track Your Progress - Build streaks, unlock badges, and watch your growth'
            ]
            program.icon = '☀️'
            program.color = '#F97316'
            program.order = 0
            program.save()
            self.stdout.write(self.style.SUCCESS(f'Updated: {program.name}'))

        # Create 30 days of content
        for day_num in range(1, 31):
            program_day, day_created = ProgramDay.objects.get_or_create(
                program=program,
                day_number=day_num,
                defaults={
                    'title': self._get_day_title(day_num),
                    'description': self._get_day_description(day_num),
                    'focus_duration': 5,  # 5 minutes
                    'tasks': [],  # Not used for ritual programs
                    'tips': self._get_day_tips(day_num),
                    'reflection_prompts': [],  # Steps handle this instead
                    'is_ritual': True
                }
            )

            if day_created:
                # Create the 4 ritual steps for this day
                self._create_steps_for_day(program_day, day_num)
                self.stdout.write(f'  Created Day {day_num} with 4 steps')
            else:
                # Update existing day
                program_day.title = self._get_day_title(day_num)
                program_day.description = self._get_day_description(day_num)
                program_day.focus_duration = 5
                program_day.tips = self._get_day_tips(day_num)
                program_day.is_ritual = True
                program_day.save()

                # Recreate steps
                program_day.steps.all().delete()
                self._create_steps_for_day(program_day, day_num)
                self.stdout.write(f'  Updated Day {day_num} with 4 steps')

        self.stdout.write(self.style.SUCCESS('Morning Charge program seeded successfully!'))

    def _create_steps_for_day(self, program_day, day_num):
        """Create the 4 ritual steps for a day"""

        # Step 1: Wake & Breathe (Breathing Exercise)
        ProgramStep.objects.create(
            program_day=program_day,
            order=1,
            step_type='breathing',
            title='Wake & Breathe',
            description='Take your first intentional breath of the day',
            subtitle='Begin with a calming breath exercise',
            duration_seconds=60,
            input_type='none',
            config={
                'animation': 'breathing_circle',
                'inhale_seconds': 4,
                'hold_seconds': 4,
                'exhale_seconds': 4,
                'cycles': 3,
                'guidance_text': [
                    'Breathe in slowly...',
                    'Hold...',
                    'Breathe out slowly...'
                ]
            },
            icon='💨',
            color='#10B981',  # Green
            background_color='#D1FAE5',
            is_required=True,
            is_skippable=False
        )

        # Step 2: Gratitude Spark
        ProgramStep.objects.create(
            program_day=program_day,
            order=2,
            step_type='gratitude',
            title='Gratitude Spark',
            description="Write one thing you're grateful for today",
            subtitle='Start your day with appreciation',
            duration_seconds=60,
            input_type='text_voice',
            placeholder_text="I'm grateful for...",
            config={
                'allow_voice': True,
                'min_length': 3,
                'max_length': 500,
                'show_previous_entries': True
            },
            icon='❤️',
            color='#EC4899',  # Pink
            background_color='#FCE7F3',
            is_required=True,
            is_skippable=False
        )

        # Step 3: Positive Affirmation
        ProgramStep.objects.create(
            program_day=program_day,
            order=3,
            step_type='affirmation',
            title='Positive Affirmation',
            description='Choose your daily affirmation',
            subtitle='Select the affirmation that resonates with you today',
            duration_seconds=60,
            input_type='single_choice',
            choices=self._get_affirmations_for_day(day_num),
            config={
                'allow_custom': True,
                'custom_placeholder': 'Write your own affirmation...',
                'show_selected_animation': True,
                'save_favorites': True,
                'daily_repetition': True
            },
            icon='✨',
            color='#8B5CF6',  # Purple
            background_color='#EDE9FE',
            is_required=True,
            is_skippable=False
        )

        # Step 4: Daily Clarity Prompt
        ProgramStep.objects.create(
            program_day=program_day,
            order=4,
            step_type='prompt',
            title='Daily Clarity',
            description="Set your intention for the day",
            subtitle=self._get_clarity_prompt(day_num),
            duration_seconds=90,
            input_type='text',
            placeholder_text='Today will be great if I...',
            prompts=self._get_clarity_prompts_rotation(day_num),
            config={
                'rotating_prompts': True,
                'show_alternative_prompt': True,
                'min_length': 5,
                'max_length': 500
            },
            icon='💡',
            color='#F97316',  # Orange
            background_color='#FEF3C7',
            is_required=True,
            is_skippable=False
        )

    def _get_day_title(self, day_num):
        """Get motivational title for each day"""
        if day_num == 1:
            return 'Your First Morning Charge'
        elif day_num == 7:
            return 'One Week Strong!'
        elif day_num == 14:
            return 'Two Weeks of Growth'
        elif day_num == 21:
            return 'Habit Formed!'
        elif day_num == 30:
            return 'Morning Master!'
        else:
            return f'Day {day_num} - Rise & Shine'

    def _get_day_description(self, day_num):
        """Get description for each day"""
        descriptions = {
            1: "Welcome to Morning Charge! Let's start your journey to intentional mornings.",
            7: "You've completed a full week! Your morning routine is taking shape.",
            14: "Two weeks of consistent mornings. You're building real momentum.",
            21: "They say it takes 21 days to form a habit. You've made it!",
            30: "Congratulations! You've completed the Morning Charge program.",
        }
        return descriptions.get(day_num, "Another beautiful morning to set your intentions and embrace the day ahead.")

    def _get_day_tips(self, day_num):
        """Get tips for each day"""
        tips_rotation = [
            [
                'Keep your phone away from bed',
                'Have water ready by your bedside',
                'Wake up at a consistent time'
            ],
            [
                'Open curtains to let natural light in',
                'Avoid checking emails first thing',
                'Take 3 deep breaths before getting up'
            ],
            [
                'Stretch gently before starting',
                'Keep a gratitude journal nearby',
                'Set a gentle alarm tone'
            ],
            [
                'Prepare your space the night before',
                'Make your bed after waking',
                'Smile when you first wake up'
            ],
            [
                'Visualize your successful day',
                'Focus on one priority at a time',
                'Celebrate small wins'
            ]
        ]
        return tips_rotation[(day_num - 1) % len(tips_rotation)]

    def _get_affirmations_for_day(self, day_num):
        """Get affirmation choices that rotate throughout the program"""
        affirmation_sets = [
            [
                'I am focused, calm, and ready to grow today',
                'I embrace today with gratitude and purpose',
                'I am capable of achieving my goals'
            ],
            [
                'Today I choose joy and positivity',
                'I am worthy of good things happening to me',
                'I trust myself to make good decisions'
            ],
            [
                'I am becoming the best version of myself',
                'I attract abundance and success',
                'I am resilient and can handle any challenge'
            ],
            [
                'I release what no longer serves me',
                'I am grateful for this new day',
                'I choose to focus on what I can control'
            ],
            [
                'I am enough exactly as I am',
                'I welcome new opportunities with open arms',
                'I create my own happiness'
            ],
            [
                'I am surrounded by love and support',
                'I trust the journey of my life',
                'I am making progress every single day'
            ],
            [
                'I radiate confidence and positivity',
                'I am open to learning and growth',
                'I deserve success and happiness'
            ]
        ]
        return affirmation_sets[(day_num - 1) % len(affirmation_sets)]

    def _get_clarity_prompt(self, day_num):
        """Get the main clarity prompt for the day"""
        prompts = [
            "What's the one thing that will make today great?",
            "What will you focus on today?",
            "What's your most important task for today?",
            "How will you show up for yourself today?",
            "What positive impact will you make today?",
            "What are you looking forward to today?",
            "What challenge will you embrace today?",
        ]
        return prompts[(day_num - 1) % len(prompts)]

    def _get_clarity_prompts_rotation(self, day_num):
        """Get alternative prompts for rotation"""
        return [
            "What's the one thing that will make today great?",
            "What will you focus on today?",
            "What's your most important task for today?",
            "How will you show up for yourself today?",
            "What positive impact will you make today?",
            "What are you looking forward to today?",
            "What challenge will you embrace today?",
            "What intention do you set for today?",
            "What would make you proud at the end of today?",
            "How will you practice self-care today?"
        ]
