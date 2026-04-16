from django import forms
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from .models import DueDatePreset, Issue, IssuePriority, IssueSeverity, IssueStatus, IssueTag, IssueType


class IssueForm(forms.ModelForm):
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Deadline',
    )
    
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label='Unassigned',
        label='Assign to',
    )
    issue_type = forms.ChoiceField(required=False, label='Type')
    severity = forms.ChoiceField(required=False, label='Severity')
    priority = forms.ChoiceField(required=False, label='Priority')
    tags = forms.ModelMultipleChoiceField(
        queryset=IssueTag.objects.none(),
        required=False,
        label='Tags',
        widget=forms.SelectMultiple(attrs={'size': 4}),
    )
    due_date_preset = forms.ModelChoiceField(
        queryset=DueDatePreset.objects.none(),
        required=False,
        empty_label='Custom / none',
        label='Due date preset',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['issue_type'].choices = [(opt.slug, opt.name) for opt in IssueType.objects.all()]
        self.fields['severity'].choices = [(opt.slug, opt.name) for opt in IssueSeverity.objects.all()]
        self.fields['priority'].choices = [(opt.slug, opt.name) for opt in IssuePriority.objects.all()]
        self.fields['tags'].queryset = IssueTag.objects.all()
        self.fields['due_date_preset'].queryset = DueDatePreset.objects.all()

    def save(self, commit=True):
        issue = super().save(commit=False)

        # Keep existing values on edit; apply model defaults on create when fields are omitted.
        issue.issue_type = self.cleaned_data.get('issue_type') or issue.issue_type or 'bug'
        issue.severity = self.cleaned_data.get('severity') or issue.severity or 'normal'
        issue.priority = self.cleaned_data.get('priority') or issue.priority or 'normal'

        preset = self.cleaned_data.get('due_date_preset')
        if preset:
            issue.deadline = timezone.now().date() + datetime.timedelta(days=preset.days_from_today)

        if commit:
            issue.save()
            self.save_m2m()
        return issue
    class Meta:
        model = Issue
        fields = ['subject', 'description', 'status', 'issue_type', 'severity', 'priority', 'deadline', 'assigned_to', 'tags']


class AssignIssueForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['assigned_to']

    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        empty_label='Unassigned',
    )


class AddWatcherForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=True,
        empty_label='Select user...',
    )


class AttachmentForm(forms.Form):
    file = forms.FileField()


class IssueStatusForm(forms.ModelForm):
    class Meta:
        model = Issue
        fields = ['status']


class BulkIssueInsertForm(forms.Form):
    issues_text = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'rows': 10,
                'placeholder': 'One issue per line. Use: Subject | Description',
            }
        ),
        help_text='Format: Subject | Description (description is optional).',
        label='Issues',
    )
    status = forms.ModelChoiceField(
        queryset=IssueStatus.objects.none(),
        required=False,
        empty_label='Use default status',
        label='Status for new issues',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['status'].queryset = IssueStatus.objects.all().order_by('order', 'name')
