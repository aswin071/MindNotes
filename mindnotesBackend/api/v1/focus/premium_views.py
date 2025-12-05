"""
API Views for Premium Focus Programs
- 5-Minute Morning Charge
- Brain Dump Reset
- Gratitude Pause
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from focus.premium_services import (
    PremiumAccessService,
    MorningChargeService,
    BrainDumpService,
    GratitudePauseService,
    PremiumProgramAnalyticsService
)
from .premium_serializers import *
from helpers.common import success_response, error_response


# ============================================
# COMMON VIEWS
# ============================================

class PremiumAccessCheckView(APIView):
    """
    GET /api/v1/focus/premium/access/

    Check user's access to premium programs (paid or trial)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Check premium access"""
        try:
            has_access, access_type, trial_info = PremiumAccessService.check_premium_access(request.user)

            data = {
                'has_access': has_access,
                'access_type': access_type,
                'trial_info': trial_info
            }

            serializer = PremiumAccessSerializer(data)
            return success_response(
                serializer.data,
                success_message="Premium access status retrieved",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to check premium access",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpCategoriesView(APIView):
    """
    GET /api/v1/focus/premium/brain-dump/categories/

    Get all brain dump categories for thought categorization
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all categories"""
        try:
            # Cache categories for 1 hour
            cache_key = 'brain_dump_categories'
            cached_data = cache.get(cache_key)

            if cached_data:
                return success_response(
                    cached_data,
                    success_message="Categories retrieved from cache",
                    status=status.HTTP_200_OK
                )

            categories = BrainDumpService.get_categories()
            serializer = BrainDumpCategorySerializer(categories, many=True)

            cache.set(cache_key, serializer.data, 3600)

            return success_response(
                serializer.data,
                success_message="Categories retrieved successfully",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch categories",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PremiumProgramStatsView(APIView):
    """
    GET /api/v1/focus/premium/stats/

    Get user's comprehensive stats across all premium programs
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user statistics"""
        try:
            stats = PremiumProgramAnalyticsService.get_user_stats(request.user.id)
            serializer = PremiumProgramStatsSerializer(stats)

            return success_response(
                serializer.data,
                success_message="Statistics retrieved successfully",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch statistics",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# MORNING CHARGE VIEWS
# ============================================

class MorningChargeStartView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/start/

    Start a new Morning Charge session or get today's session
    Body: {"session_date": "2025-12-02"} (optional)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start or resume session"""
        try:
            # Check premium access
            has_access, access_type, trial_info = PremiumAccessService.check_premium_access(request.user)
            if not has_access:
                return error_response(
                    {'error': 'Premium access required'},
                    error_message="Your trial has expired. Please subscribe to continue using Morning Charge.",
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = MorningChargeStartSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.start_session(
                user_id=request.user.id,
                session_date=serializer.validated_data.get('session_date')
            )

            # Increment usage count if trial
            if access_type == 'trial':
                PremiumAccessService.increment_program_usage(request.user, 'morning_charge')

            response_serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Morning Charge session started",
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to start session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeBreathingView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/breathing/

    Complete the breathing step
    Body: {"session_id": "...", "duration_seconds": 60}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete breathing"""
        try:
            serializer = MorningChargeBreathingSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.complete_breathing(
                session_id=serializer.validated_data['session_id'],
                duration_seconds=serializer.validated_data['duration_seconds']
            )

            response_serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Breathing completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete breathing",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeGratitudeView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/gratitude/

    Save gratitude spark (text or voice note)
    Body: {"session_id": "...", "gratitude_text": "..." OR "voice_note_url": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save gratitude"""
        try:
            serializer = MorningChargeGratitudeSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.save_gratitude(
                session_id=serializer.validated_data['session_id'],
                gratitude_text=serializer.validated_data.get('gratitude_text'),
                voice_note_url=serializer.validated_data.get('voice_note_url')
            )

            response_serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Gratitude saved",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save gratitude",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeAffirmationView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/affirmation/

    Save positive affirmation
    Body: {"session_id": "...", "affirmation_text": "...", "is_favorite": false}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save affirmation"""
        try:
            serializer = MorningChargeAffirmationSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.save_affirmation(
                session_id=serializer.validated_data['session_id'],
                affirmation_text=serializer.validated_data['affirmation_text'],
                is_favorite=serializer.validated_data.get('is_favorite', False)
            )

            response_serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Affirmation saved",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save affirmation",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeClarityView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/clarity/

    Save daily clarity prompt response
    Body: {"session_id": "...", "question": "...", "answer": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save clarity prompt"""
        try:
            serializer = MorningChargeClaritySerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.save_clarity_prompt(
                session_id=serializer.validated_data['session_id'],
                question=serializer.validated_data['question'],
                answer=serializer.validated_data['answer']
            )

            response_serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Clarity prompt saved",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save clarity prompt",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeCloseView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/close/

    Complete the charge close step
    Body: {"session_id": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete charge close"""
        try:
            serializer = MorningChargeCloseSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.complete_charge_close(
                session_id=serializer.validated_data['session_id']
            )

            response_serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Charge close completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete charge close",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeCompleteView(APIView):
    """
    POST /api/v1/focus/premium/morning-charge/complete/

    Complete the entire Morning Charge session
    Body: {"session_id": "...", "total_duration_seconds": 300}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete session"""
        try:
            serializer = MorningChargeCompleteSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = MorningChargeService.complete_session(
                session_id=serializer.validated_data['session_id'],
                total_duration_seconds=serializer.validated_data['total_duration_seconds']
            )

            response_serializer = MorningChargeSessionResponseSerializer(session)

            return success_response(
                response_serializer.data,
                success_message=f"Morning Charge completed! {session.current_streak}-day streak!",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeHistoryView(APIView):
    """
    GET /api/v1/focus/premium/morning-charge/history/

    Get user's Morning Charge session history
    Query params: ?limit=30
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get session history"""
        try:
            limit = int(request.query_params.get('limit', 30))
            sessions = MorningChargeService.get_session_history(request.user.id, limit=limit)

            serializer = MorningChargeSessionResponseSerializer(sessions, many=True)
            return success_response(
                serializer.data,
                success_message="History retrieved successfully",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch history",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MorningChargeTodayView(APIView):
    """
    GET /api/v1/focus/premium/morning-charge/today/

    Get today's Morning Charge session if it exists
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get today's session"""
        try:
            session = MorningChargeService.get_today_session(request.user.id)

            if not session:
                return success_response(
                    None,
                    success_message="No session found for today",
                    status=status.HTTP_200_OK
                )

            serializer = MorningChargeSessionResponseSerializer(session)
            return success_response(
                serializer.data,
                success_message="Today's session retrieved",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch today's session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# BRAIN DUMP VIEWS
# ============================================

class BrainDumpStartView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/start/

    Start a new Brain Dump session
    Body: {"session_date": "2025-12-02"} (optional)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start or resume session"""
        try:
            # Check premium access
            has_access, access_type, trial_info = PremiumAccessService.check_premium_access(request.user)
            if not has_access:
                return error_response(
                    {'error': 'Premium access required'},
                    error_message="Your trial has expired. Please subscribe to continue using Brain Dump Reset.",
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = BrainDumpStartSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.start_session(
                user_id=request.user.id,
                session_date=serializer.validated_data.get('session_date')
            )

            # Increment usage count if trial
            if access_type == 'trial':
                PremiumAccessService.increment_program_usage(request.user, 'brain_dump')

            response_serializer = BrainDumpSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Brain Dump session started",
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to start session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpSettleInView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/settle-in/

    Complete the settle in step
    Body: {"session_id": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete settle in"""
        try:
            serializer = BrainDumpSettleInSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.complete_settle_in(
                session_id=serializer.validated_data['session_id']
            )

            response_serializer = BrainDumpSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Settle in completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete settle in",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpAddThoughtsView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/thoughts/

    Add thoughts to the dump
    Body: {"session_id": "...", "thoughts": [{"text": "...", "category_id": null}]}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Add thoughts"""
        try:
            serializer = BrainDumpAddThoughtsSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.add_thoughts(
                session_id=serializer.validated_data['session_id'],
                thoughts_list=serializer.validated_data['thoughts']
            )

            response_serializer = BrainDumpSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Thoughts added",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to add thoughts",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpGuidedResponsesView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/guided-responses/

    Save guided question responses
    Body: {"session_id": "...", "response_1": "...", "response_2": "...", "response_3": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save guided responses"""
        try:
            serializer = BrainDumpGuidedResponsesSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.save_guided_responses(
                session_id=serializer.validated_data['session_id'],
                response_1=serializer.validated_data.get('response_1'),
                response_2=serializer.validated_data.get('response_2'),
                response_3=serializer.validated_data.get('response_3')
            )

            response_serializer = BrainDumpSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Guided responses saved",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save responses",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpCategorizeView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/categorize/

    Categorize thoughts
    Body: {"session_id": "...", "categorized_thoughts": [{"index": 0, "category_id": 1, "category_name": "..."}]}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Categorize thoughts"""
        try:
            serializer = BrainDumpCategorizeSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.categorize_thoughts(
                session_id=serializer.validated_data['session_id'],
                categorized_thoughts=serializer.validated_data['categorized_thoughts']
            )

            response_serializer = BrainDumpSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Thoughts categorized",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to categorize thoughts",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpChooseTaskView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/choose-task/

    Choose one task to focus on
    Body: {"session_id": "...", "task_text": "...", "task_category_id": 1}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Choose focus task"""
        try:
            serializer = BrainDumpChooseTaskSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.choose_focus_task(
                session_id=serializer.validated_data['session_id'],
                task_text=serializer.validated_data['task_text'],
                task_category_id=serializer.validated_data['task_category_id']
            )

            response_serializer = BrainDumpSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Focus task chosen",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to choose task",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpCloseBreatheView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/close-breathe/

    Complete the close and breathe step
    Body: {"session_id": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete close and breathe"""
        try:
            serializer = BrainDumpCloseBreatheSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.complete_close_breathe(
                session_id=serializer.validated_data['session_id']
            )

            response_serializer = BrainDumpSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Close and breathe completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete close and breathe",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpCompleteView(APIView):
    """
    POST /api/v1/focus/premium/brain-dump/complete/

    Complete the entire Brain Dump session
    Body: {"session_id": "...", "total_duration_seconds": 300}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete session"""
        try:
            serializer = BrainDumpCompleteSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = BrainDumpService.complete_session(
                session_id=serializer.validated_data['session_id'],
                total_duration_seconds=serializer.validated_data['total_duration_seconds']
            )

            response_serializer = BrainDumpSessionDetailSerializer(session)

            return success_response(
                response_serializer.data,
                success_message=f"Brain Dump completed! You cleared {session.total_thoughts_count} thoughts. {session.current_streak}-day streak!",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpHistoryView(APIView):
    """
    GET /api/v1/focus/premium/brain-dump/history/

    Get user's Brain Dump session history
    Query params: ?limit=30
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get session history"""
        try:
            limit = int(request.query_params.get('limit', 30))
            sessions = BrainDumpService.get_session_history(request.user.id, limit=limit)

            serializer = BrainDumpSessionDetailSerializer(sessions, many=True)
            return success_response(
                serializer.data,
                success_message="History retrieved successfully",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch history",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BrainDumpTodayView(APIView):
    """
    GET /api/v1/focus/premium/brain-dump/today/

    Get today's Brain Dump session if it exists
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get today's session"""
        try:
            session = BrainDumpService.get_today_session(request.user.id)

            if not session:
                return success_response(
                    None,
                    success_message="No session found for today",
                    status=status.HTTP_200_OK
                )

            serializer = BrainDumpSessionDetailSerializer(session)
            return success_response(
                serializer.data,
                success_message="Today's session retrieved",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch today's session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# ============================================
# GRATITUDE PAUSE VIEWS
# ============================================

class GratitudePauseStartView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/start/

    Start a new Gratitude Pause session
    Body: {"session_date": "2025-12-02"} (optional)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Start or resume session"""
        try:
            # Check premium access
            has_access, access_type, trial_info = PremiumAccessService.check_premium_access(request.user)
            if not has_access:
                return error_response(
                    {'error': 'Premium access required'},
                    error_message="Your trial has expired. Please subscribe to continue using Gratitude Pause.",
                    status=status.HTTP_403_FORBIDDEN
                )

            serializer = GratitudePauseStartSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = GratitudePauseService.start_session(
                user_id=request.user.id,
                session_date=serializer.validated_data.get('session_date')
            )

            # Increment usage count if trial
            if access_type == 'trial':
                PremiumAccessService.increment_program_usage(request.user, 'gratitude_pause')

            response_serializer = GratitudePauseSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Gratitude Pause session started",
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to start session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseArriveView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/arrive/

    Complete the arrive step
    Body: {"session_id": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete arrive"""
        try:
            serializer = GratitudePauseArriveSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = GratitudePauseService.complete_arrive(
                session_id=serializer.validated_data['session_id']
            )

            response_serializer = GratitudePauseSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Arrive completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete arrive",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseThreeGratitudesView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/three-gratitudes/

    Save three gratitudes
    Body: {"session_id": "...", "gratitude_1": "...", "gratitude_2": "...", "gratitude_3": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save three gratitudes"""
        try:
            serializer = GratitudePauseThreeGratitudesSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = GratitudePauseService.save_three_gratitudes(
                session_id=serializer.validated_data['session_id'],
                gratitude_1=serializer.validated_data['gratitude_1'],
                gratitude_2=serializer.validated_data['gratitude_2'],
                gratitude_3=serializer.validated_data['gratitude_3']
            )

            response_serializer = GratitudePauseSessionResponseSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Three gratitudes saved",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save gratitudes",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseDeepDiveView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/deep-dive/

    Save deep dive responses
    Body: {
        "session_id": "...",
        "selected_index": 1,
        "precise": "...",
        "why_matters": "...",
        "who_made_possible": "...",
        "sensory_moment": "...",
        "gratitude_line": "..."
    }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save deep dive"""
        try:
            serializer = GratitudePauseDeepDiveSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            deep_dive_responses = {
                'precise': serializer.validated_data['precise'],
                'why_matters': serializer.validated_data['why_matters'],
                'who_made_possible': serializer.validated_data['who_made_possible'],
                'sensory_moment': serializer.validated_data['sensory_moment'],
                'gratitude_line': serializer.validated_data['gratitude_line']
            }

            session = GratitudePauseService.save_deep_dive(
                session_id=serializer.validated_data['session_id'],
                selected_index=serializer.validated_data['selected_index'],
                deep_dive_responses=deep_dive_responses
            )

            response_serializer = GratitudePauseSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Deep dive completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save deep dive",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseExpressionView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/expression/

    Save expression action
    Body: {"session_id": "...", "action": "send_thank_you", "notes": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Save expression action"""
        try:
            serializer = GratitudePauseExpressionSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = GratitudePauseService.save_expression(
                session_id=serializer.validated_data['session_id'],
                action=serializer.validated_data['action'],
                notes=serializer.validated_data.get('notes')
            )

            response_serializer = GratitudePauseSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Expression action saved",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to save expression",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseAnchorView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/anchor/

    Complete the anchor step
    Body: {"session_id": "..."}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete anchor"""
        try:
            serializer = GratitudePauseAnchorSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = GratitudePauseService.complete_anchor(
                session_id=serializer.validated_data['session_id']
            )

            response_serializer = GratitudePauseSessionDetailSerializer(session)
            return success_response(
                response_serializer.data,
                success_message="Anchor completed",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete anchor",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseCompleteView(APIView):
    """
    POST /api/v1/focus/premium/gratitude-pause/complete/

    Complete the entire Gratitude Pause session
    Body: {"session_id": "...", "total_duration_seconds": 300}
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Complete session"""
        try:
            serializer = GratitudePauseCompleteSerializer(data=request.data)
            if not serializer.is_valid():
                return error_response(
                    serializer.errors,
                    error_message="Invalid input",
                    status=status.HTTP_400_BAD_REQUEST
                )

            session = GratitudePauseService.complete_session(
                session_id=serializer.validated_data['session_id'],
                total_duration_seconds=serializer.validated_data['total_duration_seconds']
            )

            response_serializer = GratitudePauseSessionDetailSerializer(session)

            return success_response(
                response_serializer.data,
                success_message=f"Gratitude Pause completed! {session.current_streak}-day streak!",
                status=status.HTTP_200_OK
            )

        except ValueError as e:
            return error_response(
                {'error': str(e)},
                error_message="Session not found",
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to complete session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseHistoryView(APIView):
    """
    GET /api/v1/focus/premium/gratitude-pause/history/

    Get user's Gratitude Pause session history
    Query params: ?limit=30
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get session history"""
        try:
            limit = int(request.query_params.get('limit', 30))
            sessions = GratitudePauseService.get_session_history(request.user.id, limit=limit)

            serializer = GratitudePauseSessionDetailSerializer(sessions, many=True)
            return success_response(
                serializer.data,
                success_message="History retrieved successfully",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch history",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GratitudePauseTodayView(APIView):
    """
    GET /api/v1/focus/premium/gratitude-pause/today/

    Get today's Gratitude Pause session if it exists
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get today's session"""
        try:
            session = GratitudePauseService.get_today_session(request.user.id)

            if not session:
                return success_response(
                    None,
                    success_message="No session found for today",
                    status=status.HTTP_200_OK
                )

            serializer = GratitudePauseSessionDetailSerializer(session)
            return success_response(
                serializer.data,
                success_message="Today's session retrieved",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                {'error': str(e)},
                error_message="Failed to fetch today's session",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
