from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Issue
from .forms import IssueForm


def get_default_user():
    user, _ = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com'},
    )
    return user


def issue_list(request):
    q = request.GET.get('q', '').strip()
    issues = Issue.objects.all()
    if q:
        issues = issues.filter(
            Q(subject__icontains=q) | Q(description__icontains=q)
        )
    return render(request, 'issues/list.html', {'issues': issues, 'query': q})


def issue_new(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            user = get_default_user()
            issue.created_by = user
            issue.assigned_to = user
            issue.save()
            return redirect('issue_list')
    else:
        form = IssueForm()
    return render(request, 'issues/new.html', {'form': form})

def issue_delete(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.method == 'POST':
        issue.delete()
        return redirect('issue_list')
    return render(request, 'issues/delete.html', {'issue': issue})
