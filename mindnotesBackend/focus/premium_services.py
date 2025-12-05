"""
Premium Focus Programs Service Layer
Handles business logic for:
- 5-Minute Morning Charge
- Brain Dump Reset
- Gratitude Pause

Coordinates between PostgreSQL (reference data) and MongoDB (session data)
"""

from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db import transaction
from subscriptions.models import Subscription
from .models import (
    FocusProgram,
    BrainDumpCategory,
    PremiumProgramTrial
)
from .mongo_models import (
    MorningChargeSessionMongo,
    BrainDumpSessionMongo,
    BrainDumpThoughtEmbed,
    GratitudePauseSessionMongo,
    PremiumProgramStreakMongo
)


class PremiumAccessService:
    """Handle premium program access control and trial management"""

    @staticmethod
    def check_premium_access(user):
        """
        Check if user has access to premium programs
        Returns: (has_access: bool, access_type: str, trial_info: dict)
        access_type: 'paid', 'trial', or 'expired'
        """
        # Check if user has active paid subscription
        try:
            subscription = Subscription.objects.get(user=user)
            if subscription.is_pro():
                return True, 'paid', {
                    'plan': subscription.get_plan_display_name(),
                    'expires_at': subscription.expires_at
                }
        except Subscription.DoesNotExist:
            pass

        # Check trial status
        trial_info = PremiumAccessService.get_or_create_trial(user)

        if trial_info['is_active']:
            return True, 'trial', trial_info
        else:
            return False, 'expired', trial_info

    @staticmethod
    def get_or_create_trial(user):
        """Get or create trial for user"""
        trial, created = PremiumProgramTrial.objects.get_or_create(
            user=user,
            defaults={
                'trial_ends_at': timezone.now() + timedelta(days=7)
            }
        )

        is_active = trial.is_trial_active()

        # If trial just expired, mark it
        if not is_active and not trial.trial_expired:
            trial.trial_expired = True
            trial.save()

        return {
            'is_active': is_active,
            'trial_started_at': trial.trial_started_at,
            'trial_ends_at': trial.trial_ends_at,
            'days_remaining': trial.days_remaining(),
            'morning_charge_count': trial.morning_charge_count,
            'brain_dump_count': trial.brain_dump_count,
            'gratitude_pause_count': trial.gratitude_pause_count,
            'trial_expired': trial.trial_expired,
            'converted_to_paid': trial.converted_to_paid
        }

    @staticmethod
    def increment_program_usage(user, program_type):
        """
        Increment usage count for a program type during trial
        program_type: 'morning_charge', 'brain_dump', or 'gratitude_pause'
        """
        trial = PremiumProgramTrial.objects.filter(user=user).first()
        if trial:
            if program_type == 'morning_charge':
                trial.morning_charge_count += 1
            elif program_type == 'brain_dump':
                trial.brain_dump_count += 1
            elif program_type == 'gratitude_pause':
                trial.gratitude_pause_count += 1
            trial.save()

    @staticmethod
    def convert_trial_to_paid(user):
        """Mark trial as converted when user subscribes"""
        trial = PremiumProgramTrial.objects.filter(user=user).first()
        if trial:
            trial.converted_to_paid = True
            trial.converted_at = timezone.now()
            trial.save()


