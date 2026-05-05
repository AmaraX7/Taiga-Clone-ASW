from rest_framework.decorators import api_view
import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from issues.models import Comment, Issue, IssueActivity, Watcher
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from api.serializers.issues import (
    CommentSerializer,
    IssueActivitySerializer,
    IssueDetailSerializer,
    IssueListSerializer,
    IssueStatusUpdateSerializer,
    WatcherSerializer,
)

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


def _add_activity(issue, actor, action, details=''):
    IssueActivity.objects.create(issue=issue, actor=actor, action=action, details=details)


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

@api_view(['DELETE'])
def issue_delete(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if issue.created_by != request.user:
        return Response(
            {'message': 'You do not have permission to delete this issue.'},
            status=status.HTTP_403_FORBIDDEN
        )
    issue.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def issue_set_status(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    serializer = IssueStatusUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    new_status = serializer.validated_data['status_id']
    issue.status = new_status
    issue.save(update_fields=['status'])
    _add_activity(issue, request.user, 'updated status via API', new_status.name)

    return Response({'id': issue.id, 'status': new_status.name}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def issue_watchers(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)

    if request.method == 'GET':
        watchers = issue.watchers.select_related('user').all()
        serializer = WatcherSerializer(watchers, many=True)
        return Response(serializer.data)

    user_id = request.data.get('user_id')
    if not user_id:
        return Response({'error': 'user_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, pk=user_id)
    watcher, created = Watcher.objects.get_or_create(issue=issue, user=user)
    if created:
        _add_activity(issue, request.user, 'added watcher via API', user.username)
        return Response(WatcherSerializer(watcher).data, status=status.HTTP_201_CREATED)
    else:
        return Response({'detail': 'Already watching.'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def issue_comments(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)

    if request.method == 'GET':
        comments = Comment.objects.filter(issue=issue).select_related('author')
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    serializer = CommentSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    comment = serializer.save(issue=issue, author=request.user)
    _add_activity(issue, request.user, 'added comment via API', comment.text[:80])
    return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


@api_view(['PUT', 'DELETE'])
def comment_detail(request, comment_id):
    comment = get_object_or_404(Comment.objects.select_related('issue'), pk=comment_id)

    if comment.author_id != request.user.id:
        return Response(
            {'message': 'You do not have permission to perform this action.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    if request.method == 'PUT':
        serializer = CommentSerializer(comment, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        updated_comment = serializer.save()
        _add_activity(updated_comment.issue, request.user, 'edited comment via API', updated_comment.text[:80])
        return Response(CommentSerializer(updated_comment).data, status=status.HTTP_200_OK)

    _add_activity(comment.issue, request.user, 'deleted comment via API', comment.text[:80])
    comment.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['DELETE'])
def issue_watcher_remove(request, issue_id, user_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    deleted, _ = Watcher.objects.filter(issue=issue, user_id=user_id).delete()
    if deleted:
        user = User.objects.filter(pk=user_id).first()
        _add_activity(issue, request.user, 'removed watcher via API', user.username if user else str(user_id))
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({'error': 'Watcher not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def issue_activities(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    activities = IssueActivity.objects.filter(issue=issue).select_related('actor').order_by('-created_at')
    serializer = IssueActivitySerializer(activities, many=True)
    return Response(serializer.data)
