from typing import Callable, List, Optional, Union

from django.apps import apps
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _


class InlineActionException(Exception):
    pass


class ActionNotCallable(InlineActionException):
    def __init__(self, model_admin, action, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_admin = model_admin
        self.action = action


class BaseInlineActionsMixin:
    INLINE_MODEL_ADMIN = 'inline'
    MODEL_ADMIN = 'admin'

    inline_actions: Optional[List[Union[str, Callable]]] = []

    def get_inline_actions(self, request, obj=None):
        """
        Returns a list of all actions for this Admin.
        """
        # If self.actions is explicitly set to None that means that we don't
        # want *any* actions enabled on this page.
        if self.inline_actions is None:
            return []

        actions = []

        # Gather actions from the inline admin and all parent classes,
        # starting with self and working back up.
        for klass in self.__class__.mro()[::-1]:
            class_actions = getattr(klass, 'inline_actions', [])
            # Avoid trying to iterate over None
            if not class_actions:
                continue

            for action in class_actions:
                if action not in actions:
                    actions.append(action)

        return actions

    def get_readonly_fields(self, request, obj=None):
        fields = super().get_readonly_fields(request, obj)
        fields = list(fields)

        if 'render_inline_actions' not in fields:
            fields.append('render_inline_actions')
        return fields

    def _get_admin_type(self, model_admin=None):
        """
        Returns wether this is an InlineAdmin or not.
        """
        model_admin = model_admin or self

        if isinstance(model_admin, admin.options.InlineModelAdmin):
            return self.INLINE_MODEL_ADMIN
        return self.MODEL_ADMIN

    def render_inline_actions(self, obj=None):  # NOQA: C901
        """
        Renders all defined inline actions as html.
        """
        if not (obj and obj.pk):
            return ''

        buttons = []
        for action_name in self.get_inline_actions(self._request, obj):
            action_func = getattr(self, action_name, None)
            if not action_func:
                raise RuntimeError("Could not find action `{}`".format(action_name))

            # Add per-object label support
            action_name = action_func.__name__
            label_handler = getattr(self, 'get_{}_label'.format(action_name), None)
            if callable(label_handler):
                description = label_handler(obj=obj)
            else:
                try:
                    description = action_func.short_description
                except AttributeError:
                    description = capfirst(action_name.replace('_', ' '))

            # Add per-object css classes support
            css_handler = getattr(self, 'get_{}_css'.format(action_name), None)
            if callable(css_handler):
                css_classes = css_handler(obj=obj)
            else:
                try:
                    css_classes = action_func.css_classes
                except AttributeError:
                    css_classes = ''

            # If the form is submitted, we have no information about the
            # requested action.
            # Hence we need all data to be encoded using the action name.
            action_data = [
                # required to distinguish between multiple inlines for the same model
                self.__class__.__name__.lower(),
                self._get_admin_type(),
                action_name,
                obj._meta.app_label,
                obj._meta.model_name,
                str(obj.pk),
            ]
            buttons.append(
                '<input type="submit" name="{}" value="{}" class="{}">'.format(
                    '_action__{}'.format('__'.join(action_data)),
                    description,
                    css_classes,
                )
            )
        return mark_safe(
            '<div class="submit_row inline_actions">{}</div>'.format(''.join(buttons))
        )

    render_inline_actions.short_description = _("Actions")  # type: ignore
    render_inline_actions.allow_tags = True  # type: ignore


class InlineActionsMixin(BaseInlineActionsMixin):
    def render_inline_actions(self, obj=None):
        html = super().render_inline_actions(obj=obj)
        # we have to add <p> tags as a workaround for invalid html
        return mark_safe('</p>{}<p>'.format(html))

    render_inline_actions.short_description = _("Actions")  # type: ignore
    render_inline_actions.allow_tags = True  # type: ignore

    def get_fields(self, request, obj=None):
        # store `request` for `get_inline_actions`
        self._request = request

        fields = super().get_fields(request, obj)
        if self.inline_actions is not None:  # is it explicitly disabled?
            fields = list(fields)
            if 'render_inline_actions' not in fields:
                fields.append('render_inline_actions')
        return fields


class InlineActionsModelAdminMixin(BaseInlineActionsMixin):
    class Media:
        css = {"all": ("inline_actions/css/inline_actions.css",)}

    def get_list_display(self, request):
        # store `request` for `get_inline_actions`
        self._request = request

        fields = super().get_list_display(request)
        if self.inline_actions is not None:  # is it explicitly disabled?
            fields = list(fields)
            if 'render_inline_actions' not in fields:
                fields.append('render_inline_actions')
        return fields

    def get_fields(self, request, obj=None):
        # store `request` for `get_inline_actions`
        self._request = request

        fields = super().get_fields(request, obj=obj)
        if not self.fields:
            # django adds all readonly fields by default
            # if `self.fields` is not defined we don't want to include
            # `render_inline_actions
            if 'render_inline_actions' in fields:
                fields.remove('render_inline_actions')
        return fields

    def _execute_action(self, request, model_admin, action, obj, parent_obj=None):
        """
        Tries to execute the requested action and returns a `HttpResponse`.

        raises
            ActionNotCallable - When action is not a function
        """
        # execute action
        func = getattr(model_admin, action, None)
        try:
            response = func(request, obj, parent_obj=parent_obj)
        except TypeError as e:
            raise ActionNotCallable(model_admin, action) from e

        # we should receive an HttpResponse
        if isinstance(response, HttpResponse):
            return response

        # otherwise redirect back
        if parent_obj is None:  # InlineActionsMixin.MODEL_ADMIN:
            # redirect to `changelist`
            url = reverse(
                'admin:{}_{}_changelist'.format(
                    obj._meta.app_label,
                    obj._meta.model_name,
                ),
            )
        else:
            # redirect to `changeform`
            url = reverse(
                'admin:{}_{}_change'.format(
                    parent_obj._meta.app_label,
                    parent_obj._meta.model_name,
                ),
                args=(parent_obj.pk,),
            )

        # readd query string
        query = request.META['QUERY_STRING'] or request.GET.urlencode()
        if query:
            url = '{}?{}'.format(url, query)

        return redirect(url)

    def _handle_action(self, request, object_id=None):
        """
        Resolve and executes the action issued by the current request.
        If no action was triggered, it does nothing.

        Returns `HttpResponse` or `None`
        """
        all_actions = [
            key for key in list(request.POST.keys()) if key.startswith('_action__')
        ]

        if request.method == 'POST' and all_actions:
            assert len(all_actions) == 1
            raw_action_name = all_actions[0].replace('_action__', '', 1)

            # resolve action and target models
            raw_action_parts = raw_action_name.split('__')
            admin_class_name, admin_type = raw_action_parts[:2]
            action, app_label, model_name, object_pk = raw_action_parts[2:]

            model = apps.get_model(app_label=app_label, model_name=model_name)
            parent_obj = self.get_object(request, object_id)

            # find action and execute
            if admin_type == self.MODEL_ADMIN:
                model_admin = self
                obj = model_admin.get_queryset(request).get(pk=object_pk)
                # parent_obj is None because `object_id` is None

            else:
                for inline in self.get_inline_instances(request):
                    inline_class_name = inline.__class__.__name__.lower()
                    matches_inline_class = inline_class_name == admin_class_name
                    matches_model = inline.model == model

                    if not matches_model or not matches_inline_class:
                        continue
                    model_admin = inline
                obj = model_admin.get_queryset(request).get(pk=object_pk)

            if model_admin:
                return self._execute_action(
                    request, model_admin, action, obj, parent_obj
                )
        return None

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        # handle requested action if required
        response = self._handle_action(request, object_id=object_id)
        if response:
            return response

        # continue normally
        return super().changeform_view(request, object_id, form_url, extra_context)

    def changelist_view(self, request, extra_context=None):
        # handle requested action if required
        response = self._handle_action(request)
        if response:
            return response

        # continue normally
        return super().changelist_view(request, extra_context)