class MorningChargeService:
    """Service for 5-Minute Morning Charge program"""

    @staticmethod
    def start_session(user_id, session_date=None):
        """
        Start a new Morning Charge session or get today's session
        Returns the session object
        """
        if session_date is None:
            session_date = date.today()
        elif isinstance(session_date, datetime):
            session_date = session_date.date()

        # Check if session already exists for today
        existing_session = MorningChargeSessionMongo.objects(
            user_id=user_id,
            session_date=session_date
        ).first()

        if existing_session:
            return existing_session

        # Create new session
        session = MorningChargeSessionMongo(
            user_id=user_id,
            session_date=session_date
        )
        session.save()

        return session

    @staticmethod
    def complete_breathing(session_id, duration_seconds):
        """Complete the breathing step"""
        session = MorningChargeSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.breathing_completed = True
        session.breathing_completed_at = datetime.utcnow()
        session.breathing_duration_seconds = duration_seconds
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_gratitude(session_id, gratitude_text=None, voice_note_url=None):
        """Save gratitude text or voice note"""
        session = MorningChargeSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        if gratitude_text:
            session.gratitude_text = gratitude_text
        if voice_note_url:
            session.gratitude_voice_note_url = voice_note_url

        session.gratitude_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_affirmation(session_id, affirmation_text, is_favorite=False):
        """Save positive affirmation"""
        session = MorningChargeSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.affirmation_text = affirmation_text
        session.affirmation_is_favorite = is_favorite
        session.affirmation_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_clarity_prompt(session_id, question, answer):
        """Save daily clarity prompt response"""
        session = MorningChargeSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.clarity_prompt_question = question
        session.clarity_prompt_answer = answer
        session.clarity_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def complete_charge_close(session_id):
        """Complete the charge close step"""
        session = MorningChargeSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.charge_close_completed = True
        session.charge_close_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def complete_session(session_id, total_duration_seconds):
        """Mark session as completed and update streaks"""
        session = MorningChargeSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.is_completed = True
        session.completed_at = datetime.utcnow()
        session.total_duration_seconds = total_duration_seconds
        session.updated_at = datetime.utcnow()

        # Update streak
        streak_tracker = PremiumProgramStreakMongo.objects(user_id=session.user_id).first()
        if not streak_tracker:
            streak_tracker = PremiumProgramStreakMongo(user_id=session.user_id)
            streak_tracker.save()

        current_streak = streak_tracker.update_streak('morning_charge', session.session_date)
        session.current_streak = current_streak
        session.save()

        # Award badges
        MorningChargeService._award_badges(streak_tracker, current_streak)

        return session

    @staticmethod
    def _award_badges(streak_tracker, current_streak):
        """Award badges based on streak milestones"""
        badges_to_award = []

        if current_streak == 1:
            badges_to_award.append(("Pulse Starter", "Completed your first Morning Charge"))
        elif current_streak == 7:
            badges_to_award.append(("Steady Beat", "7-day Morning Charge streak"))
        elif current_streak == 30:
            badges_to_award.append(("Flow Charger", "30-day Morning Charge streak"))
        elif current_streak == 100:
            badges_to_award.append(("Morning Warrior", "100-day Morning Charge streak"))

        for badge_name, description in badges_to_award:
            streak_tracker.add_badge(badge_name, 'morning_charge', description)

    @staticmethod
    def get_session_history(user_id, limit=30):
        """Get user's recent Morning Charge sessions"""
        sessions = MorningChargeSessionMongo.objects(
            user_id=user_id
        ).order_by('-session_date').limit(limit)

        return list(sessions)

    @staticmethod
    def get_today_session(user_id):
        """Get today's session if it exists"""
        return MorningChargeSessionMongo.objects(
            user_id=user_id,
            session_date=date.today()
        ).first()


