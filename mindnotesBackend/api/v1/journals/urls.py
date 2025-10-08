from django.urls import path
from .views import (
    QuickJournalCreateView,
    JournalAPIView,
    TagCreateView,
    TagListView,
)


urlpatterns = [
    # Journal Entry Management
    path('create', JournalAPIView.as_view(), name='journal-create'),
    path('quick', QuickJournalCreateView.as_view(), name='journal-quick-create'),
    path('list', JournalAPIView.as_view(), name='journal-list'),

    # Tag Management
    path('tags', TagListView.as_view(), name='tag-list'),
    path('tags/create', TagCreateView.as_view(), name='tag-create'),
]



