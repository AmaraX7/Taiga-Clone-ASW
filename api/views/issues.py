from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Q

from issues.models import Issue
from api.serializers.issues import IssueListSerializer

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
