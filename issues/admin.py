from django.contrib import admin
from .models import Attachment, Comment, Issue, Watcher

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'status', 'issue_type', 'priority', 'severity', 'assigned_to', 'created_by', 'created_at')
    list_filter = ('status', 'issue_type', 'priority', 'severity')
    search_fields = ('subject', 'description')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'issue', 'author', 'created_at')
    search_fields = ('text',)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'issue', 'uploaded_by', 'created_at')


@admin.register(Watcher)
class WatcherAdmin(admin.ModelAdmin):
    list_display = ('user', 'issue', 'created_at')
