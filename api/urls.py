from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from api.views.users import UserListView, UserDetailView
from api.views.issues import IssueListView, IssueDeadlineView, IssueAssignView

app_name = 'api'


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'user': request.user.username})


urlpatterns = [
    path('', health, name='health'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<str:username>/', UserDetailView.as_view(), name='user-detail'),
    path('issues/', IssueListView.as_view(), name='issue-list'),
    path('issues/<int:issue_id>/deadline/', IssueDeadlineView.as_view(), name='issue-deadline'),
    path('issues/<int:issue_id>/assign/', IssueAssignView.as_view(), name='issue-assign'),
    # Comments/Attachments/Watchers (Membre C), Catalogs (Membre D)
]