class BrainDumpService:
    """Service for Brain Dump Reset program"""

    @staticmethod
    def get_categories():
        """Get all brain dump categories"""
        return list(BrainDumpCategory.objects.all().order_by('order'))

    @staticmethod
    def start_session(user_id, session_date=None):
        """Start a new Brain Dump session"""
        if session_date is None:
            session_date = date.today()
        elif isinstance(session_date, datetime):
            session_date = session_date.date()

        # Check if session already exists for today
        existing_session = BrainDumpSessionMongo.objects(
            user_id=user_id,
            session_date=session_date
        ).first()

        if existing_session:
            return existing_session

        # Create new session
        session = BrainDumpSessionMongo(
            user_id=user_id,
            session_date=session_date
        )
        session.save()

        return session

    @staticmethod
    def complete_settle_in(session_id):
        """Complete the settle in step"""
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.settle_in_completed = True
        session.settle_in_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def add_thoughts(session_id, thoughts_list):
        """
        Add thoughts to the dump
        thoughts_list: [{"text": "...", "category_id": None, "category_name": None}]
        """
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        for idx, thought_data in enumerate(thoughts_list):
            thought = BrainDumpThoughtEmbed(
                thought_text=thought_data['text'],
                category_id=thought_data.get('category_id'),
                category_name=thought_data.get('category_name'),
                order=idx
            )
            session.dump_thoughts.append(thought)

        session.total_thoughts_count = len(session.dump_thoughts)
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_guided_responses(session_id, response_1=None, response_2=None, response_3=None):
        """Save guided question responses"""
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        if response_1:
            session.guided_question_1_response = response_1
        if response_2:
            session.guided_question_2_response = response_2
        if response_3:
            session.guided_question_3_response = response_3

        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def categorize_thoughts(session_id, categorized_thoughts):
        """
        Update categorization for thoughts
        categorized_thoughts: [{"index": 0, "category_id": 1, "category_name": "Actionable Task"}]
        """
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        # Update each thought's category
        category_counts = {}
        for cat_data in categorized_thoughts:
            idx = cat_data['index']
            if 0 <= idx < len(session.dump_thoughts):
                session.dump_thoughts[idx].category_id = cat_data['category_id']
                session.dump_thoughts[idx].category_name = cat_data['category_name']

                # Count categories
                cat_id = cat_data['category_id']
                category_counts[cat_id] = category_counts.get(cat_id, 0) + 1

        session.category_distribution = category_counts
        session.categorize_completed = True
        session.categorize_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def choose_focus_task(session_id, task_text, task_category_id):
        """Choose one task to focus on from actionable items"""
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.chosen_task_text = task_text
        session.chosen_task_category_id = task_category_id
        session.chosen_task_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def complete_close_breathe(session_id):
        """Complete the close and breathe step"""
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.close_breathe_completed = True
        session.close_breathe_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def complete_session(session_id, total_duration_seconds):
        """Mark session as completed and update streaks"""
        session = BrainDumpSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.is_completed = True
        session.completed_at = datetime.utcnow()
        session.total_duration_seconds = total_duration_seconds
        session.updated_at = datetime.utcnow()

        # Update streak
        streak_tracker = PremiumProgramStreakMongo.objects(user_id=session.user_id).first()
        if not streak_tracker:
            streak_tracker = PremiumProgramStreakMongo(user_id=session.user_id)
            streak_tracker.save()

        current_streak = streak_tracker.update_streak('brain_dump', session.session_date)
        session.current_streak = current_streak
        session.save()

        # Award badges
        BrainDumpService._award_badges(streak_tracker, current_streak)

        return session

    @staticmethod
    def _award_badges(streak_tracker, current_streak):
        """Award badges based on streak milestones"""
        badges_to_award = []

        if current_streak == 3:
            badges_to_award.append(("Mind Declutterer", "3-day Brain Dump streak"))
        elif current_streak == 7:
            badges_to_award.append(("Clear Thinker", "7-day Brain Dump streak"))
        elif current_streak == 30:
            badges_to_award.append(("Mental Organizer", "30-day Brain Dump streak"))

        for badge_name, description in badges_to_award:
            streak_tracker.add_badge(badge_name, 'brain_dump', description)

    @staticmethod
    def get_session_history(user_id, limit=30):
        """Get user's recent Brain Dump sessions"""
        sessions = BrainDumpSessionMongo.objects(
            user_id=user_id
        ).order_by('-session_date').limit(limit)

        return list(sessions)

    @staticmethod
    def get_today_session(user_id):
        """Get today's session if it exists"""
        return BrainDumpSessionMongo.objects(
            user_id=user_id,
            session_date=date.today()
        ).first()


