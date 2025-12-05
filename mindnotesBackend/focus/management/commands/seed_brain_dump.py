from django.core.management.base import BaseCommand
from focus.models import FocusProgram, ProgramDay, ProgramStep


class Command(BaseCommand):
    help = 'Seed the Brain Dump Reset 5-Minute Mental Clarity program'

    def handle(self, *args, **options):
        self.stdout.write('Seeding Brain Dump Reset program...')

        # Create Brain Dump Program
        program, created = FocusProgram.objects.get_or_create(
            program_type='brain_dump',
            defaults={
                'name': 'Brain Dump Reset',
                'description': 'Clear your mental clutter in 5 minutes. Offload thoughts, organize priorities, and choose one focused action for today.',
                'duration_days': 30,
                'objectives': [
                    'Clear Mental Clutter - Offload thoughts and reduce mental overwhelm',
                    'Organize Your Mind - Categorize thoughts into actionable items',
                    'Focus on One Thing - Choose your most important task for today',
                    'Build Clarity Habits - Develop a daily practice of mental reset'
                ],
                'daily_tasks': [],  # Not used for ritual programs
                'is_pro_only': False,
                'icon': '🧠',
                'color': '#8B5CF6',  # Purple
                'order': 1
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {program.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'Program already exists: {program.name}'))
            # Update existing program
            program.name = 'Brain Dump Reset'
            program.description = 'Clear your mental clutter in 5 minutes. Offload thoughts, organize priorities, and choose one focused action for today.'
            program.objectives = [
                'Clear Mental Clutter - Offload thoughts and reduce mental overwhelm',
                'Organize Your Mind - Categorize thoughts into actionable items',
                'Focus on One Thing - Choose your most important task for today',
                'Build Clarity Habits - Develop a daily practice of mental reset'
            ]
            program.icon = '🧠'
            program.color = '#8B5CF6'
            program.order = 1
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

        self.stdout.write(self.style.SUCCESS('Brain Dump Reset program seeded successfully!'))

    def _create_steps_for_day(self, program_day, day_num):
        """Create the 5 ritual steps for a day"""

        # Step 1: Settle In (Breathing) - 1 minute
        ProgramStep.objects.create(
            program_day=program_day,
            order=1,
            step_type='breathing',
            title='Settle In',
            description='Take a deep breath. For the next 5 minutes, let\'s clear your head.',
            subtitle='Begin with a calming breath',
            duration_seconds=60,
            input_type='none',
            config={
                'animation': 'breathing_circle',
                'inhale_seconds': 4,
                'hold_seconds': 2,
                'exhale_seconds': 6,
                'cycles': 3,
                'guidance_text': [
                    'Breathe in slowly...',
                    'Hold gently...',
                    'Breathe out completely...'
                ]
            },
            icon='💨',
            color='#10B981',  # Green
            background_color='#D1FAE5',
            is_required=True,
            is_skippable=False
        )

        # Step 2: Brain Dump - Write Your Thoughts (2 minutes)
        ProgramStep.objects.create(
            program_day=program_day,
            order=2,
            step_type='journaling',
            title='Dump Your Thoughts',
            description='Write down whatever\'s on your mind — tasks, worries, reminders. Don\'t filter, just unload.',
            subtitle='Unload everything from your mind',
            duration_seconds=120,
            input_type='text_voice',
            placeholder_text='• unfinished tasks\n• thoughts bothering me\n• random things to remember',
            prompts=self._get_dump_helper_prompts(day_num),
            config={
                'allow_voice': True,
                'allow_bullets': True,
                'min_length': 10,
                'max_length': 2000,
                'show_helper_after_idle_seconds': 10,
                'helper_title': 'Need help dumping?',
                'helper_prompts': [
                    'What\'s taking up most of your mental space today?',
                    'Is there something you keep postponing?',
                    'What thought keeps replaying in your head?'
                ]
            },
            icon='📝',
            color='#3B82F6',  # Blue
            background_color='#DBEAFE',
            is_required=True,
            is_skippable=False
        )

        # Step 3: Categorize Your Thoughts (1 minute)
        ProgramStep.objects.create(
            program_day=program_day,
            order=3,
            step_type='task',
            title='Categorize',
            description='Label each item quickly. Don\'t overthink — just trust your instinct.',
            subtitle='Drag or tap to assign categories',
            duration_seconds=60,
            input_type='multi_choice',
            choices=self._get_categories(),
            config={
                'display_mode': 'cards',
                'allow_drag': True,
                'show_icons': True,
                'categorize_previous_step': True,  # Link to previous brain dump
                'category_colors': {
                    'actionable': '#10B981',
                    'thought': '#8B5CF6',
                    'worry': '#F59E0B',
                    'reminder': '#3B82F6',
                    'personal': '#EC4899',
                    'work': '#6366F1',
                    'finance': '#14B8A6',
                    'health': '#22C55E',
                    'goal': '#F97316',
                    'let_go': '#6B7280'
                }
            },
            icon='🏷️',
            color='#F59E0B',  # Amber
            background_color='#FEF3C7',
            is_required=True,
            is_skippable=True
        )

        # Step 4: Choose One Focus Task (45 seconds)
        ProgramStep.objects.create(
            program_day=program_day,
            order=4,
            step_type='prompt',
            title='Choose One Task',
            description='Pick one thing that feels light and doable today.',
            subtitle=self._get_focus_prompt(day_num),
            duration_seconds=45,
            input_type='text',
            placeholder_text='My focus for today is...',
            prompts=[
                'What\'s the ONE thing I can complete today?',
                'Which task would make the biggest difference?',
                'What would give me the most relief if done?'
            ],
            config={
                'show_actionable_items': True,  # Show items categorized as actionable
                'save_as_focus_task': True,
                'add_to_today_tasks': True
            },
            icon='🎯',
            color='#EF4444',  # Red
            background_color='#FEE2E2',
            is_required=True,
            is_skippable=False
        )

        # Step 5: Close & Breathe (15 seconds)
        ProgramStep.objects.create(
            program_day=program_day,
            order=5,
            step_type='breathing',
            title='Close & Breathe',
            description='You just cleared your mental desk. Take one calm breath.',
            subtitle='Inhale for 4, exhale for 6',
            duration_seconds=15,
            input_type='none',
            config={
                'animation': 'breathing_circle',
                'inhale_seconds': 4,
                'hold_seconds': 0,
                'exhale_seconds': 6,
                'cycles': 1,
                'show_summary': True,
                'summary_template': 'You cleared {thought_count} thoughts, categorized {category_count} items, and chose 1 focus. 🌿',
                'play_chime': True
            },
            icon='✨',
            color='#10B981',  # Green
            background_color='#D1FAE5',
            is_required=True,
            is_skippable=False
        )

    def _get_categories(self):
        """Get the 10 categories for brain dump"""
        return [
            {'id': 'actionable', 'label': 'Actionable Task', 'icon': '✅', 'description': 'Something I can do or complete soon'},
            {'id': 'thought', 'label': 'Thought / Reflection', 'icon': '💭', 'description': 'A feeling, idea, or insight worth journaling on'},
            {'id': 'worry', 'label': 'Worry / Anxiety', 'icon': '⚠️', 'description': 'Something that\'s mentally heavy or uncertain'},
            {'id': 'reminder', 'label': 'Reminder / To-Do Later', 'icon': '🗓', 'description': 'Needs to be done, but not urgent today'},
            {'id': 'personal', 'label': 'Personal / Relationship', 'icon': '❤️', 'description': 'Related to people, emotions, or connections'},
            {'id': 'work', 'label': 'Work / Career', 'icon': '💼', 'description': 'Related to job, projects, or professional goals'},
            {'id': 'finance', 'label': 'Finance / Money', 'icon': '💰', 'description': 'Bills, expenses, or financial concerns'},
            {'id': 'health', 'label': 'Health / Mind / Body', 'icon': '🧘', 'description': 'Physical or mental well-being thoughts'},
            {'id': 'goal', 'label': 'Goal / Dream', 'icon': '🎯', 'description': 'Something I want to achieve in the future'},
            {'id': 'let_go', 'label': 'Let Go / Not Important', 'icon': '❌', 'description': 'Doesn\'t need action; release it'}
        ]

    def _get_day_title(self, day_num):
        """Get motivational title for each day"""
        if day_num == 1:
            return 'Your First Brain Dump'
        elif day_num == 7:
            return 'One Week of Clarity!'
        elif day_num == 14:
            return 'Two Weeks of Mental Freedom'
        elif day_num == 21:
            return 'Clarity Habit Formed!'
        elif day_num == 30:
            return 'Mental Reset Master!'
        else:
            return f'Day {day_num} - Clear Your Mind'

    def _get_day_description(self, day_num):
        """Get description for each day"""
        descriptions = {
            1: 'Welcome to Brain Dump Reset! Let\'s clear your mental clutter and find focus.',
            7: 'You\'ve completed a full week of mental clarity. Your mind is getting lighter!',
            14: 'Two weeks of consistent brain dumps. Notice how much clearer you feel.',
            21: 'They say it takes 21 days to form a habit. Mental clarity is now your superpower!',
            30: 'Congratulations! You\'ve mastered the art of mental reset.',
        }
        return descriptions.get(day_num, 'Another session to clear your mind and find your focus for the day.')

    def _get_day_tips(self, day_num):
        """Get tips for each day"""
        tips_rotation = [
            [
                'Don\'t filter your thoughts — just write',
                'Set a timer to avoid overthinking',
                'Do this first thing in the morning'
            ],
            [
                'No thought is too small to write',
                'Include both tasks and feelings',
                'Trust your gut when categorizing'
            ],
            [
                'Focus on quantity, not quality',
                'Let go of perfectionism',
                'Your brain dump is private — be honest'
            ],
            [
                'Notice patterns in your thoughts',
                'Choose the easiest win first',
                'Celebrate clearing mental clutter'
            ],
            [
                'Review yesterday\'s focus task',
                'Keep your dump journal handy',
                'Share your biggest insight'
            ]
        ]
        return tips_rotation[(day_num - 1) % len(tips_rotation)]

    def _get_dump_helper_prompts(self, day_num):
        """Get helper prompts that rotate throughout the program"""
        prompt_sets = [
            [
                'What\'s taking up most of your mental space today?',
                'Is there something you keep postponing?',
                'What thought keeps replaying in your head?'
            ],
            [
                'What\'s causing you stress right now?',
                'What conversation do you need to have?',
                'What decision are you avoiding?'
            ],
            [
                'What are you worried about this week?',
                'What would you do if you had more time?',
                'What\'s been on your to-do list too long?'
            ],
            [
                'What relationships need attention?',
                'What goals have you been neglecting?',
                'What would make today great?'
            ],
            [
                'What are you grateful for today?',
                'What challenge are you facing?',
                'What do you need to let go of?'
            ]
        ]
        return prompt_sets[(day_num - 1) % len(prompt_sets)]

    def _get_focus_prompt(self, day_num):
        """Get the main focus prompt for the day"""
        prompts = [
            'What\'s the ONE thing that will make today great?',
            'Which task would give you the most relief?',
            'What\'s the most important thing to complete?',
            'What would make you proud at the end of today?',
            'Which task has been waiting too long?',
            'What would move you closer to your goals?',
            'What\'s the easiest win you can get today?',
        ]
        return prompts[(day_num - 1) % len(prompts)]
