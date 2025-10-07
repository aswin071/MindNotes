from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta

from helpers.common import success_response, error_response
from authentication.models import UserStreak
from journals.models import JournalEntry
from focus.models import UserFocusProgram
from prompts.models import DailyPrompt
from utils.mongo import get_mongo_db


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Streaks (Postgres)
        today = timezone.now().date()
        last7 = today - timedelta(days=6)
        streak_count = UserStreak.objects.filter(user=user, has_entry=True, date__gte=last7, date__lte=today).count()

        # Quick journal hint: last entry
        last_entry = (
            JournalEntry.objects.filter(user=user)
            .order_by('-entry_date')
            .values('id', 'title', 'entry_date')
            .first()
        )

        # Focus program status (Postgres)
        user_program = (
            UserFocusProgram.objects.filter(user=user, status__in=['in_progress', 'paused'])
            .select_related('program')
            .order_by('-started_at')
            .values('program__name', 'status', 'current_day', 'completion_percentage')
            .first()
        )

        # Prompt of the day (Mongo: per-user assigned with shuffle)
        db = get_mongo_db()
        potd_coll = db['prompt_of_day']
        potd_doc = potd_coll.find_one({'user_id': user.id, 'date': str(today)})
        if not potd_doc:
            prompt = (
                DailyPrompt.objects.order_by('?').values('id', 'text').first()
            )
            if prompt:
                potd_doc = {'user_id': user.id, 'date': str(today), 'prompt_id': prompt['id'], 'text': prompt['text']}
                potd_coll.insert_one(potd_doc)
        prompt_of_the_day = {'text': potd_doc['text']} if potd_doc else None

        # Mood widget (Mongo placeholder for quick retrieval e.g., last 7 days)
        mood_coll = db['mood_logs']
        moods = list(
            mood_coll.find({'user_id': user.id}).sort('date', -1).limit(7)
        )
        mood_widget = [
            {'date': m.get('date'), 'mood': m.get('mood')} for m in moods
        ]

        data = {
            'streak': streak_count,
            'quick_journal_last': last_entry,
            'prompt_of_the_day': prompt_of_the_day,
            'focus_program': user_program,
            'mood_widget': mood_widget,
        }
        return success_response(data=data, success_message='Dashboard')



