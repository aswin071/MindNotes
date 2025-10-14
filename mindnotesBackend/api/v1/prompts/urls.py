from django.urls import path
from .views import (
    TodayPromptsView,
    PromptResponseView,
    PromptStreakView,
    PromptHistoryView,
)


urlpatterns = [
    path('today', TodayPromptsView.as_view(),                                          name='prompts-today'),
    path('respond', PromptResponseView.as_view(),                                      name='prompts-respond'),
    path('streak', PromptStreakView.as_view(),                                         name='prompts-streak'),
    path('history', PromptHistoryView.as_view(),                                       name='prompts-history'),
]

