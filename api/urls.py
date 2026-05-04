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
from api.views.issues import issue_set_status, issue_watchers, issue_watcher_remove

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
    path('issues/<int:issue_id>/status/', issue_set_status, name='api-issue-status'),
    path('issues/<int:issue_id>/watchers/', issue_watchers, name='api-issue-watchers'),
    path('issues/<int:issue_id>/watchers/<int:user_id>/', issue_watcher_remove, name='api-issue-watcher-remove'),
]