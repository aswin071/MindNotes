from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q

from helpers.common import success_response, error_response
from journals.models import JournalEntry
from .serializers import JournalEntrySerializer


class JournalListCreateView(APIView, PageNumberPagination):
    permission_classes = [IsAuthenticated]
    page_size = 20

    def get(self, request):
        qs = JournalEntry.objects.filter(user=request.user)
        q = request.query_params.get('q')
        tag = request.query_params.get('tag')
        start = request.query_params.get('start')
        end = request.query_params.get('end')
        include_archived = request.query_params.get('include_archived') == 'true'

        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(content__icontains=q))
        if tag:
            qs = qs.filter(tags__name__iexact=tag)
        if start:
            qs = qs.filter(entry_date__date__gte=start)
        if end:
            qs = qs.filter(entry_date__date__lte=end)
        if not include_archived:
            qs = qs.filter(is_archived=False)

        qs = qs.select_related('user').prefetch_related('tags').order_by('-entry_date')
        page = self.paginate_queryset(qs, request, view=self)
        serializer = JournalEntrySerializer(page, many=True)
        return self.get_paginated_response({'data': serializer.data})

    def post(self, request):
        serializer = JournalEntrySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            entry = serializer.save()
            return success_response(data=JournalEntrySerializer(entry).data, success_message='Entry created')
        return error_response(errors=serializer.errors, error_message='Validation failed')


class JournalDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, entry_id):
        try:
            return JournalEntry.objects.select_related('user').prefetch_related('tags').get(user=user, id=entry_id)
        except JournalEntry.DoesNotExist:
            return None

    def get(self, request, entry_id):
        entry = self.get_object(request.user, entry_id)
        if not entry:
            return error_response(error_message='Entry not found', status=404)
        return success_response(data=JournalEntrySerializer(entry).data)

    def patch(self, request, entry_id):
        entry = self.get_object(request.user, entry_id)
        if not entry:
            return error_response(error_message='Entry not found', status=404)
        serializer = JournalEntrySerializer(entry, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            entry = serializer.save()
            return success_response(data=JournalEntrySerializer(entry).data, success_message='Entry updated')
        return error_response(errors=serializer.errors, error_message='Validation failed')

    def delete(self, request, entry_id):
        entry = self.get_object(request.user, entry_id)
        if not entry:
            return error_response(error_message='Entry not found', status=404)
        entry.delete()
        return success_response(success_message='Entry deleted')


class JournalCalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        year = int(request.query_params.get('year', timezone.now().year))
        month = request.query_params.get('month')
        qs = JournalEntry.objects.filter(user=request.user, entry_date__year=year)
        if month:
            qs = qs.filter(entry_date__month=int(month))
        qs = qs.order_by('entry_date').values('entry_date__date')
        counts = {}
        for row in qs:
            date_key = str(row['entry_date__date'])
            counts[date_key] = counts.get(date_key, 0) + 1
        return success_response(data={'year': year, 'month': int(month) if month else None, 'counts': counts})


