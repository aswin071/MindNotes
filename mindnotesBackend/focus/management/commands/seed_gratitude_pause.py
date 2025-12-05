from django.core.management.base import BaseCommand
from focus.models import FocusProgram, ProgramDay, ProgramStep


class Command(BaseCommand):
    help = 'Seed the Gratitude Pause 5-Minute Deep Gratitude program'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Gratitude Pause program...')

        # Create Gratitude Pause Program
        program, created = FocusProgram.objects.get_or_create(
            program_type='gratitude',
            defaults={
                'name': 'Gratitude Pause',
                'description': 'Fill your mind with positivity in 5 minutes. Practice deep gratitude to activate dopamine and serotonin pathways.',
                'duration_days': 30,
                'objectives': [
                    'Cultivate Gratitude - Notice and appreciate the good in your life',
                    'Deepen Awareness - Explore why things matter to you',
                    'Express Thanks - Take action on your gratitude',
                    'Build Positivity - Develop a daily gratitude practice'
                ],
                'daily_tasks': [],  # Not used for ritual programs
                'is_pro_only': False,
                'icon': '🌼',
                'color': '#EC4899',  # Pink
                'order': 2
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {program.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Program already exists: {program.name}'))
            # Update existing program
            program.name = 'Gratitude Pause'
            program.description = 'Fill your mind with positivity in 5 minutes. Practice deep gratitude to activate dopamine and serotonin pathways.'
            program.objectives = [
                'Cultivate Gratitude - Notice and appreciate the good in your life',
                'Deepen Awareness - Explore why things matter to you',
                'Express Thanks - Take action on your gratitude',
                'Build Positivity - Develop a daily gratitude practice'
            ]
            program.icon = '🌼'
            program.color = '#EC4899'
            program.order = 2
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
                # Create the 5 ritual steps for this day
                self._create_steps_for_day(program_day, day_num)
                self.stdout.write(f'  Created Day {day_num} with 5 steps')
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
                self.stdout.write(f'  Updated Day {day_num} with 5 steps')

        self.stdout.write(self.style.SUCCESS('Gratitude Pause program seeded successfully!'))

    def _create_steps_for_day(self, program_day, day_num):
        """Create the 5 ritual steps for a day"""

        # Step 1: Arrive - One Calm Breath (30 seconds)
        ProgramStep.objects.create(
            program_day=program_day,
            order=1,
            step_type='breathing',
            title='Arrive',
            description='One calm breath. Let\'s notice what\'s good.',
            subtitle='Begin with presence',
            duration_seconds=30,
            input_type='none',
            config={
                'animation': 'breathing_circle',
                'inhale_seconds': 4,
                'hold_seconds': 2,
                'exhale_seconds': 4,
                'cycles': 2,
                'guidance_text': [
                    'Breathe in peace...',
                    'Hold gently...',
                    'Breathe out tension...'
                ]
            },
            icon='🌸',
            color='#EC4899',  # Pink
            background_color='#FCE7F3',
            is_required=True,
            is_skippable=False
        )

        # Step 2: List Three Gratitudes (90 seconds)
        ProgramStep.objects.create(
            program_day=program_day,
            order=2,
            step_type='gratitude',
            title='Three Gratitudes',
            description='List three things you\'re grateful for in life right now.',
            subtitle='Voice or type your gratitudes',
            duration_seconds=90,
            input_type='text_voice',
            placeholder_text='1. I\'m grateful for...\n2. I\'m grateful for...\n3. I\'m grateful for...',
            prompts=self._get_gratitude_hints(day_num),
            config={
                'allow_voice': True,
                'entry_count': 3,
                'show_hints_after_idle_seconds': 10,
                'hint_examples': self._get_gratitude_hints(day_num),
                'save_to_journal': True
            },
            icon='❤️',
            color='#EF4444',  # Red
            background_color='#FEE2E2',
            is_required=True,
            is_skippable=False
        )

        # Step 3: Deep Dive on One (135 seconds / 2:15)
        ProgramStep.objects.create(
            program_day=program_day,
            order=3,
            step_type='prompt',
            title='Deep Dive',
            description='Tap one of your gratitudes to explore it deeply.',
            subtitle='Answer 5 quick prompts (~25s each)',
            duration_seconds=135,
            input_type='text',
            placeholder_text='Reflect deeply...',
            prompts=self._get_deep_dive_prompts(),
            config={
                'select_from_previous_step': True,  # User taps one of their 3 gratitudes
                'prompt_sequence': [
                    {
                        'id': 'name_it',
                        'title': 'Name it precisely',
                        'prompt': 'What exactly are you grateful for? One sentence.',
                        'duration_seconds': 25
                    },
                    {
                        'id': 'why_matters',
                        'title': 'Why it matters (today)',
                        'prompt': 'How did this help your day, mood, or stress?',
                        'duration_seconds': 25
                    },
                    {
                        'id': 'who_what',
                        'title': 'Who/what made it possible',
                        'prompt': 'Is there a person or factor to appreciate?',
                        'duration_seconds': 25
                    },
                    {
                        'id': 'replay',
                        'title': 'Replay a moment (sensory)',
                        'prompt': 'Close eyes: what did you see/hear/feel?',
                        'duration_seconds': 25
                    },
                    {
                        'id': 'gratitude_line',
                        'title': 'Gratitude line',
                        'prompt': 'Complete: I\'m grateful for ___ because ___.',
                        'duration_seconds': 35,
                        'save_as_quote': True
                    }
                ],
                'show_progress_dots': True
            },
            icon='🔍',
            color='#8B5CF6',  # Purple
            background_color='#EDE9FE',
            is_required=True,
            is_skippable=False
        )

        # Step 4: Express It Now (30 seconds)
        ProgramStep.objects.create(
            program_day=program_day,
            order=4,
            step_type='task',
            title='Express It Now',
            description='Choose one quick action to express your gratitude.',
            subtitle='Take a small step of kindness',
            duration_seconds=30,
            input_type='single_choice',
            choices=self._get_expression_actions(),
            config={
                'show_done_animation': True,
                'track_action_taken': True,
                'allow_custom': True,
                'custom_placeholder': 'My own way to express thanks...'
            },
            icon='💌',
            color='#10B981',  # Green
            background_color='#D1FAE5',
            is_required=True,
            is_skippable=True
        )

        # Step 5: Anchor - Final Breath (15 seconds)
        ProgramStep.objects.create(
            program_day=program_day,
            order=5,
            step_type='breathing',
            title='Anchor',
            description='Inhale gratitude, exhale tension.',
            subtitle='Carry this feeling with you',
            duration_seconds=15,
            input_type='none',
            config={
                'animation': 'breathing_circle',
                'inhale_seconds': 4,
                'hold_seconds': 0,
                'exhale_seconds': 4,
                'cycles': 1,
                'show_summary': True,
                'summary_template': 'You practiced gratitude for {gratitude_count} things and explored one deeply. 🌼',
                'play_chime': True,
                'save_quote_card': True
            },
            icon='✨',
            color='#F59E0B',  # Amber
            background_color='#FEF3C7',
            is_required=True,
            is_skippable=False
        )

    def _get_expression_actions(self):
        """Get the expression action choices"""
        return [
            {'id': 'text', 'label': 'Send a thank-you text', 'icon': '📱'},
            {'id': 'note', 'label': 'Leave a kind note', 'icon': '📝'},
            {'id': 'help', 'label': 'Do a tiny helpful act', 'icon': '🤝'},
            {'id': 'reminder', 'label': 'Set reminder to say thanks later', 'icon': '⏰'},
            {'id': 'silent', 'label': 'Send silent thanks in my heart', 'icon': '💗'}
        ]

    def _get_deep_dive_prompts(self):
        """Get the 5 deep dive prompts"""
        return [
            'What exactly are you grateful for? One sentence.',
            'How did this help your day, mood, or stress?',
            'Is there a person or factor to appreciate?',
            'Close eyes: what did you see/hear/feel?',
            'Complete: I\'m grateful for ___ because ___.'
        ]

    def _get_day_title(self, day_num):
        """Get motivational title for each day"""
        if day_num == 1:
            return 'Your First Gratitude Pause'
        elif day_num == 7:
            return 'One Week of Gratitude!'
        elif day_num == 14:
            return 'Two Weeks of Positivity'
        elif day_num == 21:
            return 'Gratitude Habit Formed!'
        elif day_num == 30:
            return 'Gratitude Master!'
        else:
            return f'Day {day_num} - Notice the Good'

    def _get_day_description(self, day_num):
        """Get description for each day"""
        descriptions = {
            1: 'Welcome to Gratitude Pause! Let\'s fill your mind with positivity.',
            7: 'You\'ve completed a full week of gratitude. Notice how your perspective is shifting!',
            14: 'Two weeks of noticing the good. Your brain is rewiring for happiness.',
            21: 'They say it takes 21 days to form a habit. Gratitude is now part of who you are!',
            30: 'Congratulations! You\'ve mastered the art of gratitude.',
        }
        return descriptions.get(day_num, 'Another moment to pause and appreciate the beauty in your life.')

    def _get_day_tips(self, day_num):
        """Get tips for each day"""
        tips_rotation = [
            [
                'Start with the simplest things',
                'Notice what you usually overlook',
                'Gratitude grows with practice'
            ],
            [
                'Include people, moments, and things',
                'Be specific — details matter',
                'Feel the emotion, not just the words'
            ],
            [
                'Look for silver linings in challenges',
                'Express your thanks out loud',
                'Share your gratitude with someone'
            ],
            [
                'Review your gratitude journal',
                'Notice patterns in what you appreciate',
                'Let gratitude guide your decisions'
            ],
            [
                'Practice gratitude even on hard days',
                'Thank yourself for your efforts',
                'Spread gratitude to others'
            ]
        ]
        return tips_rotation[(day_num - 1) % len(tips_rotation)]

    def _get_gratitude_hints(self, day_num):
        """Get gratitude hint examples that rotate throughout the program"""
        hint_sets = [
            ['a kind message', 'morning coffee', 'a quiet moment'],
            ['a good night\'s sleep', 'a helpful friend', 'delicious food'],
            ['sunshine', 'music that moved you', 'a completed task'],
            ['your health', 'a loved one', 'a roof over your head'],
            ['a learning experience', 'nature around you', 'your own resilience'],
            ['technology that helps', 'a moment of peace', 'laughter shared'],
            ['clean water', 'a warm bed', 'someone who believed in you']
        ]
        return hint_sets[(day_num - 1) % len(hint_sets)]
