from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Issue(models.Model):

    TYPE = [
        ('bug', 'Bug'),
        ('question', 'Question'),
        ('enhancement', 'Enhancement'),
    ]
        
    STATE = [
        ('new', 'New'),
        ('in_progress', 'In progress'),
        ('ready_for_test', 'Ready for test'),
        ('closed', 'Closed'),
        ('needs_info', 'Needs info'),
        ('rejected', 'Rejected'),
        ('postponed', 'Postponed'),
    ]

    PRIORITY = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
    ]

    SEVERITY = [
        ('wishlist', 'Wishlist'),
        ('minor', 'Minor'),
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('critical', 'Critical'),
    ]

    subject     = models.CharField(max_length=200)
    description = models.TextField(blank=True) #opcional
    created_at  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null = True)
    status      = models.CharField(max_length=20, choices=STATE, default='new')
    type        = models.CharField(max_length=20, choices=TYPE, default='bug')
    severity    = models.CharField(max_length=20, choices=SEVERITY, default='normal')
    priority    = models.CharField(max_length=20, choices=PRIORITY, default='normal')


    def __str__(self):
        return self.subject

    class Meta: 
        ordering = ['-created_at'] 