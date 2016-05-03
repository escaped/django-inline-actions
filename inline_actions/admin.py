from django.apps import apps
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _

from .compat import InlineAdminCompat


class InlineActionsModelAdminMixin(object):
    @property
    def media(self):
        media = super(InlineActionsModelAdminMixin, self).media
        css = {
            "all": (
                "inline_actions/css/inline_actions.css",
            )
        }
        media.add_css(css)
        return media

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        all_actions = [key for key in list(request.POST.keys())
                       if key.startswith('_action__')]

        if request.method == 'POST' and all_actions:
            assert len(all_actions) == 1
            raw_action_name = all_actions[0].replace('_action__', '', 1)

            # resolve action and target models
            action, app_label, model_name, inline_pk = raw_action_name.split('__')
            inline_model = apps.get_model(app_label=app_label,
                                          model_name=model_name)
            obj = self.get_object(request, object_id)

            # find action and execute
            for inline in self.get_inline_instances(request):
                if inline.model != inline_model:
                    continue

                # get intance while respecting the queryset of the inline
                inline_obj = inline.get_queryset(request).get(pk=inline_pk)

                # execute action
                func = getattr(inline, action, None)
                try:
                    response = func(request, obj, inline_obj)
                except TypeError:
                    pass
                else:
                    # we should receive an HttpResponse
                    if not isinstance(response, HttpResponse):
                        # otherwise redirect to the `parent` model changeform
                        url = reverse(
                            'admin:{}_{}_change'.format(
                                obj._meta.app_label,
                                obj._meta.model_name,
                            ),
                            args=(obj.pk,)
                        )
                        return redirect(url)
                    return response
            raise RuntimeError(
                "Could not find inline for model `{}` with action `{}`".format(
                    inline_model,
                    action,
                )
            )

        return super(InlineActionsModelAdminMixin, self).changeform_view(
            request, object_id, form_url, extra_context)


class InlineActionsMixin(InlineAdminCompat):
    actions = []

    def get_actions(self, request, obj=None):
        # If self.actions is explicitly set to None that means that we don't
        # want *any* actions enabled on this page.
        if self.actions is None:
            return []

        actions = []

        # Gather actions from the inline admin and all parent classes,
        # starting with self and working back up.
        for klass in self.__class__.mro()[::-1]:
            class_actions = getattr(klass, 'actions', [])
            # Avoid trying to iterate over None
            if not class_actions:
                continue

            for action in class_actions:
                if action not in actions:
                    actions.append(action)

        return actions

    def get_fields(self, request, obj=None):
        # store `request` for `get_actions`
        self.__request = request

        fields = super(InlineActionsMixin, self).get_fields(request, obj)
        fields = list(fields)
        fields.append('render_actions')
        return fields

    def get_readonly_fields(self, request, obj=None):
        fields = super(InlineActionsMixin, self).get_readonly_fields(request, obj)
        fields = list(fields)
        fields.append('render_actions')
        return fields

    def render_actions(self, obj=None):
        if not obj:
            return ''

        buttons = []
        for action_name in self.get_actions(self.__request, obj):
            action_func = getattr(self, action_name, None)
            if not action_func:
                raise RuntimeError("Could not find action `{}`".format(action_name))
            try:
                description = action_func.short_description
            except AttributeError:
                description = capfirst(action_name.replace('_', ' '))
            try:
                css_classes = action_func.css_classes
            except AttributeError:
                css_classes = ''

            # If the form is submitted, we have no information about the requested action.
            # Hence we need all data to be encoded using the action name.
            action_data = [action_name,
                           obj._meta.app_label,
                           obj._meta.model_name,
                           str(obj.pk)]
            buttons.append('<input type="submit" name="{}" value="{}" class="{}">'.format(
                '_action__{}'.format('__'.join(action_data)),
                description,
                css_classes,
            ))
        return '</p><div class="submit_row inline_actions">{}</div><p>'.format(
            ''.join(buttons)
        )
    render_actions.short_description = _("Actions")
    render_actions.allow_tags = True
