from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.cache import cache
import re

from core.services import JournalService
from helpers.common import success_response, error_response, paginated_response
from .serializers import (
    JournalEntryCreateSerializer,
    JournalEntryResponseSerializer,
    QuickJournalSerializer,
    TagSerializer,
    JournalDetailSerializer
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
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _parse_nested_formdata(self, data):
        """
        Parse nested form-data like photos[0][caption] into structured dict
        Handles arrays and nested objects from multipart/form-data
        """
        parsed = {}

        for key, value in data.items():
            # Check if it's a nested key like photos[0][caption]
            match = re.match(r'^(\w+)\[(\d+)\]\[(\w+)\]$', key)
            if match:
                field_name, index, sub_field = match.groups()
                index = int(index)

                # Initialize array if not exists
                if field_name not in parsed:
                    parsed[field_name] = []

                # Extend array if needed
                while len(parsed[field_name]) <= index:
                    parsed[field_name].append({})

                # Set the value (handle file uploads)
                parsed[field_name][index][sub_field] = value[0] if isinstance(value, list) else value

            # Check for simple array like tag_ids[0]
            elif re.match(r'^(\w+)\[(\d+)\]$', key):
                match = re.match(r'^(\w+)\[(\d+)\]$', key)
                field_name, index = match.groups()
                index = int(index)

                if field_name not in parsed:
                    parsed[field_name] = []

                while len(parsed[field_name]) <= index:
                    parsed[field_name].append(None)

                parsed[field_name][index] = value[0] if isinstance(value, list) else value

            # Simple field
            else:
                parsed[key] = value[0] if isinstance(value, list) else value

        return parsed

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

            # Batch fetch all tags to avoid N+1 query problem
            all_tag_ids = set()
            for entry in entries:
                if entry.tag_ids:
                    all_tag_ids.update(list(entry.tag_ids))

            # Fetch all tags in one query and create lookup dict
            tags_dict = {}
            if all_tag_ids:
                tags_list = Tag.objects.filter(id__in=all_tag_ids, user=user).values('id', 'name', 'color')
                tags_dict = {tag['id']: tag for tag in tags_list}

            # Prepare response data
            entries_data = []
            for entry in entries:
                # Get tags from pre-fetched dict
                tags = []
                if entry.tag_ids:
                    for tag_id in entry.tag_ids:
                        if tag_id in tags_dict:
                            tags.append(tags_dict[tag_id])

                # Safely get photos data
                photos_data = []
                photos_count = 0
                try:
                    if entry.photos:
                        photos_count = len(entry.photos)
                        for photo in entry.photos:
                            photos_data.append({
                                'image_url': photo.image_url,
                                'caption': photo.caption or '',
                                'order': photo.order,
                            })
                except (AttributeError, TypeError):
                    photos_count = 0

                entries_data.append({
                    'id': str(entry.id),
                    'title': entry.title or '',
                    'content': entry.content[:200] + '...' if entry.content and len(entry.content) > 200 else entry.content or '',
                    'entry_type': entry.entry_type,
                    'entry_date': entry.entry_date.isoformat(),
                    'is_favorite': entry.is_favorite,
                    'tags': tags,
                    'word_count': entry.word_count,
                    'photos_count': photos_count,
                    'photos': photos_data,
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

        # Parse nested form-data if it's multipart
        if request.content_type and 'multipart' in request.content_type:
            parsed_data = self._parse_nested_formdata(request.data)
        else:
            parsed_data = request.data

        # Validate request data
        serializer = JournalEntryCreateSerializer(data=parsed_data)

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


class JournalDetailView(APIView):
    """
    POST /api/v1/journals/detail

    Get complete details for a single journal entry

    Request Body:
    {
        "entry_id": "required_entry_id"
    }

    Returns:
    - Full journal content (not truncated)
    - All photos with full URLs
    - All voice notes
    - Tags with colors
    - Location and weather data
    - Mood information (if associated)
    - Reading statistics
    - All metadata

    Optimized with:
    - Single MongoDB query for entry
    - Batch tag loading (no N+1)
    - Mood lookup
    - Cached for 5 minutes

    User-specific: Only returns entries owned by authenticated user
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Get detailed journal entry"""
        user = request.user
        entry_id = request.data.get("entry_id")

        if not entry_id:
            return error_response(
                error_message='entry_id is required',
                status=status.HTTP_400_BAD_REQUEST
            )
        

        # # Check cache first
        cache_key = f'journal_detail_{user.id}_{entry_id}'
        cached_data = cache.get(cache_key)

        
        if cached_data:
            return success_response(
                data=cached_data,
                success_message='Journal entry retrieved from cache',
                status=status.HTTP_200_OK
            )
        
        try:
            # Use service layer to get entry details
            entry_data = JournalService.get_entry_detail(entry_id, user)

            if not entry_data:
                return error_response(
                    error_message='Journal entry not found',
                    status=status.HTTP_404_NOT_FOUND
                )

            # Use serializer for consistent data formatting
            serializer = JournalDetailSerializer(entry_data)
            serialized_data = serializer.data

            # Cache for 5 minutes
            cache.set(cache_key, serialized_data, 300)

            return success_response(
                data=serialized_data,
                success_message='Journal entry retrieved successfully',
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return error_response(
                error_message='Failed to retrieve journal entry',
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
