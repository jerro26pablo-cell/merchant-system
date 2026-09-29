from django import template

register = template.Library()

@register.filter
def seconds_to_hours(seconds):
    """Convert seconds to hours"""
    if seconds:
        return seconds // 3600
    return 0

@register.filter
def seconds_to_minutes(seconds):
    """Convert seconds to minutes"""
    if seconds:
        return (seconds % 3600) // 60
    return 0

@register.filter
def cut(value, divisor):
    """Perform integer division"""
    if value:
        return value // divisor
    return 0
