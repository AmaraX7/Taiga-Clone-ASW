from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Issue(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('ready_for_test', 'Ready for test'),
        ('closed', 'Closed'),
        ('needs_info', 'Needs info'),
        ('rejected', 'Rejected'),
        ('postponed', 'Postponed'),
    ]
    TYPE_CHOICES = [
        ('bug', 'Bug'),
        ('question', 'Question'),
        ('enhancement', 'Enhancement'),
    ]
    SEVERITY_CHOICES = [
        ('wishlist', 'Wishlist'),
        ('minor', 'Minor'),
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('critical', 'Critical'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]

    subject     = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status      = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    issue_type  = models.CharField(max_length=20, choices=TYPE_CHOICES, default='bug')
    severity    = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='normal')
    priority    = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    # Añadimos el campo deadline que faltaba en tu modelo
    deadline    = models.DateField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_issues')
    created_by  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_issues')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.pk} {self.subject}"

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
