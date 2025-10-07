from django.urls import path
from .views import JournalListCreateView, JournalDetailView, JournalCalendarView


urlpatterns = [
    path('', JournalListCreateView.as_view(), name='journal-list-create'),
    path('<uuid:entry_id>/', JournalDetailView.as_view(), name='journal-detail'),
    path('calendar/', JournalCalendarView.as_view(), name='journal-calendar'),
]


