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
