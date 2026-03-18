from django.contrib import admin
from .models import Issue

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'status', 'issue_type', 'priority', 'severity', 'assigned_to', 'created_by', 'created_at')
    list_filter = ('status', 'issue_type', 'priority', 'severity')
    search_fields = ('subject', 'description')
