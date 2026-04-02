from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Attachment, Comment, Issue
from .forms import AssignIssueForm, AttachmentForm, IssueForm


SORTABLE_FIELDS = {
    'id': 'id',
    'issue_type': 'issue_type',
    'subject': 'subject',
    'status': 'status',
    'priority': 'priority',
    'severity': 'severity',
    'assigned_to': 'assigned_to__username',
    'created_at': 'created_at',
}

FILTER_FIELDS = {
    'type': 'issue_type',
    'severity': 'severity',
    'priority': 'priority',
    'status': 'status',
    'assigned_to': 'assigned_to__id',
    'created_by': 'created_by__id',
}

FILTER_LABELS = {
    'type': 'Type',
    'severity': 'Severity',
    'priority': 'Priority',
    'status': 'Status',
    'assigned_to': 'Assigned to',
    'created_by': 'Created by',
}


@login_required
def issue_list(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'created_at')
    order = request.GET.get('order', 'desc')

    issues = Issue.objects.all()

    if q:
        issues = issues.filter(
            Q(subject__icontains=q) | Q(description__icontains=q)
        )

    # Apply include filters (AND between categories, OR within a category)
    active_filters = {}
    for param, field in FILTER_FIELDS.items():
        values = request.GET.getlist(param)
        if values:
            issues = issues.filter(**{f'{field}__in': values})
            active_filters[param] = values

    if sort in SORTABLE_FIELDS:
        order_field = SORTABLE_FIELDS[sort]
        if order == 'desc':
            order_field = f'-{order_field}'
        issues = issues.order_by(order_field)

    filter_options = {
        'type': Issue.TYPE_CHOICES,
        'severity': Issue.SEVERITY_CHOICES,
        'priority': Issue.PRIORITY_CHOICES,
        'status': Issue.STATUS_CHOICES,
        'assigned_to': [
            (str(u.id), u.username)
            for u in User.objects.filter(
                assigned_issues__isnull=False
            ).distinct().order_by('username')
        ],
        'created_by': [
            (str(u.id), u.username)
            for u in User.objects.filter(
                created_issues__isnull=False
            ).distinct().order_by('username')
        ],
    }

    return render(request, 'issues/list.html', {
        'issues': issues,
        'query': q,
        'current_sort': sort,
        'current_order': order,
        'filter_options': filter_options,
        'filter_labels': FILTER_LABELS,
        'active_filters': active_filters,
    })


@login_required
def issue_new(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            return redirect('issue_list')
    else:
        form = IssueForm()
    return render(request, 'issues/new.html', {'form': form})


@login_required
def issue_delete(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    if request.method == 'POST':
        issue.delete()
        return redirect('issue_list')
    return render(request, 'issues/delete.html', {'issue': issue})


@login_required
def issue_detail(request, issue_id):
    issue = get_object_or_404(
        Issue.objects.select_related('created_by', 'assigned_to').prefetch_related('attachments', 'comments__author'),
        pk=issue_id,
    )
    assign_form = AssignIssueForm(instance=issue)
    attachment_form = AttachmentForm()
    return render(
        request,
        'issues/detail.html',
        {
            'issue': issue,
            'assign_form': assign_form,
            'attachment_form': attachment_form,
        },
    )


@login_required
def issue_assign(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AssignIssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def attachment_add(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            Attachment.objects.create(
                issue=issue,
                uploaded_by=request.user,
                file=form.cleaned_data['file'],
            )
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def attachment_delete(request, issue_id, attachment_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    attachment = get_object_or_404(Attachment, pk=attachment_id, issue=issue)
    if request.method == 'POST':
        attachment.file.delete(save=False)
        attachment.delete()
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def comment_add(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            Comment.objects.create(
                issue=issue,
                author=request.user,
                text=text
            )
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment.text = text
            comment.save()
        return redirect('issue_detail', issue_id=comment.issue.pk)
    return render(request, 'issues/comment_edit.html', {'comment': comment})


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    issue_id = comment.issue.pk
    if request.method == 'POST':
        comment.delete()
    return redirect('issue_detail', issue_id=issue_id)
