from mongoengine import Document, EmbeddedDocument, fields
from datetime import datetime


class FocusSessionMongo(Document):
    """
    MongoDB model for focus sessions
    Real-time updates, time-series data
    """
    user_id = fields.IntField(required=True, index=True)

    # Session details
    session_type = fields.StringField(
        choices=['pomodoro', 'custom', 'program'],
        default='custom'
    )
    status = fields.StringField(
        choices=['active', 'completed', 'paused', 'canceled'],
        default='active'
    )

    # Durations (in seconds for precision)
    planned_duration_seconds = fields.IntField(required=True)
    actual_duration_seconds = fields.IntField(default=0)

    # Task
    task_description = fields.StringField()

    # Program association (PostgreSQL IDs)
    program_id = fields.IntField()
    program_day_id = fields.IntField()
    user_program_id = fields.IntField()  # Reference to UserFocusProgram

    # Real-time tracking
    started_at = fields.DateTimeField(required=True, index=True)
    ended_at = fields.DateTimeField()
    last_tick_at = fields.DateTimeField()  # For real-time updates

    # Pauses (embedded documents for efficiency)
    pauses = fields.ListField(fields.DictField())  # [{started: datetime, ended: datetime, duration: int}]
    total_pause_duration_seconds = fields.IntField(default=0)

    # Feedback
    productivity_rating = fields.IntField(min_value=1, max_value=5)
    notes = fields.StringField()

    # Distractions logged during session
    distractions = fields.ListField(fields.StringField())
    distraction_count = fields.IntField(default=0)

    # Tags for categorization
    tags = fields.ListField(fields.StringField())

    # Milestones (for gamification)
    milestones = fields.ListField(fields.DictField())

    is_active = fields.BooleanField(default=False, index=True)

    meta = {
        'collection': 'focus_sessions',
        'indexes': [
            'user_id',
            'started_at',
            'status',
            'program_id',
            ('user_id', '-started_at'),
            ('user_id', 'status'),
            ('user_id', 'program_id'),
        ],
        'ordering': ['-started_at'],
    }

    def add_pause(self):
        """Add a pause to the session"""
        pause = {
            'started_at': datetime.utcnow(),
            'ended_at': None,
            'duration_seconds': 0
        }
        self.pauses.append(pause)
        self.save()

    def resume_pause(self):
        """Resume from latest pause"""
        if self.pauses and self.pauses[-1]['ended_at'] is None:
            pause = self.pauses[-1]
            pause['ended_at'] = datetime.utcnow()
            pause['duration_seconds'] = int((pause['ended_at'] - pause['started_at']).total_seconds())
            self.total_pause_duration_seconds += pause['duration_seconds']
            self.save()

    def add_distraction(self, distraction_note: str):
        """Log a distraction during the session"""
        if not self.distractions:
            self.distractions = []
        self.distractions.append(distraction_note)
        self.distraction_count = len(self.distractions)
        self.save()

    def __str__(self):
        return f"{self.user_id} - {self.session_type} - {self.started_at.date()}"


class DailyTaskEmbed(EmbeddedDocument):
    """Embedded document for daily tasks within program days"""
    task_text = fields.StringField(required=True)
    is_completed = fields.BooleanField(default=False)
    completed_at = fields.DateTimeField()
    order = fields.IntField(default=0)


class ReflectionResponseEmbed(EmbeddedDocument):
    """Embedded document for reflection responses"""
    prompt_id = fields.IntField()  # Reference to ProgramDay reflection prompt
    question = fields.StringField(required=True)
    answer = fields.StringField()
    answered_at = fields.DateTimeField()


class StepResponseEmbed(EmbeddedDocument):
    """Embedded document for ritual step responses"""
    step_id = fields.IntField(required=True)  # Reference to ProgramStep in PostgreSQL
    step_order = fields.IntField(required=True)
    step_type = fields.StringField(required=True)

    # Completion tracking
    is_completed = fields.BooleanField(default=False)
    started_at = fields.DateTimeField()
    completed_at = fields.DateTimeField()
    duration_seconds = fields.IntField(default=0)  # Actual time spent

    # Response data (varies by step type)
    text_response = fields.StringField()  # For gratitude, journaling, prompts
    voice_note_url = fields.StringField()  # For voice responses
    selected_choice = fields.StringField()  # For affirmation selection
    selected_choices = fields.ListField(fields.StringField())  # For multi-choice
    rating_value = fields.IntField()  # For rating/slider responses

    # For breathing exercises
    breathing_cycles_completed = fields.IntField(default=0)

    # Metadata
    skipped = fields.BooleanField(default=False)
    skip_reason = fields.StringField()