class GratitudePauseService:
    """Service for Gratitude Pause program"""

    @staticmethod
    def start_session(user_id, session_date=None):
        """Start a new Gratitude Pause session"""
        if session_date is None:
            session_date = date.today()
        elif isinstance(session_date, datetime):
            session_date = session_date.date()

        # Check if session already exists for today
        existing_session = GratitudePauseSessionMongo.objects(
            user_id=user_id,
            session_date=session_date
        ).first()

        if existing_session:
            return existing_session

        # Create new session
        session = GratitudePauseSessionMongo(
            user_id=user_id,
            session_date=session_date
        )
        session.save()

        return session

    @staticmethod
    def complete_arrive(session_id):
        """Complete the arrive step"""
        session = GratitudePauseSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.arrive_completed = True
        session.arrive_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_three_gratitudes(session_id, gratitude_1, gratitude_2, gratitude_3):
        """Save the three gratitudes"""
        session = GratitudePauseSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.gratitude_1 = gratitude_1
        session.gratitude_2 = gratitude_2
        session.gratitude_3 = gratitude_3
        session.list_three_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_deep_dive(session_id, selected_index, deep_dive_responses):
        """
        Save deep dive responses
        selected_index: 1, 2, or 3
        deep_dive_responses: {
            "precise": "...",
            "why_matters": "...",
            "who_made_possible": "...",
            "sensory_moment": "...",
            "gratitude_line": "..."
        }
        """
        session = GratitudePauseSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        # Get selected gratitude text
        if selected_index == 1:
            session.selected_gratitude_text = session.gratitude_1
        elif selected_index == 2:
            session.selected_gratitude_text = session.gratitude_2
        elif selected_index == 3:
            session.selected_gratitude_text = session.gratitude_3

        session.selected_gratitude_index = selected_index
        session.deep_dive_1_precise = deep_dive_responses.get('precise', '')
        session.deep_dive_2_why_matters = deep_dive_responses.get('why_matters', '')
        session.deep_dive_3_who_made_possible = deep_dive_responses.get('who_made_possible', '')
        session.deep_dive_4_sensory_moment = deep_dive_responses.get('sensory_moment', '')
        session.deep_dive_5_gratitude_line = deep_dive_responses.get('gratitude_line', '')
        session.deep_dive_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def save_expression(session_id, action, notes=None):
        """Save expression action"""
        session = GratitudePauseSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.expression_action = action
        if notes:
            session.expression_notes = notes
        session.expression_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def complete_anchor(session_id):
        """Complete the anchor step"""
        session = GratitudePauseSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.anchor_completed = True
        session.anchor_completed_at = datetime.utcnow()
        session.updated_at = datetime.utcnow()
        session.save()

        return session

    @staticmethod
    def complete_session(session_id, total_duration_seconds):
        """Mark session as completed and update streaks"""
        session = GratitudePauseSessionMongo.objects(id=session_id).first()
        if not session:
            raise ValueError("Session not found")

        session.is_completed = True
        session.completed_at = datetime.utcnow()
        session.total_duration_seconds = total_duration_seconds
        session.updated_at = datetime.utcnow()

        # Update streak
        streak_tracker = PremiumProgramStreakMongo.objects(user_id=session.user_id).first()
        if not streak_tracker:
            streak_tracker = PremiumProgramStreakMongo(user_id=session.user_id)
            streak_tracker.save()

        current_streak = streak_tracker.update_streak('gratitude_pause', session.session_date)
        session.current_streak = current_streak
        session.save()

        # Award badges
        GratitudePauseService._award_badges(streak_tracker, current_streak)

        return session

    @staticmethod
    def _award_badges(streak_tracker, current_streak):
        """Award badges based on streak milestones"""
        badges_to_award = []

        if current_streak == 1:
            badges_to_award.append(("Gratitude Beginner", "Completed your first Gratitude Pause"))
        elif current_streak == 7:
            badges_to_award.append(("Thankful Heart", "7-day Gratitude Pause streak"))
        elif current_streak == 30:
            badges_to_award.append(("Gratitude Master", "30-day Gratitude Pause streak"))

        for badge_name, description in badges_to_award:
            streak_tracker.add_badge(badge_name, 'gratitude_pause', description)

    @staticmethod
    def get_session_history(user_id, limit=30):
        """Get user's recent Gratitude Pause sessions"""
        sessions = GratitudePauseSessionMongo.objects(
            user_id=user_id
        ).order_by('-session_date').limit(limit)

        return list(sessions)

    @staticmethod
    def get_today_session(user_id):
        """Get today's session if it exists"""
        return GratitudePauseSessionMongo.objects(
            user_id=user_id,
            session_date=date.today()
        ).first()


class PremiumProgramAnalyticsService:
    """Analytics and insights for premium programs"""

    @staticmethod
    def get_user_stats(user_id):
        """Get comprehensive stats for a user across all premium programs"""
        streak_tracker = PremiumProgramStreakMongo.objects(user_id=user_id).first()

        if not streak_tracker:
            return {
                'morning_charge': {'current_streak': 0, 'longest_streak': 0, 'total_sessions': 0},
                'brain_dump': {'current_streak': 0, 'longest_streak': 0, 'total_sessions': 0},
                'gratitude_pause': {'current_streak': 0, 'longest_streak': 0, 'total_sessions': 0},
                'total_sessions': 0,
                'badges': []
            }

        return {
            'morning_charge': {
                'current_streak': streak_tracker.morning_charge_current_streak,
                'longest_streak': streak_tracker.morning_charge_longest_streak,
                'total_sessions': streak_tracker.morning_charge_total_sessions,
                'last_activity': streak_tracker.morning_charge_last_activity
            },
            'brain_dump': {
                'current_streak': streak_tracker.brain_dump_current_streak,
                'longest_streak': streak_tracker.brain_dump_longest_streak,
                'total_sessions': streak_tracker.brain_dump_total_sessions,
                'last_activity': streak_tracker.brain_dump_last_activity
            },
            'gratitude_pause': {
                'current_streak': streak_tracker.gratitude_pause_current_streak,
                'longest_streak': streak_tracker.gratitude_pause_longest_streak,
                'total_sessions': streak_tracker.gratitude_pause_total_sessions,
                'last_activity': streak_tracker.gratitude_pause_last_activity
            },
            'total_sessions': streak_tracker.total_premium_sessions,
            'first_session_date': streak_tracker.first_session_date,
            'badges': streak_tracker.badges
        }
