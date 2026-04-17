from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q, Max
from django.core.exceptions import PermissionDenied
from .models import Attachment, Comment, Issue, IssueActivity, Watcher
from .models import DueDatePreset, IssuePriority, IssueSeverity, IssueTag, IssueType
from .forms import (
    AddWatcherForm,
    AssignIssueForm,
    AttachmentForm,
    BulkIssueInsertForm,
    IssueForm,
    IssueStatusForm,
)
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
    'modified_at': 'modified_at',
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


def _add_activity(issue, actor, action, details=''):
    IssueActivity.objects.create(
        issue=issue,
        actor=actor,
        action=action,
        details=details,
    )


@login_required
def issue_list(request):
    q = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'modified_at')
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
        'type': [(opt.slug, opt.name) for opt in IssueType.objects.all()],
        'severity': [(opt.slug, opt.name) for opt in IssueSeverity.objects.all()],
        'priority': [(opt.slug, opt.name) for opt in IssuePriority.objects.all()],
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
        'status_choices': [(s.slug, s.name) for s in IssueStatus.objects.all()],
    })


@login_required
def issue_new(request):
    if request.method == 'POST':
        form = IssueForm(request.POST)
        if form.is_valid():
            issue = form.save(commit=False)
            issue.created_by = request.user
            issue.save()
            _add_activity(issue, request.user, 'created issue', issue.subject)
            return redirect('issue_list')
    else:
        form = IssueForm()
    return render(request, 'issues/new.html', {'form': form})


