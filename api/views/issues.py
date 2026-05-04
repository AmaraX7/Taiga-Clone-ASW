from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from issues.models import Issue
from django.contrib.auth.models import User
from api.serializers.issues import IssueListSerializer, IssueDetailSerializer
from rest_framework import status
import datetime

_FILTER_FIELDS = {
    'type':        'issue_type',
    'severity':    'severity',
    'priority':    'priority',
    'status':      'status__slug',
    'assigned_to': 'assigned_to__username',
    'created_by':  'created_by__username',
}

_SORTABLE_FIELDS = {
    'id':          'id',
    'issue_type':  'issue_type',
    'subject':     'subject',
    'status':      'status__slug',
    'priority':    'priority',
    'severity':    'severity',
    'assigned_to': 'assigned_to__username',
    'modified_at': 'modified_at',
}


class IssueListView(APIView):
    def get(self, request):
        q = request.GET.get('q', '').strip()
        sort = request.GET.get('sort', 'modified_at')
        order = request.GET.get('order', 'desc')

        issues = Issue.objects.select_related(
            'status', 'assigned_to', 'created_by'
        ).prefetch_related('tags')

        if q:
            issues = issues.filter(
                Q(subject__icontains=q) | Q(description__icontains=q)
            )

        for param, field in _FILTER_FIELDS.items():
            values = request.GET.getlist(param)
            if values:
                issues = issues.filter(**{f'{field}__in': values})

        if sort in _SORTABLE_FIELDS:
            order_field = _SORTABLE_FIELDS[sort]
            if order == 'desc':
                order_field = f'-{order_field}'
            issues = issues.order_by(order_field)

        serializer = IssueListSerializer(issues, many=True)
        return Response(serializer.data)


class IssueDeadlineView(APIView):
    def post(self, request, issue_id):
        try:
            issue = Issue.objects.get(pk=issue_id)
        except Issue.DoesNotExist:
            return Response(
                {'message': f"No issue with id '{issue_id}' found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deadline_str = request.data.get('deadline')
        if deadline_str:
            try:
                issue.deadline = datetime.date.fromisoformat(deadline_str)
            except ValueError:
                return Response(
                    {'message': 'Invalid date format. Use YYYY-MM-DD'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            issue.deadline = None

        issue.save(update_fields=['deadline'])
        serializer = IssueDetailSerializer(issue)
        return Response(serializer.data)


class IssueAssignView(APIView):
    def post(self, request, issue_id):
        try:
            issue = Issue.objects.get(pk=issue_id)
        except Issue.DoesNotExist:
            return Response(
                {'message': f"No issue with id '{issue_id}' found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        username = request.data.get('assigned_to')
        if username:
            try:
                user = User.objects.get(username=username)
                issue.assigned_to = user
            except User.DoesNotExist:
                return Response(
                    {'message': f"No user with username '{username}' found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            issue.assigned_to = None

        issue.save(update_fields=['assigned_to'])
        serializer = IssueDetailSerializer(issue)
        return Response(serializer.data)
