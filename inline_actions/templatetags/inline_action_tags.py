from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def render_inline_action_fields(context):
    """
    Render hidden fields, which are required for identifying an action.
    """
    request = context.get('request', {'POST': {}})
    all_actions = [
        key for key in list(request.POST.keys()) if key.startswith('_action__')
    ]
    if len(all_actions) == 0:
        raise RuntimeError("No inline action has been triggered.")
    if len(all_actions) > 1:
        raise RuntimeError(
            "Multiple inline actions have been triggered simultaneously."
        )

    action_key = all_actions[0]
    fields = '<input type="hidden" name="{}" value="">'.format(action_key)
    return mark_safe(fields)
