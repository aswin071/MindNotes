"""
Celery tasks for background processing
"""
from celery import shared_task
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from datetime import datetime
import base64
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def upload_file_to_storage(self, file_content_b64, filename, user_id):
    """
    Async task to upload file to storage (local or cloud)

    Args:
        file_content_b64: Base64 encoded file content
        filename: Original filename
        user_id: User ID for organizing files

    Returns:
        dict: {'success': bool, 'url': str, 'path': str}
    """
    try:
        # Decode base64 file content
        file_content = base64.b64decode(file_content_b64)

        # Generate unique filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        storage_path = f"media/journals/{user_id}/{timestamp}_{filename}"

        # Save file to storage
        path = default_storage.save(storage_path, ContentFile(file_content))

        # Get URL (works with both local and cloud storage)
        url = default_storage.url(path)

        logger.info(f"File uploaded successfully: {path}")

        return {
            'success': True,
            'url': url,
            'path': path,
            'size': len(file_content)
        }

    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                'success': False,
                'error': str(e)
            }


@shared_task(bind=True, max_retries=3)
def upload_multiple_files(self, files_data):
    """
    Async task to upload multiple files in parallel

    Args:
        files_data: List of dicts with 'content_b64', 'filename', 'user_id'

    Returns:
        list: List of upload results
    """
    results = []

    for file_data in files_data:
        try:
            result = upload_file_to_storage.apply_async(
                args=[
                    file_data['content_b64'],
                    file_data['filename'],
                    file_data['user_id']
                ]
            )
            results.append({'task_id': result.id, 'filename': file_data['filename']})
        except Exception as e:
            logger.error(f"Failed to queue file upload: {str(e)}")
            results.append({'success': False, 'error': str(e), 'filename': file_data['filename']})

    return results


@shared_task
def cleanup_old_uploads(days=30):
    """
    Cleanup uploaded files older than specified days

    Args:
        days: Number of days to keep files
    """
    # TODO: Implement cleanup logic
    logger.info(f"Cleanup task triggered for files older than {days} days")
    pass


@shared_task(bind=True, max_retries=3)
def generate_dynamic_prompts_async(self, user_id, count=20):
    """
    Async task to generate dynamic prompts in background

    Args:
        user_id: User ID for generating personalized prompts
        count: Number of prompts to generate (default: 20)

    Returns:
        dict: {'success': bool, 'count': int, 'error': str}
    """
    try:
        from django.contrib.auth import get_user_model
        from core.prompt_service import PromptService

        User = get_user_model()
        user = User.objects.get(id=user_id)

        logger.info(f"Starting dynamic prompt generation for user {user_id}")

        # Generate prompts
        created_prompts = PromptService._generate_dynamic_prompts(user, count)

        logger.info(f"Successfully generated {len(created_prompts)} prompts for user {user_id}")

        return {
            'success': True,
            'count': len(created_prompts),
            'user_id': user_id
        }

    except Exception as e:
        logger.error(f"Dynamic prompt generation failed for user {user_id}: {str(e)}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=e, countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                'success': False,
                'error': str(e),
                'user_id': user_id
            }


@shared_task
def generate_daily_prompts_batch(user_ids):
    """
    Generate daily prompts for multiple users (for scheduled tasks)

    Args:
        user_ids: List of user IDs

    Returns:
        dict: Summary of generation results
    """
    from core.prompt_service import PromptService
    from django.contrib.auth import get_user_model
    from datetime import date

    User = get_user_model()
    results = {'success': 0, 'failed': 0, 'errors': []}

    for user_id in user_ids:
        try:
            user = User.objects.get(id=user_id)
            PromptService.generate_daily_prompts(user, date.today())
            results['success'] += 1
        except Exception as e:
            results['failed'] += 1
            results['errors'].append({'user_id': user_id, 'error': str(e)})
            logger.error(f"Failed to generate prompts for user {user_id}: {str(e)}")

    logger.info(f"Batch prompt generation: {results['success']} succeeded, {results['failed']} failed")
    return results
