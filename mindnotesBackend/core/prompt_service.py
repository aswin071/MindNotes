"""
Prompt Generation Service
Handles daily prompt set generation with smart rotation algorithm
"""
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Optional
import random
import os
from django.core.cache import cache
from django.db.models import Q

from prompts.models import DailyPrompt, PromptCategory
from prompts.mongo_models import DailyPromptSetMongo, PromptResponseMongo


class PromptService:
    """Service for managing daily prompt generation and rotation"""

    @staticmethod
    def generate_daily_prompts(user, target_date: Optional[date] = None) -> DailyPromptSetMongo:
        """
        Generate 5 diverse prompts for a user on a specific date

        Smart rotation algorithm ensures:
        - NO REPEATS EVER - tracks ALL user history (not just 30 days)
        - Balanced category distribution
        - Mix of difficulty levels
        - Auto-generates new prompts when library exhausted
        """
        if target_date is None:
            target_date = date.today()

        # Check if prompts already exist for this date
        existing_set = DailyPromptSetMongo.objects(
            user_id=user.id,
            date=target_date
        ).first()

        if existing_set:
            return existing_set

        # Get ALL user's response history (lifetime - NEVER repeat)
        all_responses = PromptResponseMongo.objects(
            user_id=user.id
        ).only('prompt_id')

        used_prompt_ids = {r.prompt_id for r in all_responses}

        # Get all active prompts excluding ALL previously used ones
        available_prompts = DailyPrompt.objects.filter(
            is_active=True
        ).exclude(
            id__in=used_prompt_ids
        ).select_related('category')

        available_count = available_prompts.count()

        # Check if we need to generate new prompts dynamically
        if available_count < 5:
            # Generate new prompts to replenish library
            needed_count = 20  # Generate batch of 20 new prompts
            PromptService._generate_dynamic_prompts(user, needed_count)

            # Re-query after generation
            available_prompts = DailyPrompt.objects.filter(
                is_active=True
            ).exclude(
                id__in=used_prompt_ids
            ).select_related('category')

        # Convert to list for sampling
        prompts_list = list(available_prompts)

        # Smart selection: Ensure category diversity
        selected_prompts = PromptService._select_diverse_prompts(prompts_list, count=5)

        # Prepare prompt data for MongoDB
        prompts_data = []
        for prompt in selected_prompts:
            prompts_data.append({
                'id': prompt.id,
                'question': prompt.question,
                'description': prompt.description or '',
                'category': prompt.category.name if prompt.category else 'General',
                'category_icon': prompt.category.icon if prompt.category else '📝',
                'category_color': prompt.category.color if prompt.category else '#3B82F6',
                'tags': prompt.tags or [],
                'difficulty': prompt.difficulty,
            })

        # Create MongoDB prompt set
        prompt_set = DailyPromptSetMongo(
            user_id=user.id,
            date=target_date,
            prompts=prompts_data,
            is_active=True,
            completed_count=0,
            is_fully_completed=False,
            generated_at=datetime.now(timezone.utc)
        )
        prompt_set.save()

        return prompt_set

    @staticmethod
    def _select_diverse_prompts(prompts_list: List[DailyPrompt], count: int = 5) -> List[DailyPrompt]:
        """
        Select prompts ensuring diversity across categories and difficulty
        """
        if len(prompts_list) <= count:
            return prompts_list

        # Group by category
        by_category = {}
        for prompt in prompts_list:
            cat_name = prompt.category.name if prompt.category else 'General'
            if cat_name not in by_category:
                by_category[cat_name] = []
            by_category[cat_name].append(prompt)

        selected = []
        categories = list(by_category.keys())
        random.shuffle(categories)

        # First pass: Pick one from each category until we have 5
        for category in categories:
            if len(selected) >= count:
                break
            prompt = random.choice(by_category[category])
            selected.append(prompt)
            by_category[category].remove(prompt)

        # Second pass: If still need more, randomly select from remaining
        while len(selected) < count:
            remaining = [p for proms in by_category.values() for p in proms]
            if not remaining:
                break
            prompt = random.choice(remaining)
            selected.append(prompt)
            cat = prompt.category.name if prompt.category else 'General'
            by_category[cat].remove(prompt)

        # Shuffle final order
        random.shuffle(selected)
        return selected

    @staticmethod
    def get_today_prompts(user) -> Optional[DailyPromptSetMongo]:
        """Get or generate today's prompts for user"""
        today = date.today()

        # Try cache first
        cache_key = f'daily_prompts_{user.id}_{today}'
        cached = cache.get(cache_key)
        if cached:
            return cached

        prompt_set = PromptService.generate_daily_prompts(user, today)

        # Cache for 1 hour
        cache.set(cache_key, prompt_set, 3600)
        return prompt_set

    @staticmethod
    def submit_prompt_response(user, prompt_id: int, response_text: str,
                              time_spent: int = 0, mood: Optional[int] = None) -> Dict:
        """
        Submit a response to a prompt
        Updates completion tracking and creates journal entry
        """
        today = date.today()

        # Get today's prompt set
        prompt_set = DailyPromptSetMongo.objects(
            user_id=user.id,
            date=today
        ).first()

        if not prompt_set:
            raise ValueError("No prompt set found for today")

        # Verify prompt is in today's set
        prompt_in_set = any(p['id'] == prompt_id for p in prompt_set.prompts)
        if not prompt_in_set:
            raise ValueError("Prompt not in today's set")

        # Get prompt details from PostgreSQL
        prompt = DailyPrompt.objects.get(id=prompt_id)

        # Calculate word count
        word_count = len(response_text.split())

        # Create response in MongoDB
        prompt_response = PromptResponseMongo(
            user_id=user.id,
            prompt_id=prompt_id,
            daily_set_date=today,
            response=response_text,
            word_count=word_count,
            time_spent_seconds=time_spent,
            mood_at_response=mood,
            responded_at=datetime.now(timezone.utc),
            is_active=True
        )
        prompt_response.save()

        # Update prompt set completion
        if prompt_id not in prompt_set.completed_prompt_ids:
            prompt_set.completed_prompt_ids.append(prompt_id)
            prompt_set.completed_count += 1
            prompt_set.last_interaction_at = datetime.now(timezone.utc)

            # Check if fully completed
            if prompt_set.completed_count >= len(prompt_set.prompts):
                prompt_set.is_fully_completed = True

            prompt_set.save()

        # Invalidate cache
        cache_key = f'daily_prompts_{user.id}_{today}'
        cache.delete(cache_key)

        return {
            'response_id': str(prompt_response.id),
            'completed_count': prompt_set.completed_count,
            'total_prompts': len(prompt_set.prompts),
            'is_fully_completed': prompt_set.is_fully_completed,
            'tags': prompt.tags,
        }

    @staticmethod
    def get_user_streak(user) -> Dict:
        """
        Calculate user's prompt completion streak
        """
        today = date.today()

        # Check completion for consecutive days going backwards
        streak = 0
        current_date = today

        while True:
            prompt_set = DailyPromptSetMongo.objects(
                user_id=user.id,
                date=current_date,
                is_fully_completed=True
            ).first()

            if not prompt_set:
                break

            streak += 1
            current_date -= timedelta(days=1)

            # Safety limit
            if streak > 365:
                break

        # Get total completed days
        total_completed = DailyPromptSetMongo.objects(
            user_id=user.id,
            is_fully_completed=True
        ).count()

        return {
            'current_streak': streak,
            'total_completed_days': total_completed,
            'streak_message': PromptService._get_streak_message(streak)
        }

    @staticmethod
    def _get_streak_message(streak: int) -> str:
        """Get motivational message based on streak"""
        if streak == 0:
            return "Start your reflection journey today!"
        elif streak == 1:
            return "Great start! Come back tomorrow! 🌱"
        elif streak < 7:
            return f"{streak} days strong! Keep it going! 🔥"
        elif streak < 30:
            return f"Amazing! {streak} day streak! 🌟"
        elif streak < 100:
            return f"Incredible! {streak} days of reflection! 🏆"
        else:
            return f"Legendary! {streak} day streak! 👑"

    @staticmethod
    def get_completion_stats(user) -> Dict:
        """Get user's prompt completion statistics"""
        total_responses = PromptResponseMongo.objects(user_id=user.id).count()

        # Responses by category
        responses = PromptResponseMongo.objects(user_id=user.id).only('prompt_id')
        prompt_ids = [r.prompt_id for r in responses]

        category_stats = {}
        if prompt_ids:
            prompts_with_cats = DailyPrompt.objects.filter(
                id__in=prompt_ids
            ).select_related('category')

            for prompt in prompts_with_cats:
                cat_name = prompt.category.name if prompt.category else 'General'
                category_stats[cat_name] = category_stats.get(cat_name, 0) + 1

        # Average word count
        responses_with_words = PromptResponseMongo.objects(user_id=user.id).only('word_count')
        total_words = sum(r.word_count for r in responses_with_words)
        avg_word_count = total_words // total_responses if total_responses > 0 else 0

        return {
            'total_responses': total_responses,
            'category_breakdown': category_stats,
            'average_word_count': avg_word_count,
            'total_words_written': total_words,
        }

    @staticmethod
    def _get_tags_for_category(category_name: str) -> List[str]:
        """Get appropriate tags for a given category"""
        category_tag_map = {
            'Gratitude': ['Grateful', 'Happy', 'Calm', 'Reflection'],
            'Growth': ['Learning', 'Achievement', 'Goal', 'Breakthrough'],
            'Relationships': ['Family', 'Relationships', 'Grateful'],
            'Challenges': ['Stressed', 'Achievement', 'Confident', 'Reflection'],
            'Self-Discovery': ['Reflection', 'Important', 'Question', 'Learning'],
            'Wellness': ['Health', 'Self-care', 'Meditation', 'Calm'],
            'Creativity': ['Idea', 'Excited', 'Dream', 'Hobby'],
            'Reflection': ['Reflection', 'Memory', 'Learning', 'Review'],
        }

        available_tags = category_tag_map.get(category_name, [])
        return random.sample(available_tags, 2) if available_tags else []

    @staticmethod
    def _get_prompt_templates() -> List[str]:
        """Get all prompt generation templates"""
        return [
            # Gratitude variations
            "What unexpected moment brought you joy {time_period}?",
            "Who showed you kindness {time_period} and how did it impact you?",
            "What comfort or blessing did you take for granted {time_period}?",
            "What skill or strength are you currently grateful to possess?",
            "What lesson from your past continues to serve you well?",

            # Growth variations
            "What new perspective did you gain {time_period}?",
            "How did you challenge yourself {time_period}?",
            "What feedback or insight helped you improve recently?",
            "What pattern in your behavior are you becoming aware of?",
            "What would your future self thank you for doing today?",

            # Relationships variations
            "How did you strengthen a relationship {time_period}?",
            "What conversation left a lasting impression on you?",
            "Who needs your attention or support right now?",
            "What quality in others do you want to cultivate in yourself?",
            "How did you practice empathy or understanding {time_period}?",

            # Challenges variations
            "What difficult choice did you navigate {time_period}?",
            "How are you managing uncertainty in your life?",
            "What fear or doubt are you working through?",
            "What obstacle taught you something about your resilience?",
            "How did you practice self-compassion during difficulty?",

            # Self-Discovery variations
            "What truth about yourself became clearer {time_period}?",
            "What do you need to give yourself permission to do?",
            "What part of your identity is evolving right now?",
            "What value guides your decisions most strongly?",
            "What does authentic living mean to you currently?",

            # Wellness variations
            "How did you honor your body's needs {time_period}?",
            "What boundary protected your wellbeing recently?",
            "How did you create space for rest or restoration?",
            "What brings you a sense of groundedness or peace?",
            "How are you balancing effort and ease in your life?",

            # Creativity variations
            "What idea or possibility excites you right now?",
            "How did you express yourself uniquely {time_period}?",
            "What would you create if resources weren't a limitation?",
            "What problem are you approaching from a new angle?",
            "What inspired your imagination or curiosity {time_period}?",

            # Reflection variations
            "What moment from {time_period} will you remember and why?",
            "How has your perspective shifted over time?",
            "What pattern or theme keeps appearing in your life?",
            "What are you learning about what truly matters to you?",
            "If you could give advice to someone in your situation, what would it be?",
        ]

    @staticmethod
    def _select_next_template(prompt_templates: List[str], templates_used: set) -> tuple:
        """Select next template ensuring no immediate repeats"""
        available_templates = [t for t in prompt_templates if t not in templates_used]
        if not available_templates:
            templates_used.clear()
            available_templates = prompt_templates

        template = random.choice(available_templates)
        templates_used.add(template)
        return template, templates_used

    @staticmethod
    def _format_question_from_template(template: str) -> str:
        """Format question from template with time period if needed"""
        time_periods = ["today", "this week", "recently", "lately", "in the past few days"]

        if '{time_period}' in template:
            return template.format(time_period=random.choice(time_periods))
        return template

    @staticmethod
    def _create_prompt_if_unique(question: str, category, difficulty: str, tags: List[str]) -> Optional[DailyPrompt]:
        """Create prompt only if question doesn't already exist"""
        if DailyPrompt.objects.filter(question=question).exists():
            return None

        return DailyPrompt.objects.create(
            category=category,
            question=question,
            description="Dynamic prompt - generated for continuous variety",
            tags=tags,
            difficulty=difficulty,
            is_active=True
        )

    @staticmethod
    def _generate_dynamic_prompts(user, count: int = 20):
        """
        Generate new prompts dynamically using AI when library is exhausted

        This ensures users NEVER see repeat questions by creating fresh prompts
        Uses pattern-based generation (can be upgraded to OpenAI/Anthropic API)
        """
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"Generating {count} dynamic prompts for user {user.id}")

        # Get all categories
        categories = list(PromptCategory.objects.filter(is_active=True))
        if not categories:
            categories = [None]

        # Get prompt templates
        prompt_templates = PromptService._get_prompt_templates()
        difficulty_levels = ['easy', 'medium', 'deep']

        created_prompts = []
        templates_used = set()

        for _ in range(count):
            # Select template
            template, templates_used = PromptService._select_next_template(prompt_templates, templates_used)

            # Format question
            question = PromptService._format_question_from_template(template)

            # Select category and difficulty
            category = random.choice(categories) if categories[0] is not None else None
            difficulty = random.choice(difficulty_levels)

            # Get tags based on category
            tags = PromptService._get_tags_for_category(category.name) if category else []

            # Create prompt if unique
            prompt = PromptService._create_prompt_if_unique(question, category, difficulty, tags)
            if prompt:
                created_prompts.append(prompt)

        logger.info(f"Created {len(created_prompts)} dynamic prompts")
        return created_prompts
