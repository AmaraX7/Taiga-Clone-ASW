from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def toggle_filter_url(context, param_name, param_value):
    """Returns a URL with the given filter value toggled (added or removed)."""
    request = context['request']
    params = request.GET.copy()
    current_values = params.getlist(param_name)
    str_value = str(param_value)
    if str_value in current_values:
        current_values.remove(str_value)
    else:
        current_values.append(str_value)
    params.setlist(param_name, current_values)
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'


@register.simple_tag(takes_context=True)
def is_filter_active(context, param_name, param_value):
    """Returns True if the given filter value is currently active."""
    request = context['request']
    return str(param_value) in request.GET.getlist(param_name)


@register.simple_tag(takes_context=True)
def sort_url(context, field, current_sort, current_order):
    """Returns a sort URL preserving all current GET params (filters, search)."""
    request = context['request']
    params = request.GET.copy()
    params['sort'] = field
    if current_sort == field and current_order == 'asc':
        params['order'] = 'desc'
    else:
        params['order'] = 'asc'
    return f'?{params.urlencode()}'


@register.simple_tag
def dict_get(d, key):
    """Returns d[key] or key if not found. Needed for dynamic dict lookups in templates."""
    return d.get(key, key)


@register.simple_tag(takes_context=True)
def remove_param_url(context, param_name):
    """Returns a URL with the given param removed, preserving all others."""
    request = context['request']
    params = request.GET.copy()
    if param_name in params:
        del params[param_name]
    qs = params.urlencode()
    return f'?{qs}' if qs else '?'
