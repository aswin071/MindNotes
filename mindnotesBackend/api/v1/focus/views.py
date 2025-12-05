from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.core.cache import cache

from core.services import FocusService
from core.permissions import IsPremiumUser, IsOwner
from .serializers import (
    FocusProgramSerializer,
    EnrollProgramSerializer,
    StartProgramSerializer,
    ProgramProgressSerializer,
    DayDetailsSerializer,
    TaskStatusSerializer,
    StartFocusSessionSerializer,
    CompleteFocusSessionSerializer,
    AddReflectionSerializer,
    WeeklyReviewSerializer,
    ProgramHistorySerializer,
    PauseSessionSerializer,
    ResumeSessionSerializer,
    AddDistractionSerializer,
    # Ritual serializers
    RitualDaySerializer,
    StartRitualSessionSerializer,
    StartRitualStepSerializer,
    CompleteRitualStepSerializer,
    SkipRitualStepSerializer,
    CompleteRitualSessionSerializer,
    RitualSessionResponseSerializer,
    RitualHistorySerializer,
)
from helpers.common import success_response, error_response


class FocusProgramListView(APIView):
    """
    GET /api/v1/focus/programs/
    
    Get all available focus programs with enrollment status
    Returns programs filtered by user's subscription level
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all available programs with user's enrollment status"""
        try:
            # Use cache for performance
            cache_key = f'focus_programs_{request.user.id}'
            cached_data = cache.get(cache_key)

            if cached_data:
                return success_response(cached_data, status=status.HTTP_200_OK)

            programs = FocusService.get_available_programs(request.user)
            
            # Cache for 10 minutes
            cache.set(cache_key, programs, 600)
            
            return success_response(programs, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch programs: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EnrollProgramView(APIView):
    """
    POST /api/v1/focus/programs/enroll/
    
    Enroll user in a focus program
    Body: {"program_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Enroll user in a program"""
        serializer = EnrollProgramSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.enroll_in_program(
                user=request.user,
                program_id=serializer.validated_data['program_id']
            )

            # Clear programs cache
            cache.delete(f'focus_programs_{request.user.id}')

            return success_response(result, status=status.HTTP_201_CREATED)

        except PermissionError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to enroll: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartProgramView(APIView):
    """
    POST /api/v1/focus/programs/start/
    
    Start an enrolled program
    Body: {"enrollment_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start a program"""
        serializer = StartProgramSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.start_program(
                user=request.user,
                enrollment_id=serializer.validated_data['enrollment_id']
            )

            # Clear programs cache
            cache.delete(f'focus_programs_{request.user.id}')

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to start program: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProgramDetailsView(APIView):
    """
    GET /api/v1/focus/programs/{enrollment_id}/
    
    Get detailed information about an enrolled program
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        """Get program details with progress"""
        try:
            details = FocusService.get_program_details(
                user=request.user,
                enrollment_id=enrollment_id
            )

            serializer = ProgramProgressSerializer(details)
            return success_response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch program details: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DayDetailsView(APIView):
    """
    GET /api/v1/focus/programs/{enrollment_id}/days/{day_number}/
    
    Get detailed information for a specific program day
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id, day_number):
        """Get day details with user progress"""
        try:
            details = FocusService.get_day_details(
                user=request.user,
                enrollment_id=enrollment_id,
                day_number=day_number
            )

            serializer = DayDetailsSerializer(details)
            return success_response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch day details: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UpdateTaskStatusView(APIView):
    """
    POST /api/v1/focus/tasks/update/
    
    Update task completion status
    Body: {
        "enrollment_id": 1,
        "day_number": 1,
        "task_index": 0,
        "is_completed": true
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Update task status"""
        serializer = TaskStatusSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.update_task_status(
                user=request.user,
                enrollment_id=serializer.validated_data['enrollment_id'],
                day_number=serializer.validated_data['day_number'],
                task_index=serializer.validated_data['task_index'],
                is_completed=serializer.validated_data['is_completed']
            )

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to update task: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartFocusSessionView(APIView):
    """
    POST /api/v1/focus/sessions/start/
    
    Start a new focus session
    Body: {
        "enrollment_id": 1,
        "day_number": 1,
        "duration_minutes": 25,
        "session_type": "program"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start a focus session"""
        serializer = StartFocusSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.start_focus_session(
                user=request.user,
                enrollment_id=serializer.validated_data['enrollment_id'],
                day_number=serializer.validated_data['day_number'],
                duration_minutes=serializer.validated_data['duration_minutes'],
                session_type=serializer.validated_data.get('session_type', 'program')
            )

            return success_response(result, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to start session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompleteFocusSessionView(APIView):
    """
    POST /api/v1/focus/sessions/complete/
    
    Complete a focus session
    Body: {
        "session_id": "session_id_here",
        "productivity_rating": 4,
        "notes": "Great session"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete a focus session"""
        serializer = CompleteFocusSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.complete_focus_session(
                user=request.user,
                session_id=serializer.validated_data['session_id'],
                productivity_rating=serializer.validated_data.get('productivity_rating'),
                notes=serializer.validated_data.get('notes', '')
            )

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to complete session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PauseSessionView(APIView):
    """
    POST /api/v1/focus/sessions/pause/
    
    Pause a focus session
    Body: {"session_id": "session_id_here"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Pause an active session"""
        serializer = PauseSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from focus.mongo_models import FocusSessionMongo

            session = FocusSessionMongo.objects.get(
                id=serializer.validated_data['session_id'],
                user_id=request.user.id
            )

            if session.status != 'active':
                return error_response(
                    {'error': 'Session is not active'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            session.add_pause()
            session.status = 'paused'
            session.save()

            return success_response(
                {'message': 'Session paused'},
                status=status.HTTP_200_OK
            )

        except FocusSessionMongo.DoesNotExist:
            return error_response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to pause session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ResumeSessionView(APIView):
    """
    POST /api/v1/focus/sessions/resume/
    
    Resume a paused session
    Body: {"session_id": "session_id_here"}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Resume a paused session"""
        serializer = ResumeSessionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from focus.mongo_models import FocusSessionMongo
            from datetime import datetime

            session = FocusSessionMongo.objects.get(
                id=serializer.validated_data['session_id'],
                user_id=request.user.id
            )

            if session.status != 'paused':
                return error_response(
                    {'error': 'Session is not paused'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            session.resume_pause()
            session.status = 'active'
            session.last_tick_at = datetime.utcnow()
            session.save()

            return success_response(
                {'message': 'Session resumed'},
                status=status.HTTP_200_OK
            )

        except FocusSessionMongo.DoesNotExist:
            return error_response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to resume session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddDistractionView(APIView):
    """
    POST /api/v1/focus/sessions/distraction/
    
    Log a distraction during session
    Body: {
        "session_id": "session_id_here",
        "distraction_note": "Phone notification"
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add distraction to session"""
        serializer = AddDistractionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from focus.mongo_models import FocusSessionMongo

            session = FocusSessionMongo.objects.get(
                id=serializer.validated_data['session_id'],
                user_id=request.user.id
            )

            session.add_distraction(serializer.validated_data['distraction_note'])

            return success_response(
                {
                    'distraction_count': session.distraction_count
                },
                status=status.HTTP_200_OK
            )

        except FocusSessionMongo.DoesNotExist:
            return error_response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to add distraction: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AddReflectionView(APIView):
    """
    POST /api/v1/focus/reflections/add/
    
    Add a reflection response for a program day
    Body: {
        "enrollment_id": 1,
        "day_number": 1,
        "question": "What did you learn today?",
        "answer": "I learned that..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add reflection response"""
        serializer = AddReflectionSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.add_reflection(
                user=request.user,
                enrollment_id=serializer.validated_data['enrollment_id'],
                day_number=serializer.validated_data['day_number'],
                question=serializer.validated_data['question'],
                answer=serializer.validated_data['answer']
            )

            return success_response(result, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to add reflection: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WeeklyReviewView(APIView):
    """
    GET /api/v1/focus/programs/{enrollment_id}/weekly-review/{week_number}/
    
    Get weekly review summary
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id, week_number):
        """Get weekly review"""
        try:
            review = FocusService.get_weekly_review(
                user=request.user,
                enrollment_id=enrollment_id,
                week_number=week_number
            )

            serializer = WeeklyReviewSerializer(review)
            return success_response(serializer.data, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch weekly review: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ProgramHistoryView(APIView):
    """
    GET /api/v1/focus/history/
    
    Get user's program history
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's program history"""
        try:
            history = FocusService.get_program_history(request.user)
            
            serializer = ProgramHistorySerializer(history, many=True)
            return success_response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActiveSessionView(APIView):
    """
    GET /api/v1/focus/sessions/active/
    
    Get user's active focus session if any
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get active session"""
        try:
            from focus.mongo_models import FocusSessionMongo

            active_session = FocusSessionMongo.objects(
                user_id=request.user.id,
                status='active',
                is_active=True
            ).first()

            if not active_session:
                return error_response(
                    {'active_session': None},
                    status=status.HTTP_200_OK
                )

            return success_response(
                {
                    'active_session': {
                        'session_id': str(active_session.id),
                        'started_at': active_session.started_at,
                        'planned_duration_seconds': active_session.planned_duration_seconds,
                        'status': active_session.status,
                        'session_type': active_session.session_type,
                        'program_id': active_session.program_id,
                        'distraction_count': active_session.distraction_count,
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch active session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# RITUAL / MORNING CHARGE VIEWS
# ============================================

class RitualDayDetailsView(APIView):
    """
    GET /api/v1/focus/rituals/{enrollment_id}/days/{day_number}/

    Get ritual day details with steps for step-by-step programs like Morning Charge
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id, day_number):
        """Get ritual day details with all steps"""
        try:
            details = FocusService.get_ritual_day_details(
                user=request.user,
                enrollment_id=enrollment_id,
                day_number=day_number
            )

            return success_response(details, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch ritual day details: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartRitualSessionView(APIView):
    """
    POST /api/v1/focus/rituals/sessions/start/

    Start a new ritual session (Morning Charge, etc.)
    Body: {
        "enrollment_id": 1,
        "day_number": 1,
        "mood_before": 3  // optional
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start a ritual session"""
        serializer = StartRitualSessionSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.start_ritual_session(
                user=request.user,
                enrollment_id=serializer.validated_data['enrollment_id'],
                day_number=serializer.validated_data['day_number'],
                mood_before=serializer.validated_data.get('mood_before')
            )

            return success_response(result, status=status.HTTP_201_CREATED)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to start ritual session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartRitualStepView(APIView):
    """
    POST /api/v1/focus/rituals/steps/start/

    Start a specific step in a ritual session
    Body: {
        "session_id": "abc123",
        "step_id": 1
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start a ritual step"""
        serializer = StartRitualStepSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.start_ritual_step(
                user=request.user,
                session_id=serializer.validated_data['session_id'],
                step_id=serializer.validated_data['step_id']
            )

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to start ritual step: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompleteRitualStepView(APIView):
    """
    POST /api/v1/focus/rituals/steps/complete/

    Complete a ritual step with response
    Body: {
        "session_id": "abc123",
        "step_order": 1,
        "text_response": "I am grateful for...",  // for gratitude/prompt steps
        "selected_choice": "I am focused...",      // for affirmation steps
        "breathing_cycles_completed": 3            // for breathing steps
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete a ritual step"""
        serializer = CompleteRitualStepSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Build response data from validated data
            response_data = {}
            for field in ['text_response', 'voice_note_url', 'selected_choice',
                         'selected_choices', 'rating_value', 'breathing_cycles_completed']:
                if field in serializer.validated_data:
                    response_data[field] = serializer.validated_data[field]

            result = FocusService.complete_ritual_step(
                user=request.user,
                session_id=serializer.validated_data['session_id'],
                step_order=serializer.validated_data['step_order'],
                response_data=response_data
            )

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to complete ritual step: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SkipRitualStepView(APIView):
    """
    POST /api/v1/focus/rituals/steps/skip/

    Skip a ritual step
    Body: {
        "session_id": "abc123",
        "step_order": 1,
        "reason": "Not in the mood"  // optional
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Skip a ritual step"""
        serializer = SkipRitualStepSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.skip_ritual_step(
                user=request.user,
                session_id=serializer.validated_data['session_id'],
                step_order=serializer.validated_data['step_order'],
                reason=serializer.validated_data.get('reason', '')
            )

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to skip ritual step: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompleteRitualSessionView(APIView):
    """
    POST /api/v1/focus/rituals/sessions/complete/

    Complete a ritual session
    Body: {
        "session_id": "abc123",
        "mood_after": 4,      // optional
        "energy_level": 5,    // optional
        "notes": "Great morning!"  // optional
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete a ritual session"""
        serializer = CompleteRitualSessionSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            result = FocusService.complete_ritual_session(
                user=request.user,
                session_id=serializer.validated_data['session_id'],
                mood_after=serializer.validated_data.get('mood_after'),
                energy_level=serializer.validated_data.get('energy_level'),
                notes=serializer.validated_data.get('notes', '')
            )

            return success_response(result, status=status.HTTP_200_OK)

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to complete ritual session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ActiveRitualSessionView(APIView):
    """
    GET /api/v1/focus/rituals/sessions/active/

    Get user's active ritual session if any
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get active ritual session"""
        try:
            from focus.mongo_models import RitualSessionMongo

            active_session = RitualSessionMongo.objects(
                user_id=request.user.id,
                status='in_progress'
            ).first()

            if not active_session:
                return success_response(
                    {'active_session': None},
                    status=status.HTTP_200_OK
                )

            return success_response(
                {
                    'active_session': {
                        'session_id': str(active_session.id),
                        'program_id': active_session.program_id,
                        'day_number': active_session.day_number,
                        'started_at': active_session.started_at,
                        'current_step_order': active_session.current_step_order,
                        'total_steps': active_session.total_steps,
                        'steps_completed': active_session.steps_completed,
                        'completion_percentage': active_session.completion_percentage,
                        'status': active_session.status,
                    }
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch active ritual session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RitualSessionDetailView(APIView):
    """
    GET /api/v1/focus/rituals/sessions/{session_id}/

    Get details of a specific ritual session including all step responses
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, session_id):
        """Get ritual session details"""
        try:
            from focus.mongo_models import RitualSessionMongo

            session = RitualSessionMongo.objects.get(
                id=session_id,
                user_id=request.user.id
            )

            step_responses = []
            for step_resp in session.step_responses:
                step_responses.append({
                    'step_id': step_resp.step_id,
                    'step_order': step_resp.step_order,
                    'step_type': step_resp.step_type,
                    'is_completed': step_resp.is_completed,
                    'started_at': step_resp.started_at,
                    'completed_at': step_resp.completed_at,
                    'duration_seconds': step_resp.duration_seconds,
                    'text_response': step_resp.text_response,
                    'voice_note_url': step_resp.voice_note_url,
                    'selected_choice': step_resp.selected_choice,
                    'selected_choices': step_resp.selected_choices,
                    'rating_value': step_resp.rating_value,
                    'breathing_cycles_completed': step_resp.breathing_cycles_completed,
                    'skipped': step_resp.skipped,
                    'skip_reason': step_resp.skip_reason,
                })

            return success_response({
                'session_id': str(session.id),
                'program_id': session.program_id,
                'day_number': session.day_number,
                'status': session.status,
                'started_at': session.started_at,
                'completed_at': session.completed_at,
                'total_duration_seconds': session.total_duration_seconds,
                'current_step_order': session.current_step_order,
                'total_steps': session.total_steps,
                'steps_completed': session.steps_completed,
                'completion_percentage': session.completion_percentage,
                'mood_before': session.mood_before,
                'mood_after': session.mood_after,
                'energy_level': session.energy_level,
                'step_responses': step_responses,
            }, status=status.HTTP_200_OK)

        except RitualSessionMongo.DoesNotExist:
            return error_response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch ritual session: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RitualHistoryView(APIView):
    """
    GET /api/v1/focus/rituals/{enrollment_id}/history/

    Get ritual session history for a program enrollment
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, enrollment_id):
        """Get ritual session history"""
        try:
            from focus.models import UserFocusProgram
            from focus.mongo_models import RitualSessionMongo

            # Verify enrollment
            user_program = UserFocusProgram.objects.get(
                id=enrollment_id,
                user=request.user
            )

            sessions = RitualSessionMongo.objects(
                user_id=request.user.id,
                user_program_id=enrollment_id
            ).order_by('-created_at')

            history = []
            for session in sessions:
                history.append({
                    'session_id': str(session.id),
                    'day_number': session.day_number,
                    'status': session.status,
                    'started_at': session.started_at,
                    'completed_at': session.completed_at,
                    'total_duration_seconds': session.total_duration_seconds,
                    'steps_completed': session.steps_completed,
                    'total_steps': session.total_steps,
                    'mood_before': session.mood_before,
                    'mood_after': session.mood_after,
                    'energy_level': session.energy_level,
                })

            return success_response(history, status=status.HTTP_200_OK)

        except UserFocusProgram.DoesNotExist:
            return error_response(
                {'error': 'Enrollment not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': f'Failed to fetch ritual history: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
