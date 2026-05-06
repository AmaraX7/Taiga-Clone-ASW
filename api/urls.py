from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from api.views.catalogs import (
    IssuePriorityViewSet,
    IssueSeverityViewSet,
    IssueStatusViewSet,
    IssueTagViewSet,
    IssueTypeViewSet,
)
from api.views.issues import (
    IssueAssignView,
    issue_bulk_insert,
    IssueDeadlineView,
    IssueListView,
    comment_detail,
    issue_activities,
    issue_comments,
    issue_delete,
    issue_set_status,
    issue_watcher_remove,
    issue_watchers,
)
from api.views.users import UserDetailView, UserListView

app_name = 'api'


@api_view(['GET'])
@permission_classes([AllowAny])
def health(request):
    user = None
    if getattr(request, 'user', None) and request.user.is_authenticated:
        user = request.user.username
    return Response({'status': 'ok', 'user': user})


router = DefaultRouter()
router.register('statuses', IssueStatusViewSet, basename='status')
router.register('types', IssueTypeViewSet, basename='type')
router.register('severities', IssueSeverityViewSet, basename='severity')
router.register('priorities', IssuePriorityViewSet, basename='priority')
router.register('tags', IssueTagViewSet, basename='tag')


urlpatterns = [
    # Health
    path('', health, name='health'),
    # Catalogs (via router)
    *router.urls,

    # Issues
    path('issues/', IssueListView.as_view(), name='issue-list'),
    path('issues/bulk/', issue_bulk_insert, name='issue-bulk-insert'),
    path('issues/<int:issue_id>/', issue_delete, name='issue-delete'),
    path('issues/<int:issue_id>/deadline/', IssueDeadlineView.as_view(), name='issue-deadline'),
    path('issues/<int:issue_id>/assign/', IssueAssignView.as_view(), name='issue-assign'),
    path('issues/<int:issue_id>/status/', issue_set_status, name='api-issue-status'),
    path('issues/<int:issue_id>/comments/', issue_comments, name='api-issue-comments'),
    path('comments/<int:comment_id>/', comment_detail, name='api-comment-detail'),
    path('issues/<int:issue_id>/watchers/', issue_watchers, name='api-issue-watchers'),
    path('issues/<int:issue_id>/watchers/<int:user_id>/', issue_watcher_remove, name='api-issue-watcher-remove'),
    path('issues/<int:issue_id>/activities/', issue_activities, name='api-issue-activities'),

    # Users
    path('users/', UserListView.as_view(), name='api-users'),
    path('users/<str:username>/', UserDetailView.as_view(), name='api-user-detail'),
]
