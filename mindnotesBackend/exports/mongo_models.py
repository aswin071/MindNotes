from mongoengine import Document, fields
from datetime import datetime


class ExportRequestMongo(Document):
    """
    MongoDB model for export request processing data
    Temporary data for export generation
    """
    user_id = fields.IntField(required=True, index=True)
    export_request_id = fields.IntField()  # Reference to PostgreSQL ExportRequest
    
    # Export configuration
    export_type = fields.StringField(choices=['journal', 'mood', 'focus', 'all'], required=True)
    date_range_start = fields.DateField()
    date_range_end = fields.DateField()
    format = fields.StringField(choices=['pdf', 'json', 'csv'], default='pdf')
    
    # Processing status
    status = fields.StringField(
        choices=['pending', 'processing', 'completed', 'failed'],
        default='pending'
    )
    
    # Data collection
    collected_entries = fields.ListField(fields.DictField())
    collected_moods = fields.ListField(fields.DictField())
    collected_sessions = fields.ListField(fields.DictField())
    
    # File generation
    file_path = fields.StringField()
    file_size = fields.IntField()
    download_url = fields.StringField()
    
    # Processing metadata
    processing_started_at = fields.DateTimeField()
    processing_completed_at = fields.DateTimeField()
    error_message = fields.StringField()
    
    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)
    
    meta = {
        'collection': 'export_requests',
        'indexes': [
            'user_id',
            'export_request_id',
            'status',
            'created_at',
        ],
        'ordering': ['-created_at'],
    }
    
    def __str__(self):
        return f"{self.user_id} - {self.export_type} - {self.status}"
