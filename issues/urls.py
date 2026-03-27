from django.urls import path
from . import views

urlpatterns = [
    path('', views.issue_list, name='issue_list'),
    path('issues/new/', views.issue_new, name='issue_new'),
    path('issues/<int:pk>/delete/', views.issue_delete, name='issue_delete'),
    path('issues/<int:issue_id>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:issue_id>/assign/', views.issue_assign, name='issue_assign'),
    path('issues/<int:issue_id>/attachments/add/', views.attachment_add, name='attachment_add'),
    path(
        'issues/<int:issue_id>/attachments/<int:attachment_id>/delete/',
        views.attachment_delete,
        name='attachment_delete',
    ),
]