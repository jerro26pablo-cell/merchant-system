from django import template

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
