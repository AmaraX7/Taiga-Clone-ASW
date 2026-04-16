from django.urls import path
from . import views

urlpatterns = [
    path('', views.issue_list, name='issue_list'),
    path('issues/new/', views.issue_new, name='issue_new'),
    path('issues/<int:issue_id>/delete/', views.issue_delete, name='issue_delete'),
    path('issues/<int:issue_id>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:issue_id>/assign/', views.issue_assign, name='issue_assign'),
    path('issues/<int:issue_id>/attachments/add/', views.attachment_add, name='attachment_add'),
    path(
        'issues/<int:issue_id>/attachments/<int:attachment_id>/delete/',
        views.attachment_delete,
        name='attachment_delete',
    ),
    path('issues/<int:issue_id>/comments/add/', views.comment_add, name='comment_add'),
    path('comments/<int:comment_id>/edit/', views.comment_edit, name='comment_edit'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('issues/<int:issue_id>/watch/',   views.watcher_add,    name='watcher_add'),
    path('issues/<int:issue_id>/unwatch/', views.watcher_remove, name='watcher_remove'),
    path('issues/<int:issue_id>/deadline/', views.issue_set_deadline, name='issue_set_deadline'),
    path("issues/<int:issue_id>/status/", views.issue_update_status, name="issue_update_status"),

    # ---Settings---
    
    # Statuses
    
    path('settings/',				views.settings_view,  name='settings_view'),
    path('settings/statuses/new/',		views.status_create,  name='status_create'),
    path('settings/statuses/<int:pk>/edit/',	views.status_edit,    name='status_edit'),
    path('settings/statuses/<int:pk>/delete/',views.status_delete, name='status_delete'),
    path('settings/statuses/reorder/',	views.status_reorder, name='status_reorder'),
]
