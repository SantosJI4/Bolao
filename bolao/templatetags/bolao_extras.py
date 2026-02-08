from django import template

register = template.Library()

@register.filter
def dict_item(dictionary, key):
    """Permite acessar itens de dicionário nos templates"""
    return dictionary.get(key)

@register.filter
def get_item(dictionary, key):
    """Acessa item de dicionário - alias para dict_item"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def sub(value, arg):
    """Subtrai arg de value"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0