from django.core.management.base import BaseCommand
from utils.mongo import ensure_mongo_indexes, get_mongo_stats


class Command(BaseCommand):
    help = 'Initialize MongoDB indexes and check connection'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show MongoDB database statistics',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Initializing MongoDB...')
        )
        
        try:
            # Ensure indexes are created
            ensure_mongo_indexes()
            
            self.stdout.write(
                self.style.SUCCESS('MongoDB indexes created successfully!')
            )
            
            if options['stats']:
                stats = get_mongo_stats()
                if 'error' in stats:
                    self.stdout.write(
                        self.style.ERROR(f'Error getting stats: {stats["error"]}')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('MongoDB Statistics:')
                    )
                    for key, value in stats.items():
                        self.stdout.write(f'  {key}: {value}')
                        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error initializing MongoDB: {e}')
            )
