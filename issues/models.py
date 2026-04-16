from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime


class IssueStatus(models.Model):
    """Statuses dels issues."""
    name       = models.CharField(max_length=50, unique=True)
    slug       = models.SlugField(max_length=50, unique=True)
    color      = models.CharField(max_length=7, default='#70728f',
                                  help_text='Hex colour, e.g. #4c9aff')
    is_closed  = models.BooleanField(default=False,
                                     help_text='Issues with this status count as closed')
    order      = models.PositiveSmallIntegerField(default=0)
 
    class Meta:
        ordering = ['order', 'name']
 
    def __str__(self):
        return self.name
    
    # Si no hi ha statuses els afegim
    @classmethod
    def get_default_statuses(cls):
        return [
            {'name': 'New',            'slug': 'new',            'color': '#83eede', 'is_closed': False, 'order': 0},
            {'name': 'In progress',    'slug': 'in_progress',    'color': '#e2b93b', 'is_closed': False, 'order': 1},
            {'name': 'Ready for test', 'slug': 'ready_for_test', 'color': '#4c9aff', 'is_closed': False, 'order': 2},
            {'name': 'Needs info',     'slug': 'needs_info',     'color': '#f5a623', 'is_closed': False, 'order': 3},
            {'name': 'Closed',         'slug': 'closed',         'color': '#a0a4b8', 'is_closed': True,  'order': 4},
            {'name': 'Rejected',       'slug': 'rejected',       'color': '#e44057', 'is_closed': True,  'order': 5},
            {'name': 'Postponed',      'slug': 'postponed',      'color': '#70728f', 'is_closed': True,  'order': 6},
        ]


class IssueType(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#4c9aff')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_defaults(cls):
        return [
            {'name': 'Bug', 'slug': 'bug', 'color': '#e44057', 'order': 0},
            {'name': 'Question', 'slug': 'question', 'color': '#8b5cf6', 'order': 1},
            {'name': 'Enhancement', 'slug': 'enhancement', 'color': '#0891b2', 'order': 2},
        ]


class IssueSeverity(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6b7280')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_defaults(cls):
        return [
            {'name': 'Wishlist', 'slug': 'wishlist', 'color': '#6b7280', 'order': 0},
            {'name': 'Minor', 'slug': 'minor', 'color': '#ca8a04', 'order': 1},
            {'name': 'Normal', 'slug': 'normal', 'color': '#16a34a', 'order': 2},
            {'name': 'Important', 'slug': 'important', 'color': '#ea580c', 'order': 3},
            {'name': 'Critical', 'slug': 'critical', 'color': '#b91c1c', 'order': 4},
        ]


class IssuePriority(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#22c55e')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    @classmethod
    def get_defaults(cls):
        return [
            {'name': 'Low', 'slug': 'low', 'color': '#eab308', 'order': 0},
            {'name': 'Normal', 'slug': 'normal', 'color': '#22c55e', 'order': 1},
            {'name': 'High', 'slug': 'high', 'color': '#ef4444', 'order': 2},
        ]


class IssueTag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#70728f')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class DueDatePreset(models.Model):
    name = models.CharField(max_length=50, unique=True)
    days_from_today = models.PositiveSmallIntegerField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'days_from_today']

    def __str__(self):
        return self.name

    @classmethod
    def get_defaults(cls):
        return [
            {'name': 'In one week', 'days_from_today': 7, 'order': 0},
            {'name': 'In two weeks', 'days_from_today': 14, 'order': 1},
            {'name': 'In one month', 'days_from_today': 30, 'order': 2},
            {'name': 'In three months', 'days_from_today': 90, 'order': 3},
        ]




class Issue(models.Model):
    subject     = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.ForeignKey(IssueStatus, on_delete=models.CASCADE)
    issue_type  = models.CharField(max_length=20, default='bug')
    severity    = models.CharField(max_length=20, default='normal')
    priority    = models.CharField(max_length=10, default='normal')
    tags        = models.ManyToManyField(IssueTag, blank=True, related_name='issues')
    # Añadimos el campo deadline que faltaba en tu modelo
    deadline    = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_issues')
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_issues')
    created_at  = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} {self.subject}"

    @property
    def issue_type_label(self):
        type_obj = IssueType.objects.filter(slug=self.issue_type).only('name').first()
        return type_obj.name if type_obj else self.issue_type

    @property
    def severity_label(self):
        severity_obj = IssueSeverity.objects.filter(slug=self.severity).only('name').first()
        return severity_obj.name if severity_obj else self.severity

    @property
    def priority_label(self):
        priority_obj = IssuePriority.objects.filter(slug=self.priority).only('name').first()
        return priority_obj.name if priority_obj else self.priority

    @property
    def deadline_status(self):
        """Calcula el color del reloj basado en la fecha límite puramente en Python."""
        if not self.deadline:
            return None
            
        today = timezone.now().date()
        two_weeks = today + datetime.timedelta(days=14)
        
        if self.deadline < today:
            return 'red'
        elif today <= self.deadline <= two_weeks:
            return 'orange'
        else:
            return 'green'


class Comment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issue_comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment #{self.pk} on issue #{self.issue_id}"


class Attachment(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issue_attachments')
    file = models.FileField(upload_to='issues/attachments/')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Attachment #{self.pk} on issue #{self.issue_id}"


class Watcher(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='watchers')
    user  = models.ForeignKey(User,  on_delete=models.CASCADE, related_name='watched_issues')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('issue', 'user')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} watching #{self.issue_id}"


class IssueActivity(models.Model):
    issue = models.ForeignKey(Issue, on_delete=models.CASCADE, related_name='activities')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='issue_activities')
    action = models.CharField(max_length=50)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.actor.username} {self.action} on #{self.issue_id}"
