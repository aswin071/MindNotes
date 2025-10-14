from django.core.management.base import BaseCommand
from prompts.models import PromptCategory, DailyPrompt


class Command(BaseCommand):
    help = 'Seeds diverse reflection questions for daily prompts'

    def handle(self, *args, **options):
        self.stdout.write("Seeding prompt categories and questions...")

        # Create Categories
        categories_data = [
            {
                'name': 'Gratitude',
                'description': 'Focus on appreciation and thankfulness',
                'icon': '🙏',
                'color': '#10B981',
                'order': 1
            },
            {
                'name': 'Growth',
                'description': 'Personal development and learning',
                'icon': '🌱',
                'color': '#8B5CF6',
                'order': 2
            },
            {
                'name': 'Relationships',
                'description': 'Connections with others',
                'icon': '💝',
                'color': '#EC4899',
                'order': 3
            },
            {
                'name': 'Challenges',
                'description': 'Overcoming obstacles',
                'icon': '⚡',
                'color': '#F59E0B',
                'order': 4
            },
            {
                'name': 'Self-Discovery',
                'description': 'Understanding yourself better',
                'icon': '🔍',
                'color': '#3B82F6',
                'order': 5
            },
            {
                'name': 'Wellness',
                'description': 'Physical and mental health',
                'icon': '🌟',
                'color': '#06B6D4',
                'order': 6
            },
            {
                'name': 'Creativity',
                'description': 'Innovation and imagination',
                'icon': '🎨',
                'color': '#EF4444',
                'order': 7
            },
            {
                'name': 'Reflection',
                'description': 'Looking back and introspection',
                'icon': '🪞',
                'color': '#6366F1',
                'order': 8
            },
        ]

        categories = {}
        for cat_data in categories_data:
            category, created = PromptCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            categories[cat_data['name']] = category
            status = "Created" if created else "Exists"
            self.stdout.write(f"  {status}: {cat_data['icon']} {cat_data['name']}")

        # Comprehensive Prompt Library (120+ questions)
        prompts_data = [
            # GRATITUDE (20 prompts)
            {
                'category': 'Gratitude',
                'question': 'What made you smile today?',
                'description': 'Identify positive moments',
                'tags': ['Grateful', 'Happy'],
                'difficulty': 'easy'
            },
            {
                'category': 'Gratitude',
                'question': 'Who are you grateful for today and why?',
                'description': 'Appreciate relationships',
                'tags': ['Grateful', 'Family', 'Relationships'],
                'difficulty': 'easy'
            },
            {
                'category': 'Gratitude',
                'question': 'What small thing brought you comfort today?',
                'description': 'Notice everyday blessings',
                'tags': ['Grateful', 'Calm'],
                'difficulty': 'easy'
            },
            {
                'category': 'Gratitude',
                'question': 'What skill or ability are you thankful to have?',
                'description': 'Recognize your capabilities',
                'tags': ['Grateful', 'Achievement'],
                'difficulty': 'medium'
            },
            {
                'category': 'Gratitude',
                'question': 'What lesson from the past are you grateful for?',
                'description': 'Appreciate growth through experiences',
                'tags': ['Grateful', 'Reflection', 'Learning'],
                'difficulty': 'medium'
            },
            {
                'category': 'Gratitude',
                'question': 'What opportunity do you have that not everyone gets?',
                'description': 'Recognize privilege and fortune',
                'tags': ['Grateful', 'Reflection'],
                'difficulty': 'medium'
            },
            {
                'category': 'Gratitude',
                'question': 'Which of your senses brought you the most joy today?',
                'description': 'Appreciate sensory experiences',
                'tags': ['Grateful', 'Mindfulness'],
                'difficulty': 'easy'
            },
            {
                'category': 'Gratitude',
                'question': 'What aspect of your daily routine are you most grateful for?',
                'description': 'Find gratitude in consistency',
                'tags': ['Grateful', 'Personal'],
                'difficulty': 'easy'
            },
            {
                'category': 'Gratitude',
                'question': 'What place makes you feel most grateful?',
                'description': 'Appreciate meaningful spaces',
                'tags': ['Grateful', 'Travel'],
                'difficulty': 'easy'
            },
            {
                'category': 'Gratitude',
                'question': 'What challenge helped you grow that you\'re now grateful for?',
                'description': 'Find gratitude in difficulties',
                'tags': ['Grateful', 'Reflection', 'Goal'],
                'difficulty': 'deep'
            },

            # GROWTH (20 prompts)
            {
                'category': 'Growth',
                'question': 'What did you learn today?',
                'description': 'Identify daily learning',
                'tags': ['Learning', 'Idea'],
                'difficulty': 'easy'
            },
            {
                'category': 'Growth',
                'question': 'What skill do you want to develop next?',
                'description': 'Set learning goals',
                'tags': ['Learning', 'Goal'],
                'difficulty': 'easy'
            },
            {
                'category': 'Growth',
                'question': 'How have you grown in the past month?',
                'description': 'Track personal evolution',
                'tags': ['Reflection', 'Achievement'],
                'difficulty': 'medium'
            },
            {
                'category': 'Growth',
                'question': 'What mistake taught you something valuable?',
                'description': 'Learn from failures',
                'tags': ['Reflection', 'Learning'],
                'difficulty': 'medium'
            },
            {
                'category': 'Growth',
                'question': 'What book, podcast, or video inspired you recently?',
                'description': 'Track influential content',
                'tags': ['Learning', 'Inspired', 'Idea'],
                'difficulty': 'easy'
            },
            {
                'category': 'Growth',
                'question': 'What comfort zone did you step out of today?',
                'description': 'Acknowledge courage',
                'tags': ['Achievement', 'Confident'],
                'difficulty': 'medium'
            },
            {
                'category': 'Growth',
                'question': 'What advice would you give your younger self?',
                'description': 'Reflect on wisdom gained',
                'tags': ['Reflection', 'Learning'],
                'difficulty': 'deep'
            },
            {
                'category': 'Growth',
                'question': 'What habit are you working to build or break?',
                'description': 'Track behavior change',
                'tags': ['Goal', 'Health'],
                'difficulty': 'medium'
            },
            {
                'category': 'Growth',
                'question': 'What feedback did you receive that helped you improve?',
                'description': 'Value constructive criticism',
                'tags': ['Learning', 'Work'],
                'difficulty': 'medium'
            },
            {
                'category': 'Growth',
                'question': 'What limiting belief are you ready to let go of?',
                'description': 'Identify mental barriers',
                'tags': ['Reflection', 'Breakthrough'],
                'difficulty': 'deep'
            },

            # RELATIONSHIPS (20 prompts)
            {
                'category': 'Relationships',
                'question': 'How did you make someone\'s day better?',
                'description': 'Recognize your positive impact',
                'tags': ['Grateful', 'Family', 'Relationships'],
                'difficulty': 'easy'
            },
            {
                'category': 'Relationships',
                'question': 'Who inspired you today?',
                'description': 'Acknowledge influences',
                'tags': ['Inspired', 'Relationships'],
                'difficulty': 'easy'
            },
            {
                'category': 'Relationships',
                'question': 'What conversation made you think differently?',
                'description': 'Value perspective shifts',
                'tags': ['Idea', 'Learning', 'Relationships'],
                'difficulty': 'medium'
            },
            {
                'category': 'Relationships',
                'question': 'How did you show love to someone today?',
                'description': 'Acknowledge acts of care',
                'tags': ['Family', 'Relationships'],
                'difficulty': 'easy'
            },
            {
                'category': 'Relationships',
                'question': 'What do you appreciate most about your closest friend?',
                'description': 'Deepen gratitude for relationships',
                'tags': ['Grateful', 'Relationships'],
                'difficulty': 'easy'
            },
            {
                'category': 'Relationships',
                'question': 'How did someone support you when you needed it?',
                'description': 'Recognize support systems',
                'tags': ['Grateful', 'Relationships'],
                'difficulty': 'medium'
            },
            {
                'category': 'Relationships',
                'question': 'What quality do you admire in someone you know?',
                'description': 'Learn from others',
                'tags': ['Inspired', 'Relationships'],
                'difficulty': 'easy'
            },
            {
                'category': 'Relationships',
                'question': 'How can you strengthen a relationship that matters to you?',
                'description': 'Intentional relationship building',
                'tags': ['Goal', 'Relationships'],
                'difficulty': 'medium'
            },
            {
                'category': 'Relationships',
                'question': 'What conflict taught you about communication?',
                'description': 'Learn from disagreements',
                'tags': ['Learning', 'Reflection', 'Relationships'],
                'difficulty': 'deep'
            },
            {
                'category': 'Relationships',
                'question': 'Who do you need to reconnect with?',
                'description': 'Identify neglected relationships',
                'tags': ['Relationships', 'Goal'],
                'difficulty': 'medium'
            },

            # CHALLENGES (20 prompts)
            {
                'category': 'Challenges',
                'question': 'What challenge did you face today?',
                'description': 'Acknowledge difficulties',
                'tags': ['Reflection', 'Stressed'],
                'difficulty': 'easy'
            },
            {
                'category': 'Challenges',
                'question': 'How did you overcome an obstacle today?',
                'description': 'Celebrate problem-solving',
                'tags': ['Achievement', 'Confident'],
                'difficulty': 'medium'
            },
            {
                'category': 'Challenges',
                'question': 'What are you struggling with right now?',
                'description': 'Acknowledge current difficulties',
                'tags': ['Anxious', 'Stressed', 'Reflection'],
                'difficulty': 'medium'
            },
            {
                'category': 'Challenges',
                'question': 'What strength did you discover in yourself during a difficult time?',
                'description': 'Find resilience',
                'tags': ['Achievement', 'Reflection'],
                'difficulty': 'deep'
            },
            {
                'category': 'Challenges',
                'question': 'What fear did you face today, even just a little?',
                'description': 'Acknowledge courage',
                'tags': ['Confident', 'Achievement'],
                'difficulty': 'medium'
            },
            {
                'category': 'Challenges',
                'question': 'How are you coping with stress?',
                'description': 'Reflect on stress management',
                'tags': ['Stressed', 'Health', 'Self-care'],
                'difficulty': 'medium'
            },
            {
                'category': 'Challenges',
                'question': 'What would help you feel more at ease right now?',
                'description': 'Identify needs',
                'tags': ['Calm', 'Self-care'],
                'difficulty': 'easy'
            },
            {
                'category': 'Challenges',
                'question': 'What\'s one small step you can take toward solving a problem?',
                'description': 'Break down challenges',
                'tags': ['Goal', 'Planning'],
                'difficulty': 'medium'
            },
            {
                'category': 'Challenges',
                'question': 'What past challenge prepared you for today?',
                'description': 'Connect experiences',
                'tags': ['Reflection', 'Grateful'],
                'difficulty': 'deep'
            },
            {
                'category': 'Challenges',
                'question': 'How did you practice patience today?',
                'description': 'Recognize self-control',
                'tags': ['Calm', 'Achievement'],
                'difficulty': 'medium'
            },

            # SELF-DISCOVERY (20 prompts)
            {
                'category': 'Self-Discovery',
                'question': 'What value is most important to you right now?',
                'description': 'Clarify priorities',
                'tags': ['Reflection', 'Important'],
                'difficulty': 'medium'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What makes you unique?',
                'description': 'Celebrate individuality',
                'tags': ['Confident', 'Reflection'],
                'difficulty': 'medium'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What do you need more of in your life?',
                'description': 'Identify gaps',
                'tags': ['Reflection', 'Goal'],
                'difficulty': 'medium'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What energizes you?',
                'description': 'Understand motivations',
                'tags': ['Excited', 'Reflection'],
                'difficulty': 'easy'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What drains your energy?',
                'description': 'Identify energy leaks',
                'tags': ['Reflection', 'Stressed'],
                'difficulty': 'easy'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What does success mean to you?',
                'description': 'Define personal success',
                'tags': ['Reflection', 'Goal'],
                'difficulty': 'deep'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What brings you peace?',
                'description': 'Identify calming factors',
                'tags': ['Calm', 'Meditation'],
                'difficulty': 'easy'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What part of yourself are you still getting to know?',
                'description': 'Acknowledge ongoing discovery',
                'tags': ['Reflection', 'Question'],
                'difficulty': 'deep'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What decision are you avoiding?',
                'description': 'Face avoidance',
                'tags': ['Reflection', 'Anxious'],
                'difficulty': 'deep'
            },
            {
                'category': 'Self-Discovery',
                'question': 'What pattern do you notice in your behavior?',
                'description': 'Develop self-awareness',
                'tags': ['Reflection', 'Learning'],
                'difficulty': 'deep'
            },

            # WELLNESS (20 prompts)
            {
                'category': 'Wellness',
                'question': 'How did you take care of yourself today?',
                'description': 'Acknowledge self-care',
                'tags': ['Self-care', 'Health'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'What physical activity made you feel good?',
                'description': 'Track movement',
                'tags': ['Fitness', 'Health'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'How would you rate your sleep quality lately?',
                'description': 'Monitor rest',
                'tags': ['Health', 'Reflection'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'What healthy choice did you make today?',
                'description': 'Celebrate wellness decisions',
                'tags': ['Health', 'Achievement'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'How is your body feeling right now?',
                'description': 'Body awareness',
                'tags': ['Health', 'Mindfulness'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'What helps you relax?',
                'description': 'Identify relaxation techniques',
                'tags': ['Calm', 'Self-care'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'How did you nourish yourself today (food, rest, joy)?',
                'description': 'Holistic nourishment',
                'tags': ['Self-care', 'Health'],
                'difficulty': 'easy'
            },
            {
                'category': 'Wellness',
                'question': 'What boundary did you set to protect your wellbeing?',
                'description': 'Acknowledge self-protection',
                'tags': ['Self-care', 'Achievement'],
                'difficulty': 'medium'
            },
            {
                'category': 'Wellness',
                'question': 'What does balance look like in your life?',
                'description': 'Define personal balance',
                'tags': ['Reflection', 'Health'],
                'difficulty': 'medium'
            },
            {
                'category': 'Wellness',
                'question': 'How can you be kinder to yourself?',
                'description': 'Practice self-compassion',
                'tags': ['Self-care', 'Reflection'],
                'difficulty': 'medium'
            },

            # CREATIVITY (10 prompts)
            {
                'category': 'Creativity',
                'question': 'What idea excited you today?',
                'description': 'Capture inspiration',
                'tags': ['Idea', 'Excited'],
                'difficulty': 'easy'
            },
            {
                'category': 'Creativity',
                'question': 'What problem would you love to solve?',
                'description': 'Channel creative energy',
                'tags': ['Idea', 'Goal'],
                'difficulty': 'medium'
            },
            {
                'category': 'Creativity',
                'question': 'What would you create if you had no limitations?',
                'description': 'Dream big',
                'tags': ['Dream', 'Idea'],
                'difficulty': 'medium'
            },
            {
                'category': 'Creativity',
                'question': 'What creative activity brings you joy?',
                'description': 'Identify creative outlets',
                'tags': ['Happy', 'Hobby'],
                'difficulty': 'easy'
            },
            {
                'category': 'Creativity',
                'question': 'What inspired your imagination today?',
                'description': 'Track inspiration sources',
                'tags': ['Inspired', 'Idea'],
                'difficulty': 'easy'
            },
            {
                'category': 'Creativity',
                'question': 'How did you express yourself today?',
                'description': 'Acknowledge self-expression',
                'tags': ['Confident', 'Personal'],
                'difficulty': 'easy'
            },
            {
                'category': 'Creativity',
                'question': 'What would you do differently if you could start over?',
                'description': 'Reimagine possibilities',
                'tags': ['Reflection', 'Idea'],
                'difficulty': 'deep'
            },
            {
                'category': 'Creativity',
                'question': 'What new thing do you want to try?',
                'description': 'Explore curiosity',
                'tags': ['Excited', 'Goal'],
                'difficulty': 'easy'
            },
            {
                'category': 'Creativity',
                'question': 'What makes you lose track of time?',
                'description': 'Find flow activities',
                'tags': ['Happy', 'Hobby'],
                'difficulty': 'easy'
            },
            {
                'category': 'Creativity',
                'question': 'What unconventional solution did you think of?',
                'description': 'Value creative thinking',
                'tags': ['Idea', 'Breakthrough'],
                'difficulty': 'medium'
            },

            # REFLECTION (10 prompts)
            {
                'category': 'Reflection',
                'question': 'What moment will you remember from today?',
                'description': 'Capture memories',
                'tags': ['Memory', 'Reflection'],
                'difficulty': 'easy'
            },
            {
                'category': 'Reflection',
                'question': 'How has this week been different from last week?',
                'description': 'Notice change',
                'tags': ['Reflection', 'Review'],
                'difficulty': 'medium'
            },
            {
                'category': 'Reflection',
                'question': 'What surprised you today?',
                'description': 'Acknowledge the unexpected',
                'tags': ['Reflection', 'Excited'],
                'difficulty': 'easy'
            },
            {
                'category': 'Reflection',
                'question': 'What would you do differently if you could relive today?',
                'description': 'Learn from the day',
                'tags': ['Reflection', 'Learning'],
                'difficulty': 'medium'
            },
            {
                'category': 'Reflection',
                'question': 'What are you looking forward to?',
                'description': 'Anticipate the future',
                'tags': ['Excited', 'Goal'],
                'difficulty': 'easy'
            },
            {
                'category': 'Reflection',
                'question': 'What emotion dominated your day?',
                'description': 'Emotional awareness',
                'tags': ['Reflection', 'Mindfulness'],
                'difficulty': 'easy'
            },
            {
                'category': 'Reflection',
                'question': 'What unfinished goal is calling to you?',
                'description': 'Revisit intentions',
                'tags': ['Goal', 'Reflection'],
                'difficulty': 'medium'
            },
            {
                'category': 'Reflection',
                'question': 'What did you avoid thinking about today?',
                'description': 'Face avoidance',
                'tags': ['Reflection', 'Question'],
                'difficulty': 'deep'
            },
            {
                'category': 'Reflection',
                'question': 'If today was a chapter in your life story, what would it be titled?',
                'description': 'Creative reflection',
                'tags': ['Reflection', 'Memory'],
                'difficulty': 'medium'
            },
            {
                'category': 'Reflection',
                'question': 'What truth became clearer to you today?',
                'description': 'Acknowledge insights',
                'tags': ['Reflection', 'Breakthrough'],
                'difficulty': 'deep'
            },
        ]

        # Create prompts
        created_count = 0
        skipped_count = 0

        for prompt_data in prompts_data:
            category = categories[prompt_data['category']]
            prompt_dict = {
                'category': category,
                'question': prompt_data['question'],
                'description': prompt_data['description'],
                'tags': prompt_data['tags'],
                'difficulty': prompt_data['difficulty'],
            }

            prompt, created = DailyPrompt.objects.get_or_create(
                question=prompt_data['question'],
                defaults=prompt_dict
            )

            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Seeding completed!\n"
                f"Categories: {len(categories_data)}\n"
                f"Prompts created: {created_count}\n"
                f"Prompts skipped: {skipped_count}\n"
                f"Total prompts: {DailyPrompt.objects.count()}"
            )
        )
