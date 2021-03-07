from typing import Callable, List, Optional, Union

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class ViewAction:
    inline_actions: Optional[List[Union[str, Callable]]] = ['view_action']

    def view_action(self, request, obj, parent_obj=None):
        """Redirect to changeform of selcted inline instance"""
        url = reverse(
            'admin:{}_{}_change'.format(
                obj._meta.app_label,
                obj._meta.model_name,
            ),
            args=(obj.pk,),
        )
        return redirect(url)

    view_action.short_description = _("View")  # type: ignore


class DeleteAction:
    def get_inline_actions(self, request, obj=None):
        actions = super().get_inline_actions(request, obj)
        if self.has_delete_permission(request, obj):
            actions.append('delete_action')
        return actions

    def delete_action(self, request, obj, parent_obj=None):
        """Remove selected inline instance if permission is sufficient"""
        if self.has_delete_permission(request):
            obj.delete()
            messages.info(request, "`{}` deleted.".format(obj))

    delete_action.short_description = _("Delete")  # type: ignore


class DefaultActionsMixin(ViewAction, DeleteAction):
    inline_actions: Optional[List[Union[str, Callable]]] = []
