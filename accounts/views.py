from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied

from issues.models import Issue
from .forms import ProfileEditForm

CLOSED_STATUSES = ['closed', 'rejected', 'postponed']
SORT_FIELDS = {
    'id':         'id',
    'issue_type': 'issue_type',
    'severity':   'severity',
    'status':     'status',
    'modified':   'modified_at',
}


def _sorted_issues(qs, sort_key, order):
    field = SORT_FIELDS.get(sort_key, 'id')
    if order == 'desc':
        field = f'-{field}'
    return qs.order_by(field)


@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    profile      = profile_user.profile
    is_own       = (request.user == profile_user)
    tab          = request.GET.get('tab', 'assigned')

    # Tab 1: Open Assigned Issues
    a_sort  = request.GET.get('assigned_sort', 'id')
    a_order = request.GET.get('assigned_order', 'asc')
    assigned_issues = _sorted_issues(
        Issue.objects.filter(assigned_to=profile_user).exclude(status__in=CLOSED_STATUSES),
        a_sort, a_order,
    )

    # Tab 2: Watched Issues (own profile only)
    watched_issues, w_sort, w_order = [], 'id', 'asc'
    if is_own:
        w_sort  = request.GET.get('watched_sort', 'id')
        w_order = request.GET.get('watched_order', 'asc')
        watched_issues = _sorted_issues(
            Issue.objects.filter(watchers__user=profile_user),
            w_sort, w_order,
        )

    # Tab 3: Comments (all, newest first)
    user_comments = profile_user.issue_comments.select_related('issue').order_by('-created_at')

    # Counts for sidebar stats
    open_count    = Issue.objects.filter(
        assigned_to=profile_user
    ).exclude(status__in=CLOSED_STATUSES).count()
    watched_count = profile_user.watched_issues.count() if is_own else 0
    comment_count = profile_user.issue_comments.count()

    return render(request, 'accounts/profile.html', {
        'profile_user':    profile_user,
        'profile':         profile,
        'is_own':          is_own,
        'active_tab':      tab,
        'assigned_issues': assigned_issues,
        'a_sort':          a_sort,
        'a_order':         a_order,
        'watched_issues':  watched_issues,
        'w_sort':          w_sort,
        'w_order':         w_order,
        'user_comments':   user_comments,
        'open_count':      open_count,
        'watched_count':   watched_count,
        'comment_count':   comment_count,
    })


@login_required
def profile_edit(request, username):
    if request.user.username != username:
        raise PermissionDenied
    profile = request.user.profile
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            updated = form.save(commit=False)
            if request.POST.get('use_default') == 'on':
                if profile.avatar:
                    profile.avatar.delete(save=False)
                updated.avatar = None
            updated.save()
            return redirect('profile_view', username=username)
    else:
        form = ProfileEditForm(instance=profile)
    return render(request, 'accounts/profile_edit.html', {
        'form':         form,
        'profile_user': request.user,
        'profile':      profile,
    })
