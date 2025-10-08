from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.core.cache import cache

from core.services import JournalService
from helpers.common import success_response, error_response, paginated_response
from .serializers import (
    JournalEntryCreateSerializer,
    JournalEntryResponseSerializer,
    QuickJournalSerializer,
    TagSerializer
)
from journals.models import Tag
from journals.mongo_models import JournalEntryMongo, PhotoEmbed, VoiceNoteEmbed


class JournalAPIView(APIView):

    """
    GET /api/v1/journals/list

    Get paginated list of journal entries for authenticated user

    Query parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 20, max: 100)
    - entry_type: Filter by type (text, voice, photo, mixed)
    - is_favorite: Filter favorites (true/false)
    - tag_ids: Filter by tag IDs (comma-separated)
    - date_from: Filter from date (YYYY-MM-DD)
    - date_to: Filter to date (YYYY-MM-DD)

    User-specific: Only returns entries for authenticated user
    """
    """
    POST /api/v1/journals/create

    Create a new journal entry (all types: text, voice, photo, mixed)

    This endpoint supports:
    - Text entries with optional title and tags
    - Voice entries with audio files
    - Photo entries with images
    - Mixed entries with combination of above
    - Prompt responses embedded in entries
    - Location and weather data
    - Backdating entries

    User-specific: Each entry is tied to authenticated user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's journal entries"""
        user = request.user

        try:
            # Parse query parameters
            page = int(request.query_params.get('page', 1))
            limit = min(int(request.query_params.get('limit', 20)), 100)
            skip = (page - 1) * limit

            # Build filters
            filters = {'user_id': user.id}

            if request.query_params.get('entry_type'):
                filters['entry_type'] = request.query_params['entry_type']

            if request.query_params.get('is_favorite') == 'true':
                filters['is_favorite'] = True

            if request.query_params.get('tag_ids'):
                tag_ids = [int(tid) for tid in request.query_params['tag_ids'].split(',')]
                filters['tag_ids__in'] = tag_ids

            # Get entries from MongoDB
            entries = JournalEntryMongo.objects(**filters).order_by('-entry_date').skip(skip).limit(limit)
            total_count = JournalEntryMongo.objects(**filters).count()

            # Prepare response data
            entries_data = []
            for entry in entries:
                # Get tags
                tags = []
                if entry.tag_ids:
                    tags = list(Tag.objects.filter(id__in=entry.tag_ids, user=user).values(
                        'id', 'name', 'color'
                    ))

                entries_data.append({
                    'id': str(entry.id),
                    'title': entry.title or '',
                    'content': entry.content[:200] + '...' if entry.content and len(entry.content) > 200 else entry.content or '',
                    'entry_type': entry.entry_type,
                    'entry_date': entry.entry_date.isoformat(),
                    'is_favorite': entry.is_favorite,
                    'tags': tags,
                    'word_count': entry.word_count,
                    'photos_count': len(entry.photos) if entry.photos else 0,
                    'created_at': entry.created_at.isoformat(),
                })

            # Pagination metadata
            pagination_data = {
                'page': page,
                'limit': limit,
                'total': total_count,
                'pages': (total_count + limit - 1) // limit,
                'has_next': page * limit < total_count,
                'has_prev': page > 1,
            }

            return paginated_response(
                data=entries_data,
                items={'pagination': pagination_data},
                success_message='Entries retrieved successfully',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                error_message='Failed to retrieve journal entries',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def post(self, request):
        """Create a new journal entry"""
        user = request.user

        # Validate request data
        serializer = JournalEntryCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                errors=serializer.errors,
                error_message='Invalid journal entry data',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validated_data = serializer.validated_data

            # Create journal entry using service layer
            entry = JournalService.create_journal_entry(user, validated_data)

            # Get tags for response
            tag_ids = validated_data.get('tag_ids', [])
            tags = []
            if tag_ids:
                tags = list(Tag.objects.filter(id__in=tag_ids, user=user).values(
                    'id', 'name', 'color'
                ))

            # Prepare response data
            response_data = {
                'id': str(entry.id),
                'user_id': str(entry.user_id),
                'title': entry.title or '',
                'content': entry.content or '',
                'entry_type': entry.entry_type,
                'entry_date': entry.entry_date.isoformat(),
                'privacy': entry.privacy,
                'is_favorite': entry.is_favorite,
                'is_archived': entry.is_archived,
                'tag_ids': entry.tag_ids,
                'tags': tags,
                'location_name': entry.location_name or '',
                'weather': entry.weather or '',
                'word_count': entry.word_count,
                'character_count': entry.character_count,
                'reading_time_minutes': entry.reading_time_minutes,
                'photos_count': len(entry.photos) if entry.photos else 0,
                'voice_notes_count': len(entry.voice_notes) if entry.voice_notes else 0,
                'created_at': entry.created_at.isoformat(),
            }

            # Invalidate dashboard cache (entry count changed)
            cache.delete(f'dashboard_{user.id}')
            cache.delete(f'profile_stats_{user.id}')

            return success_response(
                data=response_data,
                success_message='Journal entry created successfully',
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                error_message='Failed to create journal entry',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuickJournalCreateView(APIView):
    """
    POST /api/v1/journals/quick

    Quick journal entry creation from Home screen quick actions
    (Voice, Speak, Photo buttons)

    This is a simplified endpoint for rapid journaling without
    needing all the fields of a full journal entry.

    Supports:
    - Quick voice recording
    - Quick text (speak-to-text)
    - Quick photo with optional caption

    User-specific: Each entry is tied to authenticated user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a quick journal entry"""
        user = request.user

        # Validate quick journal data
        serializer = QuickJournalSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                errors=serializer.errors,
                error_message='Invalid quick journal data',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            data = serializer.validated_data
            entry_type = data['entry_type']

            # Prepare journal entry data based on type
            journal_data = {
                'entry_type': entry_type,
                'privacy': 'private',  # Quick entries default to private
            }

            if entry_type == 'voice':
                # Voice entry
                journal_data['voice_notes'] = [{
                    'audio_url': data['audio_url'],
                    'duration': data.get('audio_duration', 0),
                }]
                journal_data['content'] = data.get('content', '')  # Optional transcription

            elif entry_type == 'photo':
                # Photo entry
                journal_data['photos'] = [{
                    'image_url': data['photo_url'],
                    'caption': data.get('photo_caption', ''),
                    'order': 0,
                }]
                journal_data['content'] = data.get('photo_caption', '')

            elif entry_type == 'text':
                # Text entry (speak-to-text)
                journal_data['content'] = data['content']

            # Create entry using service layer
            entry = JournalService.create_journal_entry(user, journal_data)

            # Prepare response
            response_data = {
                'id': str(entry.id),
                'entry_type': entry.entry_type,
                'content': entry.content or '',
                'entry_date': entry.entry_date.isoformat(),
                'word_count': entry.word_count,
                'created_at': entry.created_at.isoformat(),
            }

            # Invalidate caches
            cache.delete(f'dashboard_{user.id}')
            cache.delete(f'profile_stats_{user.id}')

            return success_response(
                data=response_data,
                success_message=f'Quick {entry_type} entry created successfully',
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                error_message='Failed to create quick journal entry',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TagCreateView(APIView):
    """
    POST /api/v1/journals/tags

    Create a new tag for organizing journal entries

    Tags are user-specific and stored in PostgreSQL
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Create a new tag"""
        user = request.user

        serializer = TagSerializer(data=request.data)

        if not serializer.is_valid():
            return error_response(
                errors=serializer.errors,
                error_message='Invalid tag data',
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Check if tag already exists
            tag_name = serializer.validated_data['name']
            existing_tag = Tag.objects.filter(user=user, name=tag_name).first()

            if existing_tag:
                return error_response(
                    errors={'name': 'Tag with this name already exists'},
                    error_message='Duplicate tag name',
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create tag
            tag = Tag.objects.create(
                user=user,
                name=serializer.validated_data['name'],
                color=serializer.validated_data.get('color', '#3B82F6')
            )

            return success_response(
                data=TagSerializer(tag).data,
                success_message='Tag created successfully',
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return error_response(
                error_message='Failed to create tag',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TagListView(APIView):
    """
    GET /api/v1/journals/tags

    Get all tags for the authenticated user

    Returns list of tags with their IDs, names, and colors
    User-specific: Only returns tags created by authenticated user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's tags"""
        user = request.user

        try:
            tags = Tag.objects.filter(user=user).order_by('name')
            serializer = TagSerializer(tags, many=True)

            return success_response(
                data=serializer.data,
                success_message='Tags retrieved successfully',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                error_message='Failed to retrieve tags',
                exception_info=str(e),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# class JournalAPIView(APIView):
#     """
#     GET /api/v1/journals/list

#     Get paginated list of journal entries for authenticated user

#     Query parameters:
#     - page: Page number (default: 1)
#     - limit: Items per page (default: 20, max: 100)
#     - entry_type: Filter by type (text, voice, photo, mixed)
#     - is_favorite: Filter favorites (true/false)
#     - tag_ids: Filter by tag IDs (comma-separated)
#     - date_from: Filter from date (YYYY-MM-DD)
#     - date_to: Filter to date (YYYY-MM-DD)

#     User-specific: Only returns entries for authenticated user
#     """

#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         """Get user's journal entries"""
#         user = request.user

#         try:
#             # Parse query parameters
#             page = int(request.query_params.get('page', 1))
#             limit = min(int(request.query_params.get('limit', 20)), 100)
#             skip = (page - 1) * limit

#             # Build filters
#             filters = {'user_id': user.id}

#             if request.query_params.get('entry_type'):
#                 filters['entry_type'] = request.query_params['entry_type']

#             if request.query_params.get('is_favorite') == 'true':
#                 filters['is_favorite'] = True

#             if request.query_params.get('tag_ids'):
#                 tag_ids = [int(tid) for tid in request.query_params['tag_ids'].split(',')]
#                 filters['tag_ids__in'] = tag_ids

#             # Get entries from MongoDB
#             entries = JournalEntryMongo.objects(**filters).order_by('-entry_date').skip(skip).limit(limit)
#             total_count = JournalEntryMongo.objects(**filters).count()

#             # Prepare response data
#             entries_data = []
#             for entry in entries:
#                 # Get tags
#                 tags = []
#                 if entry.tag_ids:
#                     tags = list(Tag.objects.filter(id__in=entry.tag_ids, user=user).values(
#                         'id', 'name', 'color'
#                     ))

#                 entries_data.append({
#                     'id': str(entry.id),
#                     'title': entry.title or '',
#                     'content': entry.content[:200] + '...' if entry.content and len(entry.content) > 200 else entry.content or '',
#                     'entry_type': entry.entry_type,
#                     'entry_date': entry.entry_date.isoformat(),
#                     'is_favorite': entry.is_favorite,
#                     'tags': tags,
#                     'word_count': entry.word_count,
#                     'photos_count': len(entry.photos) if entry.photos else 0,
#                     'created_at': entry.created_at.isoformat(),
#                 })

#             # Pagination metadata
#             pagination_data = {
#                 'page': page,
#                 'limit': limit,
#                 'total': total_count,
#                 'pages': (total_count + limit - 1) // limit,
#                 'has_next': page * limit < total_count,
#                 'has_prev': page > 1,
#             }

#             return paginated_response(
#                 data=entries_data,
#                 items={'pagination': pagination_data},
#                 success_message='Entries retrieved successfully',
#                 status=status.HTTP_200_OK
#             )

#         except Exception as e:
#             return error_response(
#                 error_message='Failed to retrieve journal entries',
#                 exception_info=str(e),
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#             )
