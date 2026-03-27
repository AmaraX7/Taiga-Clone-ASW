from django.shortcuts import render, redirect
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
