"""
Hybrid Database Service Layer
Handles operations between PostgreSQL and MongoDB
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db import models
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import base64

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

        # Validate tag IDs belong to user (optimized query)
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids, user=user).only('id')
            tag_ids = list(tags.values_list('id', flat=True))

        # Create embedded documents
        photos = []
        for photo_data in data.get('photos', []):
            # Handle file upload if image_url is a file object
            if hasattr(photo_data.get('image_url'), 'read'):
                # It's an uploaded file
                image_file = photo_data.pop('image_url')

                # Option 1: Synchronous upload (current behavior)
                # Use this for immediate upload
                filename = f"media/journals/{user.id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image_file.name}"
                path = default_storage.save(filename, ContentFile(image_file.read()))
                photo_data['image_url'] = default_storage.url(path)

                # Option 2: Async upload (recommended for production)
                # Uncomment below and comment above for async processing:
                # from core.tasks import upload_file_to_storage
                # file_content = image_file.read()
                # file_content_b64 = base64.b64encode(file_content).decode('utf-8')
                # result = upload_file_to_storage.delay(file_content_b64, image_file.name, user.id)
                # photo_data['image_url'] = f'pending:{result.id}'  # Store task ID temporarily
                # photo_data['upload_status'] = 'pending'

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

        # Update PostgreSQL user stats (optimized with select_related)
        with transaction.atomic():
            from authentication.models import UserProfile
            UserProfile.objects.filter(user=user).update(
                total_entries=models.F('total_entries') + 1
            )

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


class FocusService:
    """
    Service layer for Focus Programs feature
    Handles business logic for program enrollment, daily progress, sessions, and analytics
    """

    @staticmethod
    def get_available_programs(user):
        """
        Get all available focus programs based on user's subscription
        Returns programs with enrollment status
        """
        from focus.models import FocusProgram, UserFocusProgram
        from subscriptions.models import Subscription

        # Check user's subscription status
        is_pro = False
        try:
            subscription = Subscription.objects.get(user=user)
            is_pro = subscription.is_pro()
        except Subscription.DoesNotExist:
            pass

        # Get all programs
        programs = FocusProgram.objects.filter(
            is_active=True
        ).order_by('order', 'duration_days')

        program_list = []
        for program in programs:
            # Check if user is enrolled
            enrollment = UserFocusProgram.objects.filter(
                user=user,
                program=program,
                status__in=['not_started', 'in_progress', 'paused']
            ).first()

            # Check if user can access this program
            can_access = True if not program.is_pro_only else is_pro

            program_data = {
                'id': program.id,
                'name': program.name,
                'program_type': program.program_type,
                'description': program.description,
                'duration_days': program.duration_days,
                'objectives': program.objectives,
                'is_pro_only': program.is_pro_only,
                'can_access': can_access,
                'icon': program.icon,
                'color': program.color,
                'cover_image': program.cover_image.url if program.cover_image else None,
                'is_enrolled': enrollment is not None,
                'enrollment_id': enrollment.id if enrollment else None,
                'enrollment_status': enrollment.status if enrollment else None,
                'current_day': enrollment.current_day if enrollment else None,
            }
            program_list.append(program_data)

        return program_list

    @staticmethod
    def enroll_in_program(user, program_id):
        """
        Enroll user in a focus program
        Creates UserFocusProgram and ProgramProgressMongo entries
        """
        from focus.models import FocusProgram, UserFocusProgram
        from focus.mongo_models import ProgramProgressMongo
        from subscriptions.models import Subscription
        from django.utils import timezone

        # Get the program
        try:
            program = FocusProgram.objects.get(id=program_id, is_active=True)
        except FocusProgram.DoesNotExist:
            raise ValueError("Program not found or inactive")

        # Check if program requires pro subscription
        if program.is_pro_only:
            try:
                subscription = Subscription.objects.get(user=user)
                if not subscription.is_pro():
                    raise PermissionError("This program requires an active Pro subscription")
            except Subscription.DoesNotExist:
                raise PermissionError("This program requires an active Pro subscription")

        # Check if user is already enrolled in an active program
        existing_enrollment = UserFocusProgram.objects.filter(
            user=user,
            program=program,
            status__in=['in_progress', 'not_started', 'paused']
        ).first()

        if existing_enrollment:
            return {
                'enrolled': False,
                'message': 'Already enrolled in this program',
                'enrollment_id': existing_enrollment.id
            }

        # Create enrollment
        user_program = UserFocusProgram.objects.create(
            user=user,
            program=program,
            status='not_started',
            current_day=1
        )

        # Create progress tracking in MongoDB
        progress = ProgramProgressMongo(
            user_id=user.id,
            user_program_id=user_program.id,
            program_id=program.id,
            total_days=program.duration_days,
            days_completed=0,
            completion_percentage=0.0,
            started_at=timezone.now()
        )
        progress.save()

        return {
            'enrolled': True,
            'enrollment_id': user_program.id,
            'program_name': program.name,
            'total_days': program.duration_days
        }

    @staticmethod
    def start_program(user, enrollment_id):
        """
        Start a program (change status from not_started to in_progress)
        """
        from focus.models import UserFocusProgram
        from django.utils import timezone

        try:
            user_program = UserFocusProgram.objects.get(
                id=enrollment_id,
                user=user
            )
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        if user_program.status not in ['not_started', 'paused']:
            raise ValueError("Program is already started or completed")

        user_program.status = 'in_progress'
        user_program.started_at = timezone.now()
        user_program.save()

        return {
            'started': True,
            'enrollment_id': user_program.id,
            'current_day': user_program.current_day
        }

    @staticmethod
    def get_program_details(user, enrollment_id):
        """
        Get detailed information about user's enrolled program
        Includes progress, current day info, and statistics
        """
        from focus.models import UserFocusProgram, ProgramDay
        from focus.mongo_models import ProgramProgressMongo, UserProgramDayMongo

        try:
            user_program = UserFocusProgram.objects.select_related('program').get(
                id=enrollment_id,
                user=user
            )
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        program = user_program.program

        # Get progress from MongoDB
        progress = ProgramProgressMongo.objects(
            user_program_id=user_program.id
        ).first()

        if not progress:
            # Create if doesn't exist
            from django.utils import timezone
            progress = ProgramProgressMongo(
                user_id=user.id,
                user_program_id=user_program.id,
                program_id=program.id,
                total_days=program.duration_days,
                started_at=timezone.now()
            )
            progress.save()

        # Get current day info
        current_program_day = ProgramDay.objects.filter(
            program=program,
            day_number=user_program.current_day
        ).first()

        current_day_progress = None
        if current_program_day:
            current_day_progress = UserProgramDayMongo.objects(
                user_id=user.id,
                user_program_id=user_program.id,
                program_day_id=current_program_day.id
            ).first()

        return {
            'enrollment_id': user_program.id,
            'program': {
                'id': program.id,
                'name': program.name,
                'description': program.description,
                'duration_days': program.duration_days,
                'objectives': program.objectives,
            },
            'status': user_program.status,
            'current_day': user_program.current_day,
            'started_at': user_program.started_at,
            'progress': {
                'days_completed': progress.days_completed,
                'completion_percentage': progress.completion_percentage,
                'total_focus_minutes': progress.total_focus_minutes,
                'total_sessions': progress.total_sessions,
                'current_streak': progress.current_streak,
                'longest_streak': progress.longest_streak,
                'achievements': progress.achievements,
            },
            'current_day_info': {
                'day_number': current_program_day.day_number if current_program_day else None,
                'title': current_program_day.title if current_program_day else None,
                'description': current_program_day.description if current_program_day else None,
                'focus_duration': current_program_day.focus_duration if current_program_day else 25,
                'tasks': current_program_day.tasks if current_program_day else [],
                'tips': current_program_day.tips if current_program_day else [],
                'reflection_prompts': current_program_day.reflection_prompts if current_program_day else [],
                'is_completed': current_day_progress.is_completed if current_day_progress else False,
                'tasks_progress': {
                    'completed': current_day_progress.tasks_completed_count if current_day_progress else 0,
                    'total': current_day_progress.tasks_total_count if current_day_progress else 0,
                } if current_day_progress else None,
            } if current_program_day else None,
        }

    @staticmethod
    def get_day_details(user, enrollment_id, day_number):
        """
        Get detailed information for a specific program day
        """
        from focus.models import UserFocusProgram, ProgramDay
        from focus.mongo_models import UserProgramDayMongo

        try:
            user_program = UserFocusProgram.objects.select_related('program').get(
                id=enrollment_id,
                user=user
            )
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        # Get program day template
        try:
            program_day = ProgramDay.objects.get(
                program=user_program.program,
                day_number=day_number
            )
        except ProgramDay.DoesNotExist:
            raise ValueError(f"Day {day_number} not found for this program")

        # Get or create user's progress for this day
        user_day = UserProgramDayMongo.objects(
            user_id=user.id,
            user_program_id=user_program.id,
            program_day_id=program_day.id
        ).first()

        if not user_day:
            from focus.mongo_models import DailyTaskEmbed
            from datetime import datetime

            # Create new day progress
            tasks = [
                DailyTaskEmbed(task_text=task, order=i)
                for i, task in enumerate(program_day.tasks)
            ]

            user_day = UserProgramDayMongo(
                user_id=user.id,
                user_program_id=user_program.id,
                program_id=user_program.program.id,
                program_day_id=program_day.id,
                day_number=day_number,
                tasks=tasks,
                tasks_total_count=len(tasks),
                target_focus_minutes=program_day.focus_duration,
                started_at=datetime.utcnow()
            )
            user_day.save()

        return {
            'day_number': program_day.day_number,
            'title': program_day.title,
            'description': program_day.description,
            'focus_duration': program_day.focus_duration,
            'tips': program_day.tips,
            'reflection_prompts': program_day.reflection_prompts,
            'user_progress': {
                'is_completed': user_day.is_completed,
                'started_at': user_day.started_at,
                'completed_at': user_day.completed_at,
                'tasks': [
                    {
                        'text': task.task_text,
                        'is_completed': task.is_completed,
                        'completed_at': task.completed_at,
                        'order': task.order
                    }
                    for task in user_day.tasks
                ],
                'tasks_completed': user_day.tasks_completed_count,
                'tasks_total': user_day.tasks_total_count,
                'focus_minutes': user_day.total_focus_minutes,
                'target_focus_minutes': user_day.target_focus_minutes,
                'reflections': [
                    {
                        'question': refl.question,
                        'answer': refl.answer,
                        'answered_at': refl.answered_at
                    }
                    for refl in user_day.reflections
                ],
                'difficulty_rating': user_day.difficulty_rating,
                'satisfaction_rating': user_day.satisfaction_rating,
                'notes': user_day.notes,
            }
        }

    @staticmethod
    def update_task_status(user, enrollment_id, day_number, task_index, is_completed):
        """
        Mark a task as completed or incomplete
        """
        from focus.models import UserFocusProgram, ProgramDay
        from focus.mongo_models import UserProgramDayMongo
        from datetime import datetime

        try:
            user_program = UserFocusProgram.objects.get(id=enrollment_id, user=user)
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        # Get program day
        program_day = ProgramDay.objects.filter(
            program=user_program.program,
            day_number=day_number
        ).first()

        if not program_day:
            raise ValueError(f"Day {day_number} not found")

        # Get user day progress
        user_day = UserProgramDayMongo.objects(
            user_id=user.id,
            user_program_id=user_program.id,
            program_day_id=program_day.id
        ).first()

        if not user_day:
            raise ValueError("Day progress not found. Start the day first.")

        # Update task status
        if 0 <= task_index < len(user_day.tasks):
            user_day.tasks[task_index].is_completed = is_completed
            if is_completed:
                user_day.tasks[task_index].completed_at = datetime.utcnow()
            else:
                user_day.tasks[task_index].completed_at = None

            user_day.tasks_completed_count = sum(1 for task in user_day.tasks if task.is_completed)
            user_day.updated_at = datetime.utcnow()
            user_day.save()

            # Check if day is now complete
            user_day.check_completion()

            return {
                'success': True,
                'tasks_completed': user_day.tasks_completed_count,
                'tasks_total': user_day.tasks_total_count
            }
        else:
            raise ValueError("Invalid task index")

    @staticmethod
    def start_focus_session(user, enrollment_id, day_number, duration_minutes, session_type='program'):
        """
        Start a new focus session for a program day
        """
        from focus.models import UserFocusProgram, ProgramDay
        from focus.mongo_models import FocusSessionMongo, UserProgramDayMongo
        from datetime import datetime

        try:
            user_program = UserFocusProgram.objects.get(id=enrollment_id, user=user)
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        # Get program day
        program_day = ProgramDay.objects.filter(
            program=user_program.program,
            day_number=day_number
        ).first()

        # Check if there's already an active session
        active_session = FocusSessionMongo.objects(
            user_id=user.id,
            status='active',
            is_active=True
        ).first()

        if active_session:
            raise ValueError("You already have an active focus session. Please complete or cancel it first.")

        # Create focus session
        session = FocusSessionMongo(
            user_id=user.id,
            session_type=session_type,
            status='active',
            planned_duration_seconds=duration_minutes * 60,
            program_id=user_program.program.id,
            program_day_id=program_day.id if program_day else None,
            user_program_id=user_program.id,
            started_at=datetime.utcnow(),
            last_tick_at=datetime.utcnow(),
            is_active=True
        )
        session.save()

        return {
            'session_id': str(session.id),
            'started_at': session.started_at,
            'planned_duration_seconds': session.planned_duration_seconds,
            'status': session.status
        }

    @staticmethod
    def complete_focus_session(user, session_id, productivity_rating=None, notes=''):
        """
        Complete a focus session and update progress
        """
        from focus.models import UserFocusProgram
        from focus.mongo_models import FocusSessionMongo, UserProgramDayMongo, ProgramProgressMongo
        from datetime import datetime

        try:
            session = FocusSessionMongo.objects.get(id=session_id, user_id=user.id)
        except FocusSessionMongo.DoesNotExist:
            raise ValueError("Session not found")

        if session.status != 'active':
            raise ValueError("Session is not active")

        # Complete session
        session.status = 'completed'
        session.ended_at = datetime.utcnow()
        session.actual_duration_seconds = int((session.ended_at - session.started_at).total_seconds())
        session.actual_duration_seconds -= session.total_pause_duration_seconds  # Subtract pause time
        session.is_active = False

        if productivity_rating:
            session.productivity_rating = productivity_rating
        if notes:
            session.notes = notes

        session.save()

        # Update user program day progress
        if session.user_program_id and session.program_day_id:
            user_day = UserProgramDayMongo.objects(
                user_id=user.id,
                user_program_id=session.user_program_id,
                program_day_id=session.program_day_id
            ).first()

            if user_day:
                focus_minutes = session.actual_duration_seconds // 60
                user_day.total_focus_minutes += focus_minutes
                user_day.focus_sessions.append(str(session.id))
                user_day.updated_at = datetime.utcnow()
                user_day.save()

                # Check if day is complete
                user_day.check_completion()

                # Update program progress
                progress = ProgramProgressMongo.objects(
                    user_program_id=session.user_program_id
                ).first()

                if progress:
                    progress.total_focus_minutes += focus_minutes
                    progress.total_sessions += 1
                    progress.update_progress()
                    progress.update_streak(True)

                    # Check if day just completed
                    if user_day.is_completed:
                        progress.days_completed += 1
                        progress.update_progress()

                        # Update UserFocusProgram
                        try:
                            user_program = UserFocusProgram.objects.get(id=session.user_program_id)
                            if user_day.day_number == user_program.current_day:
                                user_program.current_day += 1
                                user_program.save()

                                # Check if program is complete
                                if user_program.current_day > user_program.program.duration_days:
                                    user_program.status = 'completed'
                                    user_program.completed_at = datetime.utcnow()
                                    progress.completed_at = datetime.utcnow()
                                    progress.save()
                                    user_program.save()
                        except UserFocusProgram.DoesNotExist:
                            pass

        return {
            'completed': True,
            'session_id': str(session.id),
            'actual_duration_minutes': session.actual_duration_seconds // 60,
            'ended_at': session.ended_at
        }

    @staticmethod
    def add_reflection(user, enrollment_id, day_number, question, answer):
        """
        Add a reflection response for a program day
        """
        from focus.models import UserFocusProgram, ProgramDay
        from focus.mongo_models import UserProgramDayMongo

        try:
            user_program = UserFocusProgram.objects.get(id=enrollment_id, user=user)
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        # Get program day
        program_day = ProgramDay.objects.filter(
            program=user_program.program,
            day_number=day_number
        ).first()

        if not program_day:
            raise ValueError(f"Day {day_number} not found")

        # Get user day progress
        user_day = UserProgramDayMongo.objects(
            user_id=user.id,
            user_program_id=user_program.id,
            program_day_id=program_day.id
        ).first()

        if not user_day:
            raise ValueError("Day progress not found. Start the day first.")

        # Add reflection
        user_day.add_reflection_response(question, answer, prompt_id=program_day.id)

        # Check if all reflections are complete
        if len(user_day.reflections) >= len(program_day.reflection_prompts):
            user_day.reflections_completed = True
            user_day.save()

        # Check if day is now complete
        user_day.check_completion()

        return {
            'success': True,
            'reflections_count': len(user_day.reflections),
            'day_completed': user_day.is_completed
        }

    @staticmethod
    def get_weekly_review(user, enrollment_id, week_number):
        """
        Get weekly review summary for a program
        """
        from focus.models import UserFocusProgram
        from focus.mongo_models import ProgramProgressMongo, UserProgramDayMongo

        try:
            user_program = UserFocusProgram.objects.select_related('program').get(
                id=enrollment_id,
                user=user
            )
        except UserFocusProgram.DoesNotExist:
            raise ValueError("Enrollment not found")

        # Calculate day range for the week
        start_day = (week_number - 1) * 7 + 1
        end_day = min(week_number * 7, user_program.program.duration_days)

        # Get progress
        progress = ProgramProgressMongo.objects(
            user_program_id=user_program.id
        ).first()

        if not progress:
            raise ValueError("Progress not found")

        # Get all days for this week
        week_days = UserProgramDayMongo.objects(
            user_id=user.id,
            user_program_id=user_program.id,
            day_number__gte=start_day,
            day_number__lte=end_day
        )

        # Calculate week statistics
        days_completed = sum(1 for day in week_days if day.is_completed)
        total_focus_minutes = sum(day.total_focus_minutes for day in week_days)
        avg_difficulty = sum(day.difficulty_rating for day in week_days if day.difficulty_rating) / max(len([d for d in week_days if d.difficulty_rating]), 1)
        avg_satisfaction = sum(day.satisfaction_rating for day in week_days if day.satisfaction_rating) / max(len([d for d in week_days if d.satisfaction_rating]), 1)

        # Get weekly summary if exists
        weekly_summary = next(
            (ws for ws in progress.weekly_summaries if ws['week'] == week_number),
            None
        )

        return {
            'week_number': week_number,
            'start_day': start_day,
            'end_day': end_day,
            'days_completed': days_completed,
            'total_days': end_day - start_day + 1,
            'completion_rate': (days_completed / (end_day - start_day + 1)) * 100,
            'total_focus_minutes': total_focus_minutes,
            'average_difficulty': round(avg_difficulty, 1) if avg_difficulty else None,
            'average_satisfaction': round(avg_satisfaction, 1) if avg_satisfaction else None,
            'current_streak': progress.current_streak,
            'achievements_earned': [
                ach for ach in progress.achievements
                if ach.get('earned_at') and
                   start_day <= ((ach.get('earned_at') - progress.started_at).days + 1) <= end_day
            ],
            'summary': weekly_summary['summary'] if weekly_summary else '',
        }

    @staticmethod
    def get_program_history(user):
        """
        Get user's program history (all enrollments)
        """
        from focus.models import UserFocusProgram
        from focus.mongo_models import ProgramProgressMongo

        enrollments = UserFocusProgram.objects.filter(
            user=user
        ).select_related('program').order_by('-created_at')

        history = []
        for enrollment in enrollments:
            progress = ProgramProgressMongo.objects(
                user_program_id=enrollment.id
            ).first()

            history.append({
                'enrollment_id': enrollment.id,
                'program_name': enrollment.program.name,
                'program_type': enrollment.program.program_type,
                'status': enrollment.status,
                'started_at': enrollment.started_at,
                'completed_at': enrollment.completed_at,
                'current_day': enrollment.current_day,
                'total_days': enrollment.program.duration_days,
                'completion_percentage': progress.completion_percentage if progress else 0,
                'total_focus_minutes': progress.total_focus_minutes if progress else 0,
                'current_streak': progress.current_streak if progress else 0,
            })

        return history
