from django.core.management.base import BaseCommand
from focus.models import FocusProgram, ProgramDay


class Command(BaseCommand):
    help = 'Seed focus programs with 14-day and 30-day programs'

    def handle(self, *args, **options):
        self.stdout.write('Seeding focus programs...')

        # Create 14-Day Focus Program (Free)
        program_14day, created = FocusProgram.objects.get_or_create(
            program_type='14_day',
            defaults={
                'name': '14-Day Focus Challenge',
                'description': 'Build consistent focus habits in just 2 weeks. Perfect for beginners looking to improve productivity.',
                'duration_days': 14,
                'objectives': [
                    'Develop daily focus routine',
                    'Build 14-day streak',
                    'Complete 7 hours of focused work',
                    'Master basic Pomodoro technique'
                ],
                'is_pro_only': False,
                'icon': '🎯',
                'color': '#3B82F6',
                'order': 1
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {program_14day.name}'))
            
            # Create days for 14-day program
            for day_num in range(1, 15):
                ProgramDay.objects.create(
                    program=program_14day,
                    day_number=day_num,
                    title=f'Day {day_num}: {self._get_14day_title(day_num)}',
                    description=self._get_14day_description(day_num),
                    focus_duration=25 if day_num <= 7 else 50,  # Start with 25min, then 50min
                    tasks=self._get_14day_tasks(day_num),
                    tips=self._get_14day_tips(day_num),
                    reflection_prompts=self._get_reflection_prompts(day_num)
                )
            self.stdout.write(self.style.SUCCESS(f'  Created {program_14day.duration_days} days'))

        # Create 30-Day Focus Program (Pro)
        program_30day, created = FocusProgram.objects.get_or_create(
            program_type='30_day',
            defaults={
                'name': '30-Day Focus Mastery',
                'description': 'Transform your productivity in 30 days. Advanced program for serious focus practitioners.',
                'duration_days': 30,
                'objectives': [
                    'Master deep work techniques',
                    'Build 30-day focus streak',
                    'Complete 20+ hours of focused work',
                    'Develop personalized productivity system',
                    'Achieve flow state consistently'
                ],
                'is_pro_only': True,
                'icon': '🚀',
                'color': '#10B981',
                'order': 2
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created: {program_30day.name}'))
            
            # Create days for 30-day program
            for day_num in range(1, 31):
                ProgramDay.objects.create(
                    program=program_30day,
                    day_number=day_num,
                    title=f'Day {day_num}: {self._get_30day_title(day_num)}',
                    description=self._get_30day_description(day_num),
                    focus_duration=self._get_30day_duration(day_num),
                    tasks=self._get_30day_tasks(day_num),
                    tips=self._get_30day_tips(day_num),
                    reflection_prompts=self._get_reflection_prompts(day_num)
                )
            self.stdout.write(self.style.SUCCESS(f'  Created {program_30day.duration_days} days'))

        self.stdout.write(self.style.SUCCESS('Focus programs seeded successfully!'))

    # 14-Day Program Content
    def _get_14day_title(self, day_num):
        titles = {
            1: 'Getting Started',
            2: 'Building Momentum',
            3: 'Finding Your Rhythm',
            4: 'Overcoming Distractions',
            5: 'Deep Work Basics',
            6: 'Weekend Warrior',
            7: 'Week 1 Complete!',
            8: 'Level Up',
            9: 'Flow State Intro',
            10: 'Consistency is Key',
            11: 'Advanced Techniques',
            12: 'Push Your Limits',
            13: 'Almost There',
            14: 'Final Push!'
        }
        return titles.get(day_num, f'Day {day_num}')

    def _get_14day_description(self, day_num):
        if day_num == 1:
            return 'Welcome! Today you\'ll learn the basics of focused work and set up your environment for success.'
        elif day_num == 7:
            return 'Congratulations on completing your first week! Today we\'ll review your progress and set goals for week 2.'
        elif day_num == 14:
            return 'Final day! Reflect on your journey, celebrate your wins, and plan how to continue your focus practice.'
        else:
            return f'Continue building your focus muscle. Today\'s challenge will help you develop deeper concentration.'

    def _get_14day_tasks(self, day_num):
        return [
            'Complete morning planning (5 min)',
            f'Focus session: {25 if day_num <= 7 else 50} minutes',
            'Log distractions and patterns'
        ]

    def _get_14day_tips(self, day_num):
        return [
            'Start with your most important task',
            'Eliminate notifications before starting',
            'Take short breaks between sessions',
            'Drink water and stretch regularly'
        ]

    # 30-Day Program Content
    def _get_30day_title(self, day_num):
        if day_num <= 7:
            return f'Foundation Week - Day {day_num}'
        elif day_num <= 14:
            return f'Building Habits - Day {day_num}'
        elif day_num <= 21:
            return f'Deep Work - Day {day_num}'
        else:
            return f'Mastery - Day {day_num}'

    def _get_30day_description(self, day_num):
        if day_num == 1:
            return 'Begin your 30-day journey to focus mastery. Today we establish your baseline and set ambitious goals.'
        elif day_num == 7:
            return 'First week complete! Time to analyze your progress and adjust your approach.'
        elif day_num == 14:
            return 'Halfway checkpoint. You\'re building serious momentum. Let\'s push deeper into advanced techniques.'
        elif day_num == 21:
            return 'Three weeks in! Your focus habits are becoming second nature. Time to refine and optimize.'
        elif day_num == 30:
            return 'Congratulations! You\'ve completed the 30-day focus mastery program. Reflect on your transformation.'
        else:
            return f'Continue your journey towards focus mastery with today\'s advanced techniques and challenges.'

    def _get_30day_duration(self, day_num):
        """Progressive duration increase"""
        if day_num <= 7:
            return 25
        elif day_num <= 14:
            return 50
        elif day_num <= 21:
            return 75
        else:
            return 90

    def _get_30day_tasks(self, day_num):
        return [
            'Morning review and intention setting (10 min)',
            f'Deep work session: {self._get_30day_duration(day_num)} minutes',
            'Track energy levels and productivity',
            'Evening reflection (5 min)'
        ]

    def _get_30day_tips(self, day_num):
        tips_by_week = {
            1: [
                'Start small and build gradually',
                'Create a distraction-free workspace',
                'Use the Pomodoro technique',
                'Track your progress daily'
            ],
            2: [
                'Schedule focus time in your calendar',
                'Communicate boundaries to others',
                'Experiment with different techniques',
                'Measure your deep work hours'
            ],
            3: [
                'Enter flow state with deep work',
                'Batch similar tasks together',
                'Practice single-tasking',
                'Review and adjust weekly'
            ],
            4: [
                'Master your energy management',
                'Build your personal system',
                'Share your progress with others',
                'Plan beyond the 30 days'
            ]
        }
        week = ((day_num - 1) // 7) + 1
        return tips_by_week.get(week, tips_by_week[1])

    # Shared Content
    def _get_reflection_prompts(self, day_num):
        prompts = [
            "What's the biggest win from today?",
            "What distracted you the most today?",
            "How focused did you feel during your session? (1-5)",
            "What will you do differently tomorrow?"
        ]
        
        # Special prompts for milestone days
        if day_num in [7, 14, 21, 30]:
            prompts = [
                "What have you learned this week?",
                "What patterns have you noticed in your focus?",
                "What's your proudest achievement so far?",
                "What goals will you set for next week?"
            ]
        
        return prompts
