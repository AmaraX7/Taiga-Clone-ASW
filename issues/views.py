from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import Issue
from .forms import IssueForm


def get_default_user():
    return User.objects.get(username='admin')


def issue_list(request):
    issues = Issue.objects.all()
    return render(request, 'issues/list.html', {'issues': issues})


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
