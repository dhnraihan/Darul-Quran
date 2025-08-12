from django import template
from django.utils.translation import gettext as _
from django.utils import timezone
from datetime import timedelta

register = template.Library()

@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        if total == 0:
            return 0
        return round((value / total) * 100, 1)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0


@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return value * arg
    except (ValueError, TypeError):
        return 0


@register.simple_tag
def get_greeting():
    """Get time-based greeting"""
    hour = timezone.now().hour
    
    if hour < 12:
        return _("Good morning")
    elif hour < 17:
        return _("Good afternoon")
    else:
        return _("Good evening")


@register.inclusion_tag('dashboard/widgets/stat_card.html')
def stat_card(title, value, icon, color='blue', change=None):
    """Render a statistics card"""
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'change': change,
    }


@register.inclusion_tag('dashboard/widgets/progress_bar.html')
def progress_bar(value, max_value=100, color='green'):
    """Render a progress bar"""
    try:
        percentage = (value / max_value) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        percentage = 0
    
    return {
        'value': value,
        'max_value': max_value,
        'percentage': percentage,
        'color': color,
    }


@register.inclusion_tag('dashboard/widgets/activity_feed.html')
def activity_feed(activities, limit=5):
    """Render activity feed"""
    return {
        'activities': activities[:limit] if activities else [],
    }


@register.simple_tag
def get_status_color(status):
    """Get color class for status"""
    status_colors = {
        'active': 'green',
        'pending': 'yellow',
        'completed': 'blue',
        'cancelled': 'red',
        'scheduled': 'purple',
    }
    return status_colors.get(status, 'gray')


@register.filter
def time_until(value):
    """Get human-readable time until a datetime"""
    if not value:
        return ''
    
    now = timezone.now()
    if isinstance(value, str):
        return value
    
    diff = value - now
    
    if diff.days > 7:
        return value.strftime('%B %d, %Y')
    elif diff.days > 0:
        return f"In {diff.days} day{'s' if diff.days > 1 else ''}"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"In {hours} hour{'s' if hours > 1 else ''}"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"In {minutes} minute{'s' if minutes > 1 else ''}"
    else:
        return "Starting soon"


@register.filter
def filter_by_day(availability_slots, day_num):
    """Filter availability slots by day of week (0-6, where 0 is Monday)"""
    if not availability_slots:
        return []
    
    try:
        day_num = int(day_num)
        return [slot for slot in availability_slots if slot.day_of_week == day_num]
    except (ValueError, AttributeError, TypeError):
        return []


@register.filter
def get_item(dictionary, key):
    """Get dictionary value by key in templates"""
    return dictionary.get(key)