from rest_framework.decorators import api_view
import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404

from issues.models import Comment, Issue, IssueActivity, IssueStatus, Watcher, Attachment
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from api.serializers.issues import (
    CommentSerializer,
    IssueBulkInsertSerializer,
    IssueActivitySerializer,
    IssueDetailSerializer,
    IssueListSerializer,
    IssueStatusUpdateSerializer,
    WatcherSerializer,
    AttachmentSerializer,
    AttachmentCreateSerializer,
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
    def post(self, request):
        serializer = IssueDetailSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        issue = serializer.save(created_by=request.user)
        
        _add_activity(issue, request.user, 'created issue via API', issue.subject)
        
        return Response(
            IssueDetailSerializer(issue).data,
            status=status.HTTP_201_CREATED
        )

@api_view(['POST'])
def issue_bulk_insert(request):
    serializer = IssueBulkInsertSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    issues_text = serializer.validated_data['issues_text']
    selected_status = serializer.validated_data.get('status_id')
    default_status = selected_status or IssueStatus.objects.order_by('order', 'name').first()

    if not default_status:
        return Response(
            {'message': 'No statuses available to create issues.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    created_issues = []
    for raw_line in issues_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if '|' in line:
            subject, description = [part.strip() for part in line.split('|', 1)]
        else:
            subject, description = line, ''

        if not subject:
            continue

        issue = Issue.objects.create(
            subject=subject,
            description=description,
            status=default_status,
            created_by=request.user,
        )
        _add_activity(issue, request.user, 'created issue (bulk) via API', issue.subject)
        created_issues.append(issue)

    serializer = IssueListSerializer(created_issues, many=True)
    return Response(
        {
            'created_count': len(created_issues),
            'issues': serializer.data,
        },
        status=status.HTTP_201_CREATED,
    )


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

    def delete(self, request, issue_id):
        try:
            issue = Issue.objects.get(pk=issue_id)
        except Issue.DoesNotExist:
            return Response(
                {'message': f"No issue with id '{issue_id}' found."},
                status=status.HTTP_404_NOT_FOUND,
            )

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

@api_view(['GET', 'DELETE', 'PUT'])
def issue_detail(request, issue_id):
    issue = get_object_or_404(
        Issue.objects.select_related('status', 'assigned_to', 'created_by')
                     .prefetch_related('tags'),
        pk=issue_id,
    )

    if request.method == 'GET':
        serializer = IssueDetailSerializer(issue)
        return Response(serializer.data)

    if request.method == 'PUT':
        if issue.created_by != request.user:
            return Response(
                {'message': 'You do not have permission to update this issue.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = IssueDetailSerializer(issue, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        updated_issue = serializer.save()
        _add_activity(updated_issue, request.user, 'updated issue via API', updated_issue.subject)
        return Response(IssueDetailSerializer(updated_issue).data, status=status.HTTP_200_OK)

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

    username = request.data.get('username')
    if not username:
        return Response({'message': 'username is required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(User, username=username)
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
def issue_watcher_remove(request, issue_id, username):
    issue = get_object_or_404(Issue, pk=issue_id)
    deleted, _ = Watcher.objects.filter(issue=issue, user__username=username).delete()
    if deleted:
        _add_activity(issue, request.user, 'removed watcher via API', username)
        return Response(status=status.HTTP_204_NO_CONTENT)
    return Response({'message': 'Watcher not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def issue_activities(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    activities = IssueActivity.objects.filter(issue=issue).select_related('actor').order_by('-created_at')
    serializer = IssueActivitySerializer(activities, many=True)
    return Response(serializer.data)
    
@api_view(['GET', 'POST'])
def issue_attachments(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)

    if request.method == 'GET':
        attachments = issue.attachments.select_related('uploaded_by').all()
        serializer = AttachmentSerializer(attachments, many=True)
        return Response(serializer.data)

    serializer = AttachmentCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    attachment = serializer.save(
        issue=issue,
        uploaded_by=request.user
    )

    _add_activity(issue, request.user, 'added attachment via API', attachment.file.name)

    return Response(AttachmentSerializer(attachment).data, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
def attachment_delete(request, attachment_id):
    attachment = get_object_or_404(Attachment, pk=attachment_id)

    if attachment.uploaded_by != request.user:
        return Response(
            {'message': 'You do not have permission to delete this attachment.'},
            status=status.HTTP_403_FORBIDDEN
        )

    issue = attachment.issue
    filename = attachment.file.name

    file_path = attachment.file.path

    attachment.delete()

    import os
    if os.path.isfile(file_path):
        os.remove(file_path)

    _add_activity(issue, request.user, 'deleted attachment via API', filename)

    return Response(status=status.HTTP_204_NO_CONTENT)
