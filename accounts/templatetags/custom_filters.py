from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Dictionary से value निकालने के लिए - यह आपके टेम्पलेट के लिए जरूरी है"""
    try:
        if dictionary is None:
            return None
        if hasattr(dictionary, 'get'):
            return dictionary.get(key)
        return None
    except (AttributeError, KeyError, TypeError):
        return None

@register.filter
def floatformat(value, arg='1'):
    """Number को format करने के लिए (पहले से मौजूद floatformat को ओवरराइड नहीं करता)"""
    try:
        if value is None:
            return '0'
        if arg == '1':
            return f"{float(value):.1f}"
        elif arg == '0':
            return f"{float(value):.0f}"
        elif arg == '2':
            return f"{float(value):.2f}"
        else:
            return f"{float(value):.{arg}f}"
    except (ValueError, TypeError):
        return str(value)

@register.filter
def multiply(value, arg):
    """गुणा करने के लिए"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """घटाने के लिए"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0