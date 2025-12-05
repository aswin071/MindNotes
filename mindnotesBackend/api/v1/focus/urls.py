from django.urls import path, include
from .views import (
    FocusProgramListView,
    EnrollProgramView,
    StartProgramView,
    ProgramDetailsView,
    DayDetailsView,
    UpdateTaskStatusView,
    StartFocusSessionView,
    CompleteFocusSessionView,
    PauseSessionView,
    ResumeSessionView,
    AddDistractionView,
    AddReflectionView,
    WeeklyReviewView,
    ProgramHistoryView,
    ActiveSessionView,
    # Ritual views
    RitualDayDetailsView,
    StartRitualSessionView,
    StartRitualStepView,
    CompleteRitualStepView,
    SkipRitualStepView,
    CompleteRitualSessionView,
    ActiveRitualSessionView,
    RitualSessionDetailView,
    RitualHistoryView,
)

urlpatterns = [
    # Premium Focus Programs (Morning Charge, Brain Dump, Gratitude Pause)
    path('', include('api.v1.focus.premium_urls')),


    # Program management
    path('programs', FocusProgramListView.as_view(),                                                name='focus-programs-list'),
    path('programs/enroll', EnrollProgramView.as_view(),                                            name='focus-programs-enroll'),
    path('programs/start', StartProgramView.as_view(),                                              name='focus-programs-start'),
    path('programs/<int:enrollment_id>', ProgramDetailsView.as_view(),                              name='focus-programs-details'),
    path('programs/<int:enrollment_id>/days/<int:day_number>', DayDetailsView.as_view(),            name='focus-day-details'),
    path('programs/<int:enrollment_id>/weekly-review/<int:week_number>', WeeklyReviewView.as_view(), name='focus-weekly-review'),

    # Task management
    path('tasks/update', UpdateTaskStatusView.as_view(),                                                    name='focus-task-update'),

    # Focus sessions
    path('sessions/start', StartFocusSessionView.as_view(),                                                 name='focus-session-start'),
    path('sessions/complete', CompleteFocusSessionView.as_view(),                                           name='focus-session-complete'),
    path('sessions/pause', PauseSessionView.as_view(),                                                      name='focus-session-pause'),
    path('sessions/resume', ResumeSessionView.as_view(),                                                    name='focus-session-resume'),
    path('sessions/distraction', AddDistractionView.as_view(),                                              name='focus-session-distraction'),
    path('sessions/active', ActiveSessionView.as_view(),                                                    name='focus-session-active'),

    # Reflections
    path('reflections/add', AddReflectionView.as_view(),                                                    name='focus-reflection-add'),

    # History
    path('history', ProgramHistoryView.as_view(),                                                           name='focus-history'),

    # ============================================
    # RITUAL / MORNING CHARGE ENDPOINTS
    # ============================================

    # Ritual day details (with steps)
    path('rituals/<int:enrollment_id>/days/<int:day_number>', RitualDayDetailsView.as_view(),       name='ritual-day-details'),

    # Ritual sessions
    path('rituals/sessions/start', StartRitualSessionView.as_view(),                                name='ritual-session-start'),
    path('rituals/sessions/complete', CompleteRitualSessionView.as_view(),                          name='ritual-session-complete'),
    path('rituals/sessions/active', ActiveRitualSessionView.as_view(),                              name='ritual-session-active'),
    path('rituals/sessions/<str:session_id>', RitualSessionDetailView.as_view(),                    name='ritual-session-detail'),

    # Ritual steps
    path('rituals/steps/start', StartRitualStepView.as_view(),                                      name='ritual-step-start'),
    path('rituals/steps/complete', CompleteRitualStepView.as_view(),                                name='ritual-step-complete'),
    path('rituals/steps/skip', SkipRitualStepView.as_view(),                                        name='ritual-step-skip'),

    # Ritual history
    path('rituals/<int:enrollment_id>/history', RitualHistoryView.as_view(),                        name='ritual-history'),
]
