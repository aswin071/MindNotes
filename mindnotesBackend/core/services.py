"""
Hybrid Database Service Layer
Handles operations between PostgreSQL and MongoDB
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from django.contrib.auth import get_user_model
from django.db import transaction

# MongoDB Models
from journals.mongo_models import JournalEntryMongo, PhotoEmbed, VoiceNoteEmbed, PromptResponseEmbed
from moods.mongo_models import MoodEntryMongo
from focus.mongo_models import FocusSessionMongo
from prompts.mongo_models import DailyPromptSetMongo, PromptResponseMongo
from analytics.mongo_models import UserAnalyticsMongo, DailyActivityLogMongo
from exports.mongo_models import ExportRequestMongo

User = get_user_model()


class JournalService:
    """
    Service layer to handle hybrid database operations for journals
    """
    
    @staticmethod
    def create_journal_entry(user, data: Dict[str, Any]) -> JournalEntryMongo:
        """
        Create journal entry in MongoDB with PostgreSQL references
        """
        from journals.models import Tag  # PostgreSQL model

        # Handle tags - either by IDs or by names (auto-create)
        tag_ids = data.get('tag_ids', [])
        tag_names = data.get('tag_names', [])

        # If tag names provided, get or create tags
        if tag_names:
            for tag_name in tag_names:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_name,
                    defaults={'color': '#3B82F6'}
                )
                if tag.id not in tag_ids:
                    tag_ids.append(tag.id)

        # Validate tag IDs belong to user
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids, user=user)
            tag_ids = list(tags.values_list('id', flat=True))

        # Create embedded documents
        photos = []
        for photo_data in data.get('photos', []):
            photos.append(PhotoEmbed(**photo_data))

        voice_notes = []
        for voice_data in data.get('voice_notes', []):
            voice_notes.append(VoiceNoteEmbed(**voice_data))

        prompt_responses = []
        for prompt_data in data.get('prompt_responses', []):
            prompt_responses.append(PromptResponseEmbed(**prompt_data))

        # Create MongoDB document
        # Note: user.id is an integer (BigAutoField) from PostgreSQL User model
        entry = JournalEntryMongo(
            user_id=user.id,
            title=data.get('title', ''),
            content=data.get('content', ''),
            entry_type=data.get('entry_type', 'text'),
            entry_date=data.get('entry_date', datetime.utcnow()),
            tag_ids=tag_ids,
            privacy=data.get('privacy', 'private'),
            location_name=data.get('location_name', ''),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            weather=data.get('weather', ''),
            temperature=data.get('temperature'),
            photos=photos,
            voice_notes=voice_notes,
            prompt_responses=prompt_responses,
        )
        entry.save()

        # Update PostgreSQL user stats
        with transaction.atomic():
            profile = user.profile
            profile.total_entries += 1
            profile.save(update_fields=['total_entries'])

        return entry
    
    @staticmethod
    def get_user_entries(user, filters: Optional[Dict[str, Any]] = None) -> List[JournalEntryMongo]:
        """
        Get journal entries with filters
        """
        query = {'user_id': user.id}
        
        if filters:
            if filters.get('date_from'):
                query['entry_date__gte'] = filters['date_from']
            if filters.get('date_to'):
                query['entry_date__lte'] = filters['date_to']
            if filters.get('is_favorite'):
                query['is_favorite'] = True
            if filters.get('tag_ids'):
                query['tag_ids__in'] = filters['tag_ids']
            if filters.get('entry_type'):
                query['entry_type'] = filters['entry_type']
        
        return list(JournalEntryMongo.objects(**query).order_by('-entry_date'))
    
    @staticmethod
    def search_entries(user, search_query: str) -> List[JournalEntryMongo]:
        """
        Full-text search in MongoDB
        """
        return list(JournalEntryMongo.objects(
            user_id=user.id
        ).search_text(search_query).order_by('$text_score'))
    
    @staticmethod
    def update_entry(entry_id: str, user, data: Dict[str, Any]) -> Optional[JournalEntryMongo]:
        """
        Update journal entry
        """
        try:
            entry = JournalEntryMongo.objects.get(id=entry_id, user_id=user.id)
            
            # Update fields
            for field, value in data.items():
                if hasattr(entry, field):
                    setattr(entry, field, value)
            
            # Update version and edit history
            entry.version += 1
            entry.edit_history.append({
                'edited_at': datetime.utcnow(),
                'changes': data
            })
            
            entry.save()
            return entry
        except JournalEntryMongo.DoesNotExist:
            return None


class MoodService:
    """
    Service layer for mood entries
    """
    
    @staticmethod
    def create_mood_entry(user, data: Dict[str, Any]) -> MoodEntryMongo:
        """
        Create mood entry in MongoDB
        """
        entry = MoodEntryMongo(
            user_id=user.id,
            journal_entry_id=data.get('journal_entry_id'),
            category_id=data.get('category_id'),
            custom_category_id=data.get('custom_category_id'),
            category_name=data.get('category_name'),
            emoji=data.get('emoji'),
            intensity=data.get('intensity'),
            note=data.get('note'),
            factors=data.get('factors', []),
            recorded_at=data.get('recorded_at', datetime.utcnow()),
            context=data.get('context', {})
        )
        entry.save()
        return entry
    
    @staticmethod
    def get_user_moods(user, filters: Optional[Dict[str, Any]] = None) -> List[MoodEntryMongo]:
        """
        Get mood entries with filters
        """
        query = {'user_id': user.id}
        
        if filters:
            if filters.get('date_from'):
                query['recorded_at__gte'] = filters['date_from']
            if filters.get('date_to'):
                query['recorded_at__lte'] = filters['date_to']
            if filters.get('category_id'):
                query['category_id'] = filters['category_id']
        
        return list(MoodEntryMongo.objects(**query).order_by('-recorded_at'))


class FocusService:
    """
    Service layer for focus sessions
    """
    
    @staticmethod
    def create_focus_session(user, data: Dict[str, Any]) -> FocusSessionMongo:
        """
        Create focus session in MongoDB
        """
        session = FocusSessionMongo(
            user_id=user.id,
            session_type=data.get('session_type', 'custom'),
            planned_duration_seconds=data.get('planned_duration_seconds'),
            task_description=data.get('task_description'),
            program_id=data.get('program_id'),
            program_day_id=data.get('program_day_id'),
            started_at=data.get('started_at', datetime.utcnow()),
            tags=data.get('tags', [])
        )
        session.save()
        return session
    
    @staticmethod
    def update_session_tick(session_id: str, user, duration_seconds: int) -> Optional[FocusSessionMongo]:
        """
        Update session with real-time tick
        """
        try:
            session = FocusSessionMongo.objects.get(id=session_id, user_id=user.id)
            session.actual_duration_seconds = duration_seconds
            session.last_tick_at = datetime.utcnow()
            session.save()
            return session
        except FocusSessionMongo.DoesNotExist:
            return None
    
    @staticmethod
    def complete_session(session_id: str, user, data: Dict[str, Any]) -> Optional[FocusSessionMongo]:
        """
        Complete focus session
        """
        try:
            session = FocusSessionMongo.objects.get(id=session_id, user_id=user.id)
            session.status = 'completed'
            session.ended_at = datetime.utcnow()
            session.productivity_rating = data.get('productivity_rating')
            session.notes = data.get('notes')
            session.save()
            return session
        except FocusSessionMongo.DoesNotExist:
            return None


class PromptService:
    """
    Service layer for prompts
    """
    
    @staticmethod
    def create_daily_prompt_set(user, date: date, prompts: List[Dict[str, Any]]) -> DailyPromptSetMongo:
        """
        Create daily prompt set
        """
        prompt_set = DailyPromptSetMongo(
            user_id=user.id,
            date=date,
            prompts=prompts,
            last_interaction_at=datetime.utcnow()
        )
        prompt_set.save()
        return prompt_set
    
    @staticmethod
    def submit_prompt_response(user, data: Dict[str, Any]) -> PromptResponseMongo:
        """
        Submit prompt response
        """
        response = PromptResponseMongo(
            user_id=user.id,
            prompt_id=data.get('prompt_id'),
            daily_set_date=data.get('daily_set_date'),
            response=data.get('response'),
            word_count=len(data.get('response', '').split()),
            time_spent_seconds=data.get('time_spent_seconds', 0),
            mood_at_response=data.get('mood_at_response'),
            location=data.get('location', {})
        )
        response.save()
        return response


class AnalyticsService:
    """
    Service layer for analytics
    """
    
    @staticmethod
    def get_user_analytics(user) -> Optional[UserAnalyticsMongo]:
        """
        Get user analytics
        """
        try:
            return UserAnalyticsMongo.objects.get(user_id=user.id)
        except UserAnalyticsMongo.DoesNotExist:
            return None
    
    @staticmethod
    def update_daily_activity(user, date: date, activity_data: Dict[str, Any]) -> DailyActivityLogMongo:
        """
        Update daily activity log
        """
        log, created = DailyActivityLogMongo.objects.get_or_create(
            user_id=user.id,
            date=date,
            defaults=activity_data
        )
        
        if not created:
            # Update existing log
            for key, value in activity_data.items():
                setattr(log, key, value)
            log.save()
        
        return log


class ExportService:
    """
    Service layer for exports
    """

    @staticmethod
    def create_export_request(user, data: Dict[str, Any]) -> ExportRequestMongo:
        """
        Create export request
        """
        export_request = ExportRequestMongo(
            user_id=user.id,
            export_request_id=data.get('export_request_id'),
            export_type=data.get('export_type'),
            date_range_start=data.get('date_range_start'),
            date_range_end=data.get('date_range_end'),
            format=data.get('format', 'pdf')
        )
        export_request.save()
        return export_request

    @staticmethod
    def collect_export_data(export_request_id: str) -> Dict[str, Any]:
        """
        Collect data for export
        """
        try:
            export_request = ExportRequestMongo.objects.get(id=export_request_id)

            # Collect journal entries
            journal_query = {'user_id': export_request.user_id}
            if export_request.date_range_start:
                journal_query['entry_date__gte'] = export_request.date_range_start
            if export_request.date_range_end:
                journal_query['entry_date__lte'] = export_request.date_range_end

            entries = list(JournalEntryMongo.objects(**journal_query))
            export_request.collected_entries = [entry.to_mongo().to_dict() for entry in entries]

            # Collect mood entries
            mood_query = {'user_id': export_request.user_id}
            if export_request.date_range_start:
                mood_query['recorded_at__gte'] = export_request.date_range_start
            if export_request.date_range_end:
                mood_query['recorded_at__lte'] = export_request.date_range_end

            moods = list(MoodEntryMongo.objects(**mood_query))
            export_request.collected_moods = [mood.to_mongo().to_dict() for mood in moods]

            # Collect focus sessions
            focus_query = {'user_id': export_request.user_id}
            if export_request.date_range_start:
                focus_query['started_at__gte'] = export_request.date_range_start
            if export_request.date_range_end:
                focus_query['started_at__lte'] = export_request.date_range_end

            sessions = list(FocusSessionMongo.objects(**focus_query))
            export_request.collected_sessions = [session.to_mongo().to_dict() for session in sessions]

            export_request.save()
            return {
                'entries': len(entries),
                'moods': len(moods),
                'sessions': len(sessions)
            }
        except ExportRequestMongo.DoesNotExist:
            return None


class ProfileService:
    """
    Service layer for profile data aggregation
    """

    @staticmethod
    def get_profile_stats(user) -> Dict[str, Any]:
        """
        Aggregate profile statistics from PostgreSQL and MongoDB
        """
        from authentication.models import UserProfile, UserStreak
        from subscriptions.models import Subscription
        from django.db.models import Count

        # Get PostgreSQL data
        profile = user.profile

        # Get or create subscription
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={'plan': 'free', 'status': 'active'}
        )

        # Calculate current streak
        current_streak = ProfileService._calculate_current_streak(user)

        # Count total entries from MongoDB
        total_entries = JournalEntryMongo.objects(user_id=user.id).count()

        # Count total focus minutes from MongoDB
        completed_sessions = FocusSessionMongo.objects(
            user_id=user.id,
            status='completed'
        )
        total_focus_minutes = sum(
            session.actual_duration_seconds // 60
            for session in completed_sessions
        )

        # Calculate days using app
        days_using_app = (datetime.utcnow().date() - user.created_at.date()).days

        return {
            'user_id': str(user.id),
            'email': user.email,
            'full_name': user.full_name or '',
            'avatar': user.avatar.url if user.avatar else None,
            'bio': user.bio,

            # Statistics
            'total_entries': total_entries,
            'current_streak': current_streak,
            'longest_streak': profile.longest_streak,
            'total_focus_minutes': total_focus_minutes,
            'days_using_app': days_using_app,

            # Subscription
            'is_pro': subscription.is_pro(),
            'subscription_plan': subscription.get_plan_display_name(),
            'subscription_status': subscription.status,
            'subscription_expires_at': subscription.expires_at,

            # Preferences
            'timezone': user.timezone,
            'language': user.language,
            'daily_reminder': user.daily_reminder,
            'reminder_time': str(user.reminder_time) if user.reminder_time else None,
            'email_notifications': user.email_notifications,
            'push_notifications': user.push_notifications,

            # Profile settings
            'default_entry_privacy': profile.default_entry_privacy,
            'default_focus_duration': profile.default_focus_duration,
            'mood_tracking_enabled': profile.mood_tracking_enabled,

            # Account info
            'is_verified': user.is_verified,
            'onboarding_completed': user.onboarding_completed,
            'created_at': user.created_at,
            'last_login_at': user.last_login_at,
        }

    @staticmethod
    def _calculate_current_streak(user) -> int:
        """
        Calculate current streak based on journal entries
        """
        from datetime import timedelta

        # Get all journal entry dates from MongoDB
        entries = JournalEntryMongo.objects(user_id=user.id).only('entry_date').order_by('-entry_date')

        if not entries:
            return 0

        # Get unique dates
        unique_dates = sorted(set(entry.entry_date.date() for entry in entries), reverse=True)

        # Calculate streak
        streak = 0
        today = datetime.utcnow().date()

        for i, entry_date in enumerate(unique_dates):
            if i == 0:
                # Check if most recent entry is today or yesterday
                if entry_date == today or entry_date == today - timedelta(days=1):
                    streak = 1
                else:
                    break
            else:
                # Check if dates are consecutive
                expected_date = unique_dates[i-1] - timedelta(days=1)
                if entry_date == expected_date:
                    streak += 1
                else:
                    break

        # Update longest streak if needed
        profile = user.profile
        if streak > profile.longest_streak:
            profile.longest_streak = streak
            profile.save(update_fields=['longest_streak'])

        # Update current streak
        if profile.current_streak != streak:
            profile.current_streak = streak
            profile.save(update_fields=['current_streak'])

        return streak


class DashboardService:
    """
    Service layer for Home Dashboard data aggregation
    Provides all data needed for the dashboard screen
    """

    @staticmethod
    def get_dashboard_data(user) -> Dict[str, Any]:
        """
        Aggregate all dashboard data from PostgreSQL and MongoDB
        Returns complete data for Home screen wireframe
        """
        from authentication.models import UserProfile
        from moods.models import MoodCategory
        from prompts.models import DailyPrompt
        from focus.models import UserFocusProgram, ProgramDay
        from datetime import date, timedelta

        # Get user profile for greeting
        profile = user.profile

        # 1. USER GREETING DATA
        greeting = DashboardService._get_greeting()
        current_streak = ProfileService._calculate_current_streak(user)

        # 2. PROMPT OF THE DAY
        prompt_data = DashboardService._get_daily_prompt(user)

        # 3. ACTIVE FOCUS PROGRAM
        focus_program_data = DashboardService._get_active_focus_program(user)

        # 4. MOOD OPTIONS (for "How are you feeling?")
        mood_options = DashboardService._get_mood_options()

        # 5. RECENT ACTIVITY (optional - for future enhancements)
        today_stats = DashboardService._get_today_stats(user)

        return {
            # Header section
            'greeting': greeting,
            'user': {
                'id': str(user.id),
                'full_name': user.full_name or user.email.split('@')[0],
                'avatar': user.avatar.url if user.avatar else None,
                'current_streak': current_streak,
            },

            # Quick Journal section (static - UI driven)
            'quick_journal_options': [
                {'type': 'voice', 'label': 'Voice', 'icon': '🎤'},
                {'type': 'speak', 'label': 'Speak', 'icon': '✍️'},
                {'type': 'photo', 'label': 'Photo', 'icon': '📷'},
            ],

            # Prompt of the Day section
            'prompt_of_the_day': prompt_data,

            # Focus Program section
            'active_focus_program': focus_program_data,

            # Mood tracker section
            'mood_options': mood_options,

            # Today's activity stats
            'today_stats': today_stats,

            # Metadata
            'fetched_at': datetime.utcnow().isoformat(),
        }

    @staticmethod
    def _get_greeting() -> str:
        """Get time-based greeting"""
        from datetime import datetime

        hour = datetime.now().hour

        if 5 <= hour < 12:
            return "Good Morning"
        elif 12 <= hour < 17:
            return "Good Afternoon"
        elif 17 <= hour < 22:
            return "Good Evening"
        else:
            return "Good Night"

    @staticmethod
    def _get_daily_prompt(user) -> Dict[str, Any]:
        """
        Get today's prompt for the user
        Creates or retrieves daily prompt set from MongoDB
        """
        from prompts.models import DailyPrompt
        from prompts.mongo_models import DailyPromptSetMongo
        from datetime import date
        import random

        today = date.today()

        # Check if user has a prompt set for today in MongoDB
        try:
            prompt_set = DailyPromptSetMongo.objects.get(
                user_id=user.id,
                date=today
            )

            # Get the first unanswered prompt
            answered_ids = prompt_set.completed_prompt_ids
            unanswered_prompts = [
                p for p in prompt_set.prompts
                if p.get('id') not in answered_ids
            ]

            if unanswered_prompts:
                current_prompt = unanswered_prompts[0]
                return {
                    'id': current_prompt['id'],
                    'question': current_prompt['question'],
                    'category': current_prompt.get('category', 'Reflection'),
                    'is_answered': False,
                    'total_prompts': len(prompt_set.prompts),
                    'answered_count': len(answered_ids),
                }
            else:
                # All prompts answered for today
                return {
                    'id': None,
                    'question': f"You've completed all prompts for today! 🎉",
                    'category': 'Completed',
                    'is_answered': True,
                    'total_prompts': len(prompt_set.prompts),
                    'answered_count': len(answered_ids),
                }

        except DailyPromptSetMongo.DoesNotExist:
            # Generate new prompt set for today
            all_prompts = list(DailyPrompt.objects.filter(is_active=True).values(
                'id', 'question', 'category__name', 'difficulty'
            ))

            if not all_prompts:
                return {
                    'id': None,
                    'question': 'No prompts available yet.',
                    'category': None,
                    'is_answered': False,
                    'total_prompts': 0,
                    'answered_count': 0,
                }

            # Select 3 random prompts for the day
            daily_prompts = random.sample(all_prompts, min(3, len(all_prompts)))

            # Create prompt set in MongoDB
            prompt_set = DailyPromptSetMongo(
                user_id=user.id,
                date=today,
                prompts=[{
                    'id': p['id'],
                    'question': p['question'],
                    'category': p['category__name'] or 'Reflection',
                    'difficulty': p['difficulty']
                } for p in daily_prompts],
                completed_prompt_ids=[],
                completed_count=0,
                generated_at=datetime.utcnow()
            )
            prompt_set.save()

            # Return first prompt
            first_prompt = daily_prompts[0]
            return {
                'id': first_prompt['id'],
                'question': first_prompt['question'],
                'category': first_prompt['category__name'] or 'Reflection',
                'is_answered': False,
                'total_prompts': len(daily_prompts),
                'answered_count': 0,
            }

    @staticmethod
    def _get_active_focus_program(user) -> Optional[Dict[str, Any]]:
        """
        Get user's active focus program with current day progress
        """
        from focus.models import UserFocusProgram, ProgramDay

        try:
            # Get active program
            user_program = UserFocusProgram.objects.filter(
                user=user,
                status='in_progress'
            ).select_related('program').first()

            if not user_program:
                return None

            # Get current day details
            current_day = ProgramDay.objects.filter(
                program=user_program.program,
                day_number=user_program.current_day
            ).first()

            # Calculate progress
            total_days = user_program.program.duration_days
            progress_percentage = (user_program.current_day / total_days) * 100

            # Get today's completed focus sessions from MongoDB
            from datetime import date
            today = date.today()

            today_sessions = FocusSessionMongo.objects(
                user_id=user.id,
                program_id=user_program.program.id,
                started_at__gte=datetime.combine(today, datetime.min.time()),
                status='completed'
            )

            today_minutes = sum(s.actual_duration_seconds // 60 for s in today_sessions)
            target_minutes = current_day.focus_duration if current_day else 0

            return {
                'id': user_program.id,
                'program_name': user_program.program.name,
                'program_type': user_program.program.program_type,
                'current_day': user_program.current_day,
                'total_days': total_days,
                'progress_percentage': round(progress_percentage, 1),
                'current_day_title': current_day.title if current_day else f"Day {user_program.current_day}",
                'current_day_description': current_day.description if current_day else "",
                'target_focus_minutes': target_minutes,
                'completed_focus_minutes_today': today_minutes,
                'status': user_program.status,
                'started_at': user_program.started_at.isoformat() if user_program.started_at else None,
            }

        except Exception as e:
            return None

    @staticmethod
    def _get_mood_options() -> List[Dict[str, Any]]:
        """
        Get mood category options for mood tracker
        Returns the 5 main mood categories
        """
        from moods.models import MoodCategory

        # Get system mood categories
        moods = MoodCategory.objects.filter(
            is_active=True,
            is_system=True
        ).order_by('order')[:5]

        return [
            {
                'id': mood.id,
                'name': mood.name,
                'emoji': mood.emoji,
                'color': mood.color,
                'description': mood.description,
            }
            for mood in moods
        ]

    @staticmethod
    def _get_today_stats(user) -> Dict[str, Any]:
        """
        Get today's activity statistics
        """
        from datetime import date, datetime as dt

        today = date.today()
        today_start = dt.combine(today, dt.min.time())

        # Count today's journal entries
        today_entries = JournalEntryMongo.objects(
            user_id=user.id,
            entry_date__gte=today_start
        ).count()

        # Count today's mood logs
        today_moods = MoodEntryMongo.objects(
            user_id=user.id,
            recorded_at__gte=today_start
        ).count()

        # Count today's focus sessions
        today_focus = FocusSessionMongo.objects(
            user_id=user.id,
            started_at__gte=today_start
        ).count()

        return {
            'entries_today': today_entries,
            'moods_logged_today': today_moods,
            'focus_sessions_today': today_focus,
            'has_journaled_today': today_entries > 0,
        }
