from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.cache import cache

from core.prompt_service import PromptService
from helpers.common import success_response, error_response
from .serializers import PromptResponseSerializer


class TodayPromptsView(APIView):
    """
    GET /api/v1/prompts/today

    Get today's 5 reflection questions for the user

    Returns:
    - 5 prompts with questions, categories, and tags
    - Completion status (which ones are answered)
    - Streak information
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get today's prompts"""
        user = request.user

        try:
            # Get or generate today's prompts
            prompt_set = PromptService.get_today_prompts(user)

            # Get streak info
            streak_info = PromptService.get_user_streak(user)

            # Prepare response
            prompts_data = []
            for idx, prompt in enumerate(prompt_set.prompts, 1):
                is_completed = prompt['id'] in prompt_set.completed_prompt_ids

                prompts_data.append({
                    'number': idx,
                    'prompt_id': prompt['id'],
                    'question': prompt['question'],
                    'description': prompt['description'],
                    'category': prompt['category'],
                    'category_icon': prompt['category_icon'],
                    'category_color': prompt['category_color'],
                    'tags': prompt['tags'],
                    'difficulty': prompt['difficulty'],
                    'is_completed': is_completed,
                })

            response_data = {
                'date': prompt_set.date.isoformat(),
                'prompts': prompts_data,
                'completion': {
                    'completed_count': prompt_set.completed_count,
                    'total_count': len(prompt_set.prompts),
                    'is_fully_completed': prompt_set.is_fully_completed,
                    'progress_percentage': (prompt_set.completed_count / len(prompt_set.prompts) * 100) if prompt_set.prompts else 0,
                },
                'streak': streak_info,
            }

            return success_response(
                data=response_data,
                success_message='Today prompts retrieved successfully',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                error_message='Failed to retrieve prompts',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptResponseView(APIView):
    """
    POST /api/v1/prompts/respond

    Submit a response to a prompt question

    Request body:
    - prompt_id: ID of the prompt being answered
    - response: User's written response
    - time_spent: Time spent writing (optional, seconds)
    - mood: User's mood rating (optional, 1-5)
    - save_as_journal: Whether to save as journal entry (default: true)
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Submit prompt response"""
        user = request.user

        serializer = PromptResponseSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                errors=serializer.errors,
                error_message='Invalid response data',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validated_data = serializer.validated_data

            # Submit response
            result = PromptService.submit_prompt_response(
                user=user,
                prompt_id=validated_data['prompt_id'],
                response_text=validated_data['response'],
                time_spent=validated_data.get('time_spent', 0),
                mood=validated_data.get('mood')
            )

            # Optionally save as journal entry (default behavior)
            if validated_data.get('save_as_journal', True):
                from core.services import JournalService
                from prompts.models import DailyPrompt

                prompt = DailyPrompt.objects.get(id=validated_data['prompt_id'])

                journal_data = {
                    'content': validated_data['response'],
                    'title': f"Prompt: {prompt.question[:50]}...",
                    'entry_type': 'text',
                    'tag_ids': [],  # Tags from prompt
                    'privacy': 'private',
                }

                # Add matching tags
                from journals.models import Tag
                if prompt.tags:
                    matching_tags = Tag.objects.filter(
                        user=user,
                        name__in=prompt.tags
                    ).values_list('id', flat=True)
                    journal_data['tag_ids'] = list(matching_tags)

                journal_entry = JournalService.create_journal_entry(user, journal_data)
                result['journal_entry_id'] = str(journal_entry.id)

            # Clear cache
            cache.delete(f'daily_prompts_{user.id}_{validated_data.get("date")}')
            cache.delete(f'dashboard_{user.id}')

            return success_response(
                data=result,
                success_message='Response submitted successfully',
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return error_response(
                error_message=str(e),
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return error_response(
                error_message='Failed to submit response',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptStreakView(APIView):
    """
    GET /api/v1/prompts/streak

    Get user's prompt completion streak and statistics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get streak information"""
        user = request.user

        try:
            streak_info = PromptService.get_user_streak(user)
            stats = PromptService.get_completion_stats(user)

            response_data = {
                **streak_info,
                **stats,
            }

            return success_response(
                data=response_data,
                success_message='Streak information retrieved successfully',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                error_message='Failed to retrieve streak',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PromptHistoryView(APIView):
    """
    GET /api/v1/prompts/history

    Get user's prompt response history

    Query params:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20)
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get response history"""
        user = request.user

        try:
            from prompts.mongo_models import PromptResponseMongo
            from prompts.models import DailyPrompt

            page = int(request.query_params.get('page', 1))
            limit = min(int(request.query_params.get('limit', 20)), 100)
            skip = (page - 1) * limit

            # Get responses
            responses = PromptResponseMongo.objects(
                user_id=user.id
            ).order_by('-responded_at').skip(skip).limit(limit)

            total_count = PromptResponseMongo.objects(user_id=user.id).count()

            # Get prompt details
            prompt_ids = [r.prompt_id for r in responses]
            prompts_dict = {}
            if prompt_ids:
                prompts = DailyPrompt.objects.filter(id__in=prompt_ids).select_related('category')
                prompts_dict = {p.id: p for p in prompts}

            # Prepare response data
            history_data = []
            for response in responses:
                prompt = prompts_dict.get(response.prompt_id)

                history_data.append({
                    'response_id': str(response.id),
                    'prompt_id': response.prompt_id,
                    'question': prompt.question if prompt else 'Unknown',
                    'category': prompt.category.name if prompt and prompt.category else 'General',
                    'response': response.response,
                    'word_count': response.word_count,
                    'responded_at': response.responded_at.isoformat(),
                    'date': response.daily_set_date.isoformat() if response.daily_set_date else None,
                })

            pagination = {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit,
                'has_next': page * limit < total_count,
                'has_prev': page > 1,
            }

            return success_response(
                data={
                    
                    'history': history_data
                    
                },
                success_message='History retrieved successfully',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                error_message='Failed to retrieve history',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
