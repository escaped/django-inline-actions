from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _


class ViewAction(object):
    actions = ['view_action']

    def view_action(self, request, obj, inline_obj):
        """Redirect to changeform of selcted inline instance"""
        url = reverse(
            'admin:{}_{}_change'.format(
                inline_obj._meta.app_label,
                inline_obj._meta.model_name,
            ),
            args=(inline_obj.pk,)
        )
        return redirect(url)
    view_action.short_description = _("View")


class DeleteAction(object):
    def get_actions(self, request, obj=None):
        actions = super(DeleteAction, self).get_actions(request, obj)
        if self.has_delete_permission(request, obj):
            actions.append('delete_action')
        return actions

    def delete_action(self, request, obj, inline_obj):
        """Remove selected inline instance if permission is sufficient"""
        if self.has_delete_permission(request):
            inline_obj.delete()
            messages.info(request, "`{}` deleted.".format(inline_obj))
    delete_action.short_description = _("Delete")


class DefaultActionsMixin(ViewAction,
                          DeleteAction):
    actions = []
