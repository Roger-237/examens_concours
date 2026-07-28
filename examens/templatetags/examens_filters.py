from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Filtre personnalisé pour accéder à un élément de dictionnaire par sa clé.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)
