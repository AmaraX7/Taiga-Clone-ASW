from django.shortcuts import render, redirect, get_object_or_404
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
            issue.created_by = get_default_user()
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