@login_required
def issue_edit(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if issue.created_by_id != request.user.id:
        raise PermissionDenied

    if request.method == 'POST':
        form = IssueForm(request.POST, instance=issue)
        if form.is_valid():
            updated_issue = form.save()
            _add_activity(updated_issue, request.user, 'edited issue', updated_issue.subject)
            return redirect('issue_detail', issue_id=updated_issue.id)
    else:
        form = IssueForm(instance=issue)

    return render(
        request,
        'issues/edit.html',
        {
            'form': form,
            'issue': issue,
        },
    )


@login_required
def issue_bulk_insert(request):
    if request.method == 'POST':
        form = BulkIssueInsertForm(request.POST)
        if form.is_valid():
            issues_text = form.cleaned_data['issues_text']
            selected_status = form.cleaned_data['status']
            default_status = selected_status or IssueStatus.objects.order_by('order', 'name').first()

            created_count = 0
            for raw_line in issues_text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                if '|' in line:
                    subject, description = [part.strip() for part in line.split('|', 1)]
                else:
                    subject, description = line, ''

                if not subject:
                    continue

                issue = Issue.objects.create(
                    subject=subject,
                    description=description,
                    status=default_status,
                    created_by=request.user,
                )
                _add_activity(issue, request.user, 'created issue (bulk)', issue.subject)
                created_count += 1

            messages.success(request, f'{created_count} issue(s) created by bulk insert.')
            return redirect('issue_list')
    else:
        form = BulkIssueInsertForm()

    return render(request, 'issues/bulk_insert.html', {'form': form})


@login_required
def issue_delete(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if issue.created_by_id != request.user.id:
        raise PermissionDenied
    if request.method == 'POST':
        _add_activity(issue, request.user, 'deleted issue', issue.subject)
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
    watcher_form = AddWatcherForm()
    attachment_form = AttachmentForm()
    status_form = IssueStatusForm(instance=issue)
    activities = issue.activities.select_related('actor').all()
    return render(
        request,
        'issues/detail.html',
        {
            'issue': issue,
            'assign_form': assign_form,
            'watcher_form': watcher_form,
            'attachment_form': attachment_form,
            'status_form': status_form,
            'is_watching': is_watching,
            'watcher_list': watcher_list,
            'activities': activities,
        },
    )


@login_required
def watcher_add(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AddWatcherForm(request.POST)
        if form.is_valid():
            watcher, created = Watcher.objects.get_or_create(issue=issue, user=form.cleaned_data['user'])
            if created:
                _add_activity(issue, request.user, 'added watcher', watcher.user.username)
    return redirect('issue_detail', issue_id=issue_id)


@login_required
def watcher_remove(request, issue_id, user_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        removed_user = User.objects.filter(id=user_id).first()
        Watcher.objects.filter(issue=issue, user_id=user_id).delete()
        if removed_user:
            _add_activity(issue, request.user, 'removed watcher', removed_user.username)
    return redirect('issue_detail', issue_id=issue_id)


@login_required
def issue_update_status(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        slug = request.POST.get('status')
        try:
            issue.status = IssueStatus.objects.get(slug=slug)
            issue.save()
            _add_activity(issue, request.user, 'updated status', issue.status.name)
        except IssueStatus.DoesNotExist:
            pass
    next_url = request.POST.get('next', '/')
    return redirect(next_url)


@login_required
def issue_assign(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AssignIssueForm(request.POST, instance=issue)
        if form.is_valid():
            updated_issue = form.save()
            assignee_name = updated_issue.assigned_to.username if updated_issue.assigned_to else 'Unassigned'
            _add_activity(updated_issue, request.user, 'updated assignee', assignee_name)
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def attachment_add(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = Attachment.objects.create(
                issue=issue,
                uploaded_by=request.user,
                file=form.cleaned_data['file'],
            )
            _add_activity(issue, request.user, 'added attachment', attachment.file.name)
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def attachment_delete(request, issue_id, attachment_id):
    attachment = get_object_or_404(Attachment.objects.select_related('issue'), pk=attachment_id)
    issue = attachment.issue
    if attachment.uploaded_by_id != request.user.id:
        raise PermissionDenied
    if request.method == 'POST':
        deleted_name = attachment.file.name
        attachment.file.delete(save=False)
        attachment.delete()
        _add_activity(issue, request.user, 'deleted attachment', deleted_name)
    # If a stale issue_id was posted, redirect to the real issue detail instead of 404.
    target_issue_id = issue.id if issue.id != issue_id else issue_id
    return redirect('issue_detail', issue_id=target_issue_id)


@login_required
def attachment_delete_legacy(request, attachment_id):
    attachment = get_object_or_404(Attachment.objects.select_related('issue'), pk=attachment_id)
    return attachment_delete(request, issue_id=attachment.issue_id, attachment_id=attachment_id)


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
            _add_activity(issue, request.user, 'added comment', text[:80])
    return redirect('issue_detail', issue_id=issue.id)


@login_required
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author_id != request.user.id:
        raise PermissionDenied
    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        if text:
            comment.text = text
            comment.save()
            _add_activity(comment.issue, request.user, 'edited comment', text[:80])
        return redirect('issue_detail', issue_id=comment.issue.pk)
    return render(request, 'issues/comment_edit.html', {'comment': comment})


@login_required
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    if comment.author_id != request.user.id:
        raise PermissionDenied
    issue_id = comment.issue.pk
    if request.method == 'POST':
        _add_activity(comment.issue, request.user, 'deleted comment', comment.text[:80])
        comment.delete()
    return redirect('issue_detail', issue_id=issue_id)


#settings
 
 
@login_required
def settings_view(request):
    """Main settings page — lists all configurable issue catalogs."""
    for item in IssueStatus.get_default_statuses():
        IssueStatus.objects.get_or_create(slug=item['slug'], defaults=item)
    for item in IssueType.get_defaults():
        IssueType.objects.get_or_create(slug=item['slug'], defaults=item)
    for item in IssueSeverity.get_defaults():
        IssueSeverity.objects.get_or_create(slug=item['slug'], defaults=item)
    for item in IssuePriority.get_defaults():
        IssuePriority.objects.get_or_create(slug=item['slug'], defaults=item)
    for item in DueDatePreset.get_defaults():
        DueDatePreset.objects.get_or_create(name=item['name'], defaults=item)

    context = {
        'statuses': IssueStatus.objects.all(),
        'types': IssueType.objects.all(),
        'severities': IssueSeverity.objects.all(),
        'priorities': IssuePriority.objects.all(),
        'tags': IssueTag.objects.all(),
        'due_date_presets': DueDatePreset.objects.all(),
    }
    return render(request, 'issues/settings.html', context)
 
 
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


def _catalog_model(catalog):
    catalog_map = {
        'types': IssueType,
        'severities': IssueSeverity,
        'priorities': IssuePriority,
        'tags': IssueTag,
        'due-dates': DueDatePreset,
    }
    return catalog_map.get(catalog)


@login_required
def catalog_create(request, catalog):
    model = _catalog_model(catalog)
    if not model:
        raise PermissionDenied
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        color = request.POST.get('color', '#70728f').strip()
        if model is DueDatePreset:
            days = int(request.POST.get('days_from_today', '0') or 0)
            if name and days > 0:
                last_order = model.objects.aggregate(Max('order'))['order__max']
                model.objects.create(name=name, days_from_today=days, order=(last_order + 1) if last_order is not None else 0)
        elif model is IssueTag:
            if name:
                slug = slugify(name)
                model.objects.get_or_create(name=name, defaults={'slug': slug, 'color': color})
        else:
            if name:
                slug = slugify(name)
                last_order = model.objects.aggregate(Max('order'))['order__max']
                model.objects.get_or_create(
                    slug=slug,
                    defaults={
                        'name': name,
                        'color': color,
                        'order': (last_order + 1) if last_order is not None else 0,
                    },
                )
    return redirect('settings_view')


@login_required
def catalog_edit(request, catalog, pk):
    model = _catalog_model(catalog)
    if not model:
        raise PermissionDenied
    item = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        item.name = request.POST.get('name', item.name).strip() or item.name
        if hasattr(item, 'color'):
            item.color = request.POST.get('color', item.color).strip() or item.color
        if hasattr(item, 'days_from_today'):
            item.days_from_today = int(request.POST.get('days_from_today', item.days_from_today) or item.days_from_today)
        if hasattr(item, 'slug'):
            item.slug = slugify(item.name)
        item.save()
        return redirect('settings_view')
    return render(request, 'issues/catalog_edit.html', {'item': item, 'catalog': catalog})


@login_required
def catalog_delete(request, catalog, pk):
    model = _catalog_model(catalog)
    if not model:
        raise PermissionDenied
    item = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        item.delete()
    return redirect('settings_view')

#deadline
  
@login_required
def issue_set_deadline(request, issue_id):
    issue = get_object_or_404(Issue, pk=issue_id)
    if request.method == 'POST':
        deadline_str = request.POST.get('deadline', '').strip()
        if deadline_str:
            import datetime
            try:
                issue.deadline = datetime.date.fromisoformat(deadline_str)
            except ValueError:
                pass
        else:
            issue.deadline = None
        issue.save(update_fields=['deadline'])
    return redirect('issue_detail', issue_id=issue_id)
