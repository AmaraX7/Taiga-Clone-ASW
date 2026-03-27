from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Attachment, Issue
from .forms import AssignIssueForm, AttachmentForm, IssueForm


def get_default_user():
    return User.objects.get(username='admin')


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


def issue_list(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'created_at')
    order = request.GET.get('order', 'desc')

    issues = Issue.objects.all()
    if q:
        issues = issues.filter(
            Q(subject__icontains=q) | Q(description__icontains=q)
        )

    if sort in SORTABLE_FIELDS:
        order_field = SORTABLE_FIELDS[sort]
        if order == 'desc':
            order_field = f'-{order_field}'
        issues = issues.order_by(order_field)

    return render(request, 'issues/list.html', {
        'issues': issues,
        'query': q,
        'current_sort': sort,
        'current_order': order,
    })


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


def issue_assign(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AssignIssueForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()
    return redirect('issue_detail', issue_id=issue.id)


def attachment_add(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            Attachment.objects.create(
                issue=issue,
                uploaded_by=get_default_user(),
                file=form.cleaned_data['file'],
            )
    return redirect('issue_detail', issue_id=issue.id)


def attachment_delete(request, issue_id, attachment_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    attachment = get_object_or_404(Attachment, pk=attachment_id, issue=issue)
    if request.method == 'POST':
        attachment.file.delete(save=False)
        attachment.delete()
    return redirect('issue_detail', issue_id=issue.id)
