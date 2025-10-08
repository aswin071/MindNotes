"""
Example usage of the hybrid database setup
This file demonstrates how to use PostgreSQL and MongoDB together
"""

from datetime import datetime, date
from django.contrib.auth import get_user_model
from core.services import (
    JournalService, 
    MoodService, 
    FocusService, 
    PromptService,
    AnalyticsService,
    ExportService
)

User = get_user_model()


def example_journal_operations():
    """
    Example: Creating and managing journal entries
    """
    # Get a user (assuming you have one)
    user = User.objects.first()
    
    # Create a journal entry with photos and voice notes
    journal_data = {
        'title': 'My First Entry',
        'content': 'Today was a great day! I learned so much about hybrid databases.',
        'entry_type': 'mixed',
        'entry_date': datetime.utcnow(),
        'privacy': 'private',
        'location_name': 'Home Office',
        'latitude': 40.7128,
        'longitude': -74.0060,
        'weather': 'Sunny',
        'temperature': 22.5,
        'tag_ids': [1, 2],  # References to PostgreSQL Tag model
        'photos': [
            {
                'image_url': '/media/journal_entries/photo1.jpg',
                'caption': 'My workspace',
                'width': 1920,
                'height': 1080,
                'file_size': 1024000
            }
        ],
        'voice_notes': [
            {
                'audio_url': '/media/voice_notes/note1.mp3',
                'duration': 120,
                'file_size': 2048000,
                'transcription': 'This is a voice note about my day'
            }
        ],
        'prompt_responses': [
            {
                'prompt_id': 1,  # Reference to PostgreSQL DailyPrompt
                'question': 'How was your day?',
                'answer': 'It was amazing!',
                'word_count': 3
            }
        ]
    }
    
    # Create the journal entry
    entry = JournalService.create_journal_entry(user, journal_data)
    print(f"Created journal entry: {entry.id}")
    
    # Search for entries
    entries = JournalService.search_entries(user, "great day")
    print(f"Found {len(entries)} entries matching 'great day'")
    
    # Get entries with filters
    filters = {
        'date_from': datetime(2024, 1, 1),
        'date_to': datetime(2024, 12, 31),
        'is_favorite': True
    }
    filtered_entries = JournalService.get_user_entries(user, filters)
    print(f"Found {len(filtered_entries)} filtered entries")


def example_mood_operations():
    """
    Example: Creating and managing mood entries
    """
    user = User.objects.first()
    
    # Create a mood entry
    mood_data = {
        'category_id': 1,  # Reference to PostgreSQL MoodCategory
        'category_name': 'Happy',
        'emoji': '😊',
        'intensity': 8,
        'note': 'Feeling great after completing the project',
        'factors': [
            {'id': 1, 'name': 'Sleep', 'value': 'good'},
            {'id': 2, 'name': 'Exercise', 'value': 'completed'},
            {'id': 3, 'name': 'Work', 'value': 'productive'}
        ],
        'recorded_at': datetime.utcnow(),
        'context': {
            'location': 'office',
            'time_of_day': 'afternoon'
        }
    }
    
    mood_entry = MoodService.create_mood_entry(user, mood_data)
    print(f"Created mood entry: {mood_entry.id}")
    
    # Get mood entries for the last week
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    filters = {
        'date_from': week_ago,
        'category_id': 1
    }
    recent_moods = MoodService.get_user_moods(user, filters)
    print(f"Found {len(recent_moods)} recent mood entries")


def example_focus_operations():
    """
    Example: Creating and managing focus sessions
    """
    user = User.objects.first()
    
    # Create a focus session
    session_data = {
        'session_type': 'pomodoro',
        'planned_duration_seconds': 1500,  # 25 minutes
        'task_description': 'Work on hybrid database implementation',
        'program_id': 1,  # Reference to PostgreSQL FocusProgram
        'program_day_id': 1,  # Reference to PostgreSQL ProgramDay
        'started_at': datetime.utcnow(),
        'tags': ['work', 'programming', 'database']
    }
    
    session = FocusService.create_focus_session(user, session_data)
    print(f"Created focus session: {session.id}")
    
    # Simulate real-time updates (every 30 seconds)
    import time
    for i in range(3):
        time.sleep(1)  # Simulate time passing
        duration = (i + 1) * 30
        updated_session = FocusService.update_session_tick(session.id, user, duration)
        print(f"Updated session duration: {duration} seconds")
    
    # Complete the session
    completion_data = {
        'productivity_rating': 4,
        'notes': 'Very productive session, completed the MongoDB models'
    }
    completed_session = FocusService.complete_session(session.id, user, completion_data)
    print(f"Completed session: {completed_session.id}")


