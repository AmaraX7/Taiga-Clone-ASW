from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from .models import Attachment, Comment, Issue, Watcher
from .forms import AssignIssueForm, AttachmentForm, IssueForm, IssueStatusForm
#settings
from django.contrib import messages
from django.utils.text import slugify
from .models import IssueStatus


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
        'status': [
            (str(s.id), s.name)
            for s in IssueStatus.objects.all().order_by('order')
        ],
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
        Issue.objects.select_related('created_by', 'assigned_to')
                     .prefetch_related('attachments', 'comments__author', 'watchers__user'),
        pk=issue_id,
    )
    is_watching  = issue.watchers.filter(user=request.user).exists()
    watcher_list = issue.watchers.select_related('user').all()
    assign_form = AssignIssueForm(instance=issue)
    attachment_form = AttachmentForm()
    status_form = IssueStatusForm(instance=issue)
    return render(
        request,
        'issues/detail.html',
        {
            'issue': issue,
            'assign_form': assign_form,
            'attachment_form': attachment_form,
            'status_form': status_form,
            'is_watching': is_watching,
            'watcher_list': watcher_list,
        },
    )


@login_required
def watcher_add(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        Watcher.objects.get_or_create(issue=issue, user=request.user)
    return redirect('issue_detail', issue_id=issue_id)


@login_required
def watcher_remove(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        Watcher.objects.filter(issue=issue, user=request.user).delete()
    return redirect('issue_detail', issue_id=issue_id)


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


#settings
 
 
@login_required
def settings_view(request):
    """Main settings page — lists all custom statuses."""
    # Carrega els per defecte del model si no hi ha
    if not IssueStatus.objects.exists():
        for s in IssueStatus.get_default_statuses():
            IssueStatus.objects.create(**s)
 
    statuses = IssueStatus.objects.all()
    return render(request, 'issues/settings.html', {'statuses': statuses})
 
 
@login_required
def status_create(request):
    if request.method == 'POST':
        name      = request.POST.get('name', '').strip()
        color     = request.POST.get('color', '#70728f').strip()
        is_closed = request.POST.get('is_closed') == 'on'
        if name:
            slug = slugify(name)
            # Slug ha de ser únic, anem sumant números al darrere fins que ho sigui
            base_slug, n = slug, 1
            while IssueStatus.objects.filter(slug=slug).exists():
                slug = f'{base_slug}-{n}'
                n += 1
                
            last_order = IssueStatus.objects.aggregate(Max('order'))['order__max']
            next_order = (last_order + 1) if last_order is not None else 0
            
            IssueStatus.objects.create(name=name, slug=slug, color=color, is_closed=is_closed, order=next_order)
            messages.success(request, f'Status "{name}" created.')
        else:
            messages.error(request, 'Name is required.')
    return redirect('settings_view')
 
 
@login_required
def status_edit(request, pk):
    status = get_object_or_404(IssueStatus, pk=pk)
    if request.method == 'POST':
        name      = request.POST.get('name', '').strip()
        color     = request.POST.get('color', '#70728f').strip()
        is_closed = request.POST.get('is_closed') == 'on'
        if name:
            status.name      = name
            status.color     = color
            status.is_closed = is_closed
            status.save()
            messages.success(request, f'Status "{name}" updated.')
        else:
            messages.error(request, 'Name is required.')
        return redirect('settings_view')
    return render(request, 'issues/status_edit.html', {'status': status})
 
 
@login_required
def status_delete(request, pk):
    status = get_object_or_404(IssueStatus, pk=pk)
    if request.method == 'POST':
        name = status.name
        status.delete()
        messages.success(request, f'Status "{name}" deleted.')
    return redirect('settings_view')
 
 
@login_required
def status_reorder(request):
    """Accepts a POST with ordered list of IDs and updates their `order` field."""
    if request.method == 'POST':
        ids = request.POST.getlist('order[]')
        for i, pk in enumerate(ids):
            IssueStatus.objects.filter(pk=pk).update(order=i)
    return redirect('settings_view')


@login_required
def issue_update_status(request, issue_id):
    issue = get_object_or_404(Issue, id=issue_id)

    if request.method == "POST":
        form = IssueStatusForm(request.POST, instance=issue)
        if form.is_valid():
            form.save()

    return redirect("issue_detail", issue_id=issue.id)
