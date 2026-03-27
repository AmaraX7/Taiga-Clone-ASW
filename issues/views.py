from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Issue, Comment
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







def issue_detail(request, pk):
    issue = Issue.objects.get(pk=pk)
    comments = issue.comments.all()
    return render(request, 'issues/detail.html', {
        'issue': issue,
        'comments': comments
    })

def comment_add(request, pk):
    issue = Issue.objects.get(pk=pk)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(
                issue=issue,
                author=get_default_user(),
                text=text
            )
    return redirect('issue_detail', pk=pk)

def comment_edit(request, pk):
    comment = Comment.objects.get(pk=pk)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment.text = text
            comment.save()
        return redirect('issue_detail', pk=comment.issue.pk)
    return render(request, 'issues/comment_edit.html', {'comment': comment})

def comment_delete(request, pk):
    comment = Comment.objects.get(pk=pk)
    issue_pk = comment.issue.pk
    if request.method == 'POST':
        comment.delete()
    return redirect('issue_detail', pk=issue_pk)
