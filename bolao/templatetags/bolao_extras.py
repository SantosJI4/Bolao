from django import template

register = template.Library()

@register.filter
def dict_item(dictionary, key):
    """Permite acessar itens de dicionário nos templates"""
    return dictionary.get(key)