def example_prompt_operations():
    """
    Example: Creating and managing prompt sets and responses
    """
    user = User.objects.first()
    
    # Create a daily prompt set
    prompts = [
        {
            'id': 1,
            'question': 'What are you grateful for today?',
            'category': 'gratitude'
        },
        {
            'id': 2,
            'question': 'What was the highlight of your day?',
            'category': 'reflection'
        },
        {
            'id': 3,
            'question': 'What would you like to improve tomorrow?',
            'category': 'planning'
        }
    ]
    
    prompt_set = PromptService.create_daily_prompt_set(user, date.today(), prompts)
    print(f"Created daily prompt set: {prompt_set.id}")
    
    # Submit responses to prompts
    response_data = {
        'prompt_id': 1,
        'daily_set_date': date.today(),
        'response': 'I am grateful for learning about hybrid databases and having a supportive team.',
        'time_spent_seconds': 120,
        'mood_at_response': 8,
        'location': {
            'name': 'Home Office',
            'latitude': 40.7128,
            'longitude': -74.0060
        }
    }
    
    response = PromptService.submit_prompt_response(user, response_data)
    print(f"Submitted prompt response: {response.id}")


def example_analytics_operations():
    """
    Example: Working with analytics data
    """
    user = User.objects.first()
    
    # Get user analytics
    analytics = AnalyticsService.get_user_analytics(user)
    if analytics:
        print(f"User analytics: {analytics.total_entries} entries, {analytics.current_streak} day streak")
    else:
        print("No analytics data found for user")
    
    # Update daily activity log
    activity_data = {
        'journal_entries_count': 1,
        'mood_entries_count': 1,
        'focus_sessions_count': 1,
        'total_words_written': 150,
        'total_focus_minutes': 25,
        'average_mood_intensity': 8.0,
        'has_journal_entry': True,
        'has_mood_entry': True,
        'has_focus_session': True
    }
    
    activity_log = AnalyticsService.update_daily_activity(user, date.today(), activity_data)
    print(f"Updated daily activity log: {activity_log.id}")


def example_export_operations():
    """
    Example: Creating and processing export requests
    """
    user = User.objects.first()
    
    # Create an export request
    export_data = {
        'export_request_id': 1,  # Reference to PostgreSQL ExportRequest
        'export_type': 'all',
        'date_range_start': date(2024, 1, 1),
        'date_range_end': date(2024, 12, 31),
        'format': 'pdf'
    }
    
    export_request = ExportService.create_export_request(user, export_data)
    print(f"Created export request: {export_request.id}")
    
    # Collect data for export
    collection_stats = ExportService.collect_export_data(export_request.id)
    if collection_stats:
        print(f"Collected data: {collection_stats['entries']} entries, "
              f"{collection_stats['moods']} moods, "
              f"{collection_stats['sessions']} sessions")
    else:
        print("Failed to collect export data")


def run_all_examples():
    """
    Run all examples
    """
    print("=== Hybrid Database Usage Examples ===\n")
    
    try:
        print("1. Journal Operations:")
        example_journal_operations()
        print()
        
        print("2. Mood Operations:")
        example_mood_operations()
        print()
        
        print("3. Focus Operations:")
        example_focus_operations()
        print()
        
        print("4. Prompt Operations:")
        example_prompt_operations()
        print()
        
        print("5. Analytics Operations:")
        example_analytics_operations()
        print()
        
        print("6. Export Operations:")
        example_export_operations()
        print()
        
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"Error running examples: {e}")


if __name__ == "__main__":
    # This would typically be run in a Django shell or management command
    run_all_examples()
