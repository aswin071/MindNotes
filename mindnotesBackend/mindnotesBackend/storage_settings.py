"""
Cloud Storage Configuration for MindNotes

This file contains settings for AWS S3 and Google Cloud Storage.
Choose one storage backend based on your deployment.
"""
import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================================
# LOCAL STORAGE (Development)
# ============================================================================
# Uncomment below for local file storage during development

# MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_URL = '/media/'
# DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'


# ============================================================================
# AWS S3 STORAGE (Production - Recommended)
# ============================================================================
# Uncomment below for AWS S3 storage in production
# Install: pip install django-storages boto3

"""
# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME', 'mindnotes-media')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')

# S3 Settings
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',  # 1 day cache
}
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False  # Don't add query string auth to URLs
AWS_S3_FILE_OVERWRITE = False  # Don't overwrite files with same name
AWS_S3_SIGNATURE_VERSION = 's3v4'

# Static and Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3StaticStorage'

# Media URL
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/'
"""


# ============================================================================
# GOOGLE CLOUD STORAGE (Production - Alternative)
# ============================================================================
# Uncomment below for Google Cloud Storage
# Install: pip install django-storages google-cloud-storage

"""
# GCS Configuration
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME', 'mindnotes-media')
GS_PROJECT_ID = os.getenv('GS_PROJECT_ID')
GS_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')  # Path to service account JSON

# GCS Settings
GS_DEFAULT_ACL = 'publicRead'
GS_FILE_OVERWRITE = False
GS_CACHE_CONTROL = 'public, max-age=86400'  # 1 day cache
GS_QUERYSTRING_AUTH = False

# Storage backend
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

# Media URL
MEDIA_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
"""


# ============================================================================
# CLOUDFLARE R2 STORAGE (Production - Cost-effective alternative)
# ============================================================================
# Uses S3-compatible API with zero egress fees
# Install: pip install django-storages boto3

"""
# Cloudflare R2 Configuration (S3-compatible)
AWS_ACCESS_KEY_ID = os.getenv('R2_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('R2_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('R2_BUCKET_NAME', 'mindnotes-media')
AWS_S3_ENDPOINT_URL = os.getenv('R2_ENDPOINT_URL')  # e.g., https://account-id.r2.cloudflarestorage.com
AWS_S3_CUSTOM_DOMAIN = os.getenv('R2_CUSTOM_DOMAIN')  # Optional: your custom domain

# R2 Settings
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_DEFAULT_ACL = None  # R2 doesn't use ACLs
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False

# Storage backend
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Media URL
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/' if AWS_S3_CUSTOM_DOMAIN else f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/'
"""


# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================
"""
1. Choose your storage backend (S3, GCS, or R2)
2. Uncomment the relevant configuration section above
3. Add the required environment variables to your .env file:

For AWS S3:
-----------
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=mindnotes-media
AWS_S3_REGION_NAME=us-east-1

For Google Cloud Storage:
--------------------------
GS_BUCKET_NAME=mindnotes-media
GS_PROJECT_ID=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

For Cloudflare R2:
------------------
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key
R2_BUCKET_NAME=mindnotes-media
R2_ENDPOINT_URL=https://account-id.r2.cloudflarestorage.com
R2_CUSTOM_DOMAIN=media.yourdomain.com  # Optional

4. Import this in settings.py:
   from .storage_settings import *

5. Run migrations if needed
6. Test with: python manage.py shell
   >>> from django.core.files.storage import default_storage
   >>> default_storage.bucket_name  # Should show your bucket name

7. For production, also configure CloudFront/CloudFlare CDN for better performance
"""
