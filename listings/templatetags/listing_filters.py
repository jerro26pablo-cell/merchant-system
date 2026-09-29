from django import template
from django.utils.html import escapejs as django_escapejs

register = template.Library()

@register.filter
def seconds_to_hours(value):
    """Convert seconds to hours (integer division)"""
    try:
        return int(value) // 3600
    except (TypeError, ValueError):
        return 0

@register.filter
def seconds_to_minutes(value):
    """Convert seconds to minutes (integer division), excluding full hours"""
    try:
        return (int(value) % 3600) // 60
    except (TypeError, ValueError):
        return 0

@register.filter
def ordinal(value):
    """Convert an integer to its ordinal representation (1st, 2nd, 3rd, etc.)"""
    try:
        value = int(value)
        if 10 <= value % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(value % 10, 'th')
        return f"{value}{suffix}"
    except (TypeError, ValueError):
        return str(value)

@register.filter
def escapejs(value):
    """Escape string for use in JavaScript"""
    return django_escapejs(value)