class RitualSessionMongo(Document):
    """
    MongoDB model for ritual sessions (Morning Charge, Evening Wind-down, etc.)
    Different from FocusSession - designed for step-by-step guided flows
    """
    user_id = fields.IntField(required=True, index=True)

    # Program references (PostgreSQL IDs)
    program_id = fields.IntField(required=True, index=True)
    program_day_id = fields.IntField(required=True)
    user_program_id = fields.IntField(required=True, index=True)
    day_number = fields.IntField(required=True)

    # Session status
    status = fields.StringField(
        choices=['not_started', 'in_progress', 'completed', 'abandoned'],
        default='not_started'
    )

    # Timing
    started_at = fields.DateTimeField()
    completed_at = fields.DateTimeField()
    total_duration_seconds = fields.IntField(default=0)

    # Step tracking
    current_step_order = fields.IntField(default=0)
    total_steps = fields.IntField(required=True)
    steps_completed = fields.IntField(default=0)

    # Step responses (embedded)
    step_responses = fields.ListField(fields.EmbeddedDocumentField(StepResponseEmbed))

    # Session metrics
    completion_percentage = fields.FloatField(default=0.0)

    # Mood tracking (optional before/after)
    mood_before = fields.IntField(min_value=1, max_value=5)
    mood_after = fields.IntField(min_value=1, max_value=5)
    energy_level = fields.IntField(min_value=1, max_value=5)

    # Notes
    notes = fields.StringField()

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'ritual_sessions',
        'indexes': [
            'user_id',
            'program_id',
            'user_program_id',
            'status',
            ('user_id', '-created_at'),
            ('user_id', 'program_id', 'day_number'),
        ],
        'ordering': ['-created_at'],
    }

    def start_step(self, step_id: int, step_order: int, step_type: str):
        """Start a new step in the ritual"""
        step_response = StepResponseEmbed(
            step_id=step_id,
            step_order=step_order,
            step_type=step_type,
            started_at=datetime.utcnow()
        )
        self.step_responses.append(step_response)
        self.current_step_order = step_order
        self.updated_at = datetime.utcnow()
        self.save()
        return step_response

    def complete_step(self, step_order: int, response_data: dict = None):
        """Complete a step with optional response data"""
        for step_response in self.step_responses:
            if step_response.step_order == step_order:
                step_response.is_completed = True
                step_response.completed_at = datetime.utcnow()

                if step_response.started_at:
                    step_response.duration_seconds = int(
                        (step_response.completed_at - step_response.started_at).total_seconds()
                    )

                # Apply response data based on step type
                if response_data:
                    if 'text_response' in response_data:
                        step_response.text_response = response_data['text_response']
                    if 'voice_note_url' in response_data:
                        step_response.voice_note_url = response_data['voice_note_url']
                    if 'selected_choice' in response_data:
                        step_response.selected_choice = response_data['selected_choice']
                    if 'selected_choices' in response_data:
                        step_response.selected_choices = response_data['selected_choices']
                    if 'rating_value' in response_data:
                        step_response.rating_value = response_data['rating_value']
                    if 'breathing_cycles_completed' in response_data:
                        step_response.breathing_cycles_completed = response_data['breathing_cycles_completed']

                self.steps_completed += 1
                self.completion_percentage = (self.steps_completed / self.total_steps) * 100
                self.updated_at = datetime.utcnow()
                self.save()
                return True
        return False

    def skip_step(self, step_order: int, reason: str = ''):
        """Skip a step"""
        for step_response in self.step_responses:
            if step_response.step_order == step_order:
                step_response.skipped = True
                step_response.skip_reason = reason
                step_response.completed_at = datetime.utcnow()
                self.steps_completed += 1
                self.completion_percentage = (self.steps_completed / self.total_steps) * 100
                self.updated_at = datetime.utcnow()
                self.save()
                return True
        return False

    def complete_session(self, mood_after: int = None, energy_level: int = None):
        """Mark the entire ritual session as complete"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()

        if self.started_at:
            self.total_duration_seconds = int(
                (self.completed_at - self.started_at).total_seconds()
            )

        if mood_after:
            self.mood_after = mood_after
        if energy_level:
            self.energy_level = energy_level

        self.completion_percentage = 100.0
        self.updated_at = datetime.utcnow()
        self.save()

    def __str__(self):
        return f"Ritual Session - User {self.user_id} - Program {self.program_id} - Day {self.day_number}"


class UserProgramDayMongo(Document):
    """
    MongoDB model for user's daily program progress
    Stores user's completion status and progress for individual program days
    """
    user_id = fields.IntField(required=True, index=True)
    user_program_id = fields.IntField(required=True, index=True)  # Reference to UserFocusProgram in PostgreSQL
    program_id = fields.IntField(required=True, index=True)  # Reference to FocusProgram
    program_day_id = fields.IntField(required=True, index=True)  # Reference to ProgramDay
    day_number = fields.IntField(required=True)

    # Completion status
    is_completed = fields.BooleanField(default=False, index=True)
    completed_at = fields.DateTimeField()
    started_at = fields.DateTimeField()

    # Daily tasks (embedded)
    tasks = fields.ListField(fields.EmbeddedDocumentField(DailyTaskEmbed))
    tasks_completed_count = fields.IntField(default=0)
    tasks_total_count = fields.IntField(default=0)

    # Focus session tracking
    focus_sessions = fields.ListField(fields.StringField())  # List of FocusSessionMongo IDs
    total_focus_minutes = fields.IntField(default=0)
    target_focus_minutes = fields.IntField(default=0)  # From ProgramDay

    # Reflection responses (embedded)
    reflections = fields.ListField(fields.EmbeddedDocumentField(ReflectionResponseEmbed))
    reflections_completed = fields.BooleanField(default=False)

    # Notes
    notes = fields.StringField()

    # Rating
    difficulty_rating = fields.IntField(min_value=1, max_value=5)
    satisfaction_rating = fields.IntField(min_value=1, max_value=5)

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'user_program_days',
        'indexes': [
            'user_id',
            'user_program_id',
            'program_id',
            'day_number',
            'is_completed',
            ('user_id', 'program_id'),
            ('user_program_id', 'day_number'),
            ('user_id', 'user_program_id', 'day_number'),
        ],
        'ordering': ['day_number'],
    }

    def mark_task_completed(self, task_index: int):
        """Mark a specific task as completed"""
        if 0 <= task_index < len(self.tasks):
            self.tasks[task_index].is_completed = True
            self.tasks[task_index].completed_at = datetime.utcnow()
            self.tasks_completed_count = sum(1 for task in self.tasks if task.is_completed)
            self.updated_at = datetime.utcnow()
            self.save()

    def add_reflection_response(self, question: str, answer: str, prompt_id: int = None):
        """Add a reflection response"""
        reflection = ReflectionResponseEmbed(
            prompt_id=prompt_id,
            question=question,
            answer=answer,
            answered_at=datetime.utcnow()
        )
        self.reflections.append(reflection)
        self.updated_at = datetime.utcnow()
        self.save()

    def check_completion(self):
        """Check if day is fully completed (tasks + focus + reflection)"""
        tasks_done = self.tasks_completed_count == self.tasks_total_count if self.tasks_total_count > 0 else True
        focus_done = self.total_focus_minutes >= self.target_focus_minutes if self.target_focus_minutes > 0 else True
        reflections_done = len(self.reflections) > 0

        if tasks_done and focus_done and reflections_done and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()
            self.updated_at = datetime.utcnow()
            self.save()
            return True
        return False

    def __str__(self):
        return f"User {self.user_id} - Program {self.program_id} - Day {self.day_number}"


class ProgramProgressMongo(Document):
    """
    MongoDB model for aggregated program progress
    Stores weekly summaries and overall program statistics
    """
    user_id = fields.IntField(required=True, index=True)
    user_program_id = fields.IntField(required=True, index=True, unique=True)
    program_id = fields.IntField(required=True, index=True)

    # Overall progress
    total_days = fields.IntField(required=True)
    days_completed = fields.IntField(default=0)
    completion_percentage = fields.FloatField(default=0.0)

    # Focus statistics
    total_focus_minutes = fields.IntField(default=0)
    total_sessions = fields.IntField(default=0)
    average_session_length = fields.IntField(default=0)

    # Streak tracking
    current_streak = fields.IntField(default=0)
    longest_streak = fields.IntField(default=0)
    last_activity_date = fields.DateField()

    # Weekly summaries (embedded as dictionaries)
    # Structure: [{week: 1, days_completed: 5, focus_minutes: 150, summary: "Great week!"}]
    weekly_summaries = fields.ListField(fields.DictField())

    # Achievements/badges earned
    achievements = fields.ListField(fields.DictField())  # [{name: "First Week", earned_at: datetime}]

    # Overall ratings
    overall_difficulty = fields.FloatField()  # Average difficulty rating
    overall_satisfaction = fields.FloatField()  # Average satisfaction rating

    # Timestamps
    started_at = fields.DateTimeField()
    last_updated_at = fields.DateTimeField(default=datetime.utcnow)
    completed_at = fields.DateTimeField()

    meta = {
        'collection': 'program_progress',
        'indexes': [
            'user_id',
            'user_program_id',
            'program_id',
            ('user_id', 'program_id'),
        ],
    }

    def update_progress(self):
        """Recalculate and update progress statistics"""
        if self.total_days > 0:
            self.completion_percentage = (self.days_completed / self.total_days) * 100

        if self.total_sessions > 0:
            self.average_session_length = self.total_focus_minutes // self.total_sessions

        self.last_updated_at = datetime.utcnow()
        self.save()

    def add_weekly_summary(self, week_number: int, days_completed: int, focus_minutes: int, summary: str = ""):
        """Add or update weekly summary"""
        weekly_summary = {
            'week': week_number,
            'days_completed': days_completed,
            'focus_minutes': focus_minutes,
            'summary': summary,
            'created_at': datetime.utcnow()
        }

        # Check if week summary already exists
        existing_index = next((i for i, ws in enumerate(self.weekly_summaries) if ws['week'] == week_number), None)

        if existing_index is not None:
            self.weekly_summaries[existing_index] = weekly_summary
        else:
            self.weekly_summaries.append(weekly_summary)

        self.last_updated_at = datetime.utcnow()
        self.save()

    def add_achievement(self, achievement_name: str, description: str = ""):
        """Add an achievement/badge"""
        achievement = {
            'name': achievement_name,
            'description': description,
            'earned_at': datetime.utcnow()
        }

        # Check if achievement already exists
        if not any(ach['name'] == achievement_name for ach in self.achievements):
            self.achievements.append(achievement)
            self.save()

    def update_streak(self, is_active_today: bool):
        """Update streak information"""
        today = datetime.utcnow().date()

        if is_active_today:
            if self.last_activity_date:
                days_diff = (today - self.last_activity_date).days

                if days_diff == 1:
                    # Consecutive day
                    self.current_streak += 1
                elif days_diff > 1:
                    # Streak broken
                    self.current_streak = 1
                # If days_diff == 0, same day, don't increment
            else:
                # First activity
                self.current_streak = 1

            self.last_activity_date = today

            # Update longest streak
            if self.current_streak > self.longest_streak:
                self.longest_streak = self.current_streak

            self.save()

    def __str__(self):
        return f"Progress for User {self.user_id} - Program {self.program_id}"


# ============================================
# PREMIUM FOCUS PROGRAMS - MONGODB MODELS
# ============================================

class MorningChargeSessionMongo(Document):
    """
    MongoDB model for 5-Minute Morning Charge sessions
    Stores user's daily morning charge completion data
    """
    user_id = fields.IntField(required=True, index=True)
    session_date = fields.DateField(required=True, index=True)

    # Step 1: Wake & Breathe (1 min)
    breathing_completed = fields.BooleanField(default=False)
    breathing_completed_at = fields.DateTimeField()
    breathing_duration_seconds = fields.IntField(default=0)

    # Step 2: Gratitude Spark (1 min)
    gratitude_text = fields.StringField()
    gratitude_voice_note_url = fields.StringField()
    gratitude_completed_at = fields.DateTimeField()

    # Step 3: Positive Affirmation (1 min)
    affirmation_text = fields.StringField()
    affirmation_is_favorite = fields.BooleanField(default=False)
    affirmation_completed_at = fields.DateTimeField()

    # Step 4: Daily Clarity Prompt (1-2 min)
    clarity_prompt_question = fields.StringField()
    clarity_prompt_answer = fields.StringField()
    clarity_completed_at = fields.DateTimeField()

    # Step 5: Charge Close (30 sec)
    charge_close_completed = fields.BooleanField(default=False)
    charge_close_completed_at = fields.DateTimeField()

    # Overall session tracking
    is_completed = fields.BooleanField(default=False, index=True)
    completed_at = fields.DateTimeField()
    total_duration_seconds = fields.IntField(default=0)

    # Streak tracking
    current_streak = fields.IntField(default=0)

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow, index=True)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'morning_charge_sessions',
        'indexes': [
            'user_id',
            'session_date',
            'is_completed',
            ('user_id', '-session_date'),
            ('user_id', 'is_completed'),
        ],
        'ordering': ['-session_date'],
    }

    def __str__(self):
        return f"Morning Charge - User {self.user_id} - {self.session_date}"


class BrainDumpThoughtEmbed(EmbeddedDocument):
    """Embedded document for individual brain dump thoughts"""
    thought_text = fields.StringField(required=True)
    category_id = fields.IntField()  # Reference to BrainDumpCategory
    category_name = fields.StringField()
    order = fields.IntField(default=0)
    created_at = fields.DateTimeField(default=datetime.utcnow)


class BrainDumpSessionMongo(Document):
    """
    MongoDB model for Brain Dump Reset sessions
    Stores user's brain dump sessions with categorized thoughts
    """
    user_id = fields.IntField(required=True, index=True)
    session_date = fields.DateField(required=True, index=True)

    # Step 1: Settle In (1 min)
    settle_in_completed = fields.BooleanField(default=False)
    settle_in_completed_at = fields.DateTimeField()

    # Step 2: Write Your Dump (2 min) - bullet points
    dump_thoughts = fields.ListField(fields.EmbeddedDocumentField(BrainDumpThoughtEmbed))
    total_thoughts_count = fields.IntField(default=0)

    # Guided questions responses (if user needed help)
    guided_question_1_response = fields.StringField()  # "What's taking up most mental space?"
    guided_question_2_response = fields.StringField()  # "Is there something you keep postponing?"
    guided_question_3_response = fields.StringField()  # "What thought keeps replaying?"

    # Step 3: Categorize Your Thoughts - already embedded in thoughts
    categorize_completed = fields.BooleanField(default=False)
    categorize_completed_at = fields.DateTimeField()

    # Category distribution
    category_distribution = fields.DictField()  # {category_id: count}

    # Step 4: Choose One Task - from actionable items
    chosen_task_text = fields.StringField()
    chosen_task_category_id = fields.IntField()
    chosen_task_completed_at = fields.DateTimeField()

    # Step 5: Close & Breathe
    close_breathe_completed = fields.BooleanField(default=False)
    close_breathe_completed_at = fields.DateTimeField()

    # Overall session tracking
    is_completed = fields.BooleanField(default=False, index=True)
    completed_at = fields.DateTimeField()
    total_duration_seconds = fields.IntField(default=0)

    # Streak tracking
    current_streak = fields.IntField(default=0)

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow, index=True)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'brain_dump_sessions',
        'indexes': [
            'user_id',
            'session_date',
            'is_completed',
            ('user_id', '-session_date'),
            ('user_id', 'is_completed'),
        ],
        'ordering': ['-session_date'],
    }

    def __str__(self):
        return f"Brain Dump - User {self.user_id} - {self.session_date}"


class GratitudePauseSessionMongo(Document):
    """
    MongoDB model for Gratitude Pause sessions
    Stores user's gratitude pause deep dive sessions
    """
    user_id = fields.IntField(required=True, index=True)
    session_date = fields.DateField(required=True, index=True)

    # Step 1: Arrive (0:30)
    arrive_completed = fields.BooleanField(default=False)
    arrive_completed_at = fields.DateTimeField()

    # Step 2: List Three (0:30-2:00) - 3 gratitudes
    gratitude_1 = fields.StringField()
    gratitude_2 = fields.StringField()
    gratitude_3 = fields.StringField()
    list_three_completed_at = fields.DateTimeField()

    # Step 3: Deep Dive on One (2:00-4:15)
    selected_gratitude_index = fields.IntField()  # Which one they chose (1, 2, or 3)
    selected_gratitude_text = fields.StringField()

    # 5 Deep Dive Prompts
    deep_dive_1_precise = fields.StringField()  # "What exactly are you grateful for?"
    deep_dive_2_why_matters = fields.StringField()  # "How did this help your day?"
    deep_dive_3_who_made_possible = fields.StringField()  # "Who/what made it possible?"
    deep_dive_4_sensory_moment = fields.StringField()  # "Replay a moment"
    deep_dive_5_gratitude_line = fields.StringField()  # "I'm grateful for ___ because ___"

    deep_dive_completed_at = fields.DateTimeField()

    # Step 4: Express It Now (4:15-4:45)
    expression_action = fields.StringField(
        choices=['send_thank_you', 'leave_note', 'helpful_act', 'reminder_later', 'skipped'],
    )
    expression_notes = fields.StringField()
    expression_completed_at = fields.DateTimeField()

    # Step 5: Anchor (4:45-5:00)
    anchor_completed = fields.BooleanField(default=False)
    anchor_completed_at = fields.DateTimeField()

    # Overall session tracking
    is_completed = fields.BooleanField(default=False, index=True)
    completed_at = fields.DateTimeField()
    total_duration_seconds = fields.IntField(default=0)

    # Streak tracking
    current_streak = fields.IntField(default=0)

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow, index=True)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'gratitude_pause_sessions',
        'indexes': [
            'user_id',
            'session_date',
            'is_completed',
            ('user_id', '-session_date'),
            ('user_id', 'is_completed'),
        ],
        'ordering': ['-session_date'],
    }

    def __str__(self):
        return f"Gratitude Pause - User {self.user_id} - {self.session_date}"


class PremiumProgramStreakMongo(Document):
    """
    MongoDB model for tracking streaks across all premium programs
    Consolidated streak tracking for gamification
    """
    user_id = fields.IntField(required=True, index=True, unique=True)

    # Per-program streaks
    morning_charge_current_streak = fields.IntField(default=0)
    morning_charge_longest_streak = fields.IntField(default=0)
    morning_charge_last_activity = fields.DateField()
    morning_charge_total_sessions = fields.IntField(default=0)

    brain_dump_current_streak = fields.IntField(default=0)
    brain_dump_longest_streak = fields.IntField(default=0)
    brain_dump_last_activity = fields.DateField()
    brain_dump_total_sessions = fields.IntField(default=0)

    gratitude_pause_current_streak = fields.IntField(default=0)
    gratitude_pause_longest_streak = fields.IntField(default=0)
    gratitude_pause_last_activity = fields.DateField()
    gratitude_pause_total_sessions = fields.IntField(default=0)

    # Badges/Achievements
    badges = fields.ListField(fields.DictField())  # [{name, program_type, earned_at, description}]

    # Overall stats
    total_premium_sessions = fields.IntField(default=0)
    first_session_date = fields.DateField()

    # Timestamps
    created_at = fields.DateTimeField(default=datetime.utcnow)
    updated_at = fields.DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'premium_program_streaks',
        'indexes': [
            'user_id',
        ],
    }

    def update_streak(self, program_type: str, session_date):
        """
        Update streak for a specific program type
        program_type: 'morning_charge', 'brain_dump', or 'gratitude_pause'
        """
        from datetime import date, timedelta

        if isinstance(session_date, datetime):
            session_date = session_date.date()
        elif not isinstance(session_date, date):
            session_date = date.today()

        # Get program-specific fields
        current_streak_field = f"{program_type}_current_streak"
        longest_streak_field = f"{program_type}_longest_streak"
        last_activity_field = f"{program_type}_last_activity"
        total_sessions_field = f"{program_type}_total_sessions"

        last_activity = getattr(self, last_activity_field)
        current_streak = getattr(self, current_streak_field, 0)

        if last_activity:
            days_diff = (session_date - last_activity).days

            if days_diff == 0:
                # Same day, don't increment
                pass
            elif days_diff == 1:
                # Consecutive day
                current_streak += 1
            else:
                # Streak broken
                current_streak = 1
        else:
            # First session
            current_streak = 1

        # Update fields
        setattr(self, current_streak_field, current_streak)
        setattr(self, last_activity_field, session_date)

        # Update longest streak
        longest_streak = getattr(self, longest_streak_field, 0)
        if current_streak > longest_streak:
            setattr(self, longest_streak_field, current_streak)

        # Increment total sessions
        total_sessions = getattr(self, total_sessions_field, 0)
        setattr(self, total_sessions_field, total_sessions + 1)

        # Update overall stats
        self.total_premium_sessions += 1
        if not self.first_session_date:
            self.first_session_date = session_date

        self.updated_at = datetime.utcnow()
        self.save()

        return current_streak

    def add_badge(self, badge_name: str, program_type: str, description: str = ""):
        """Add a badge/achievement"""
        badge = {
            'name': badge_name,
            'program_type': program_type,
            'description': description,
            'earned_at': datetime.utcnow()
        }

        # Check if badge already exists
        if not any(b['name'] == badge_name and b['program_type'] == program_type for b in self.badges):
            self.badges.append(badge)
            self.updated_at = datetime.utcnow()
            self.save()

    def __str__(self):
        return f"Premium Streaks - User {self.user_id}"
