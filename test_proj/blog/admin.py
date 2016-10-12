from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _

from inline_actions.actions import DefaultActionsMixin, ViewAction
from inline_actions.admin import (InlineActionsMixin,
                                  InlineActionsModelAdminMixin)

from .models import Article, Author


class UnPublishActionsMixin(object):
    def get_inline_actions(self, request, obj=None):
        actions = super(UnPublishActionsMixin, self).get_inline_actions(request, obj)
        if obj:
            if obj.status == Article.DRAFT:
                actions.append('publish')
            elif obj.status == Article.PUBLISHED:
                actions.append('unpublish')
        return actions

    def publish(self, request, obj, parent_obj=None):
        obj.status = Article.PUBLISHED
        obj.save()
        messages.info(request, _("Article published."))
    publish.short_description = _("Publish")

    def unpublish(self, request, obj, parent_obj=None):
        obj.status = Article.DRAFT
        obj.save()
        messages.info(request, _("Article unpublished."))
    unpublish.short_description = _("Unpublish")


class ArticleInline(DefaultActionsMixin,
                    UnPublishActionsMixin,
                    InlineActionsMixin,
                    admin.TabularInline):
    model = Article
    fields = ('title', 'status',)
    readonly_fields = ('title', 'status',)

    def has_add_permission(self, request):
        return False


@admin.register(Author)
class AuthorAdmin(InlineActionsModelAdminMixin,
                  admin.ModelAdmin):
    inlines = [ArticleInline]
    list_display = ('name',)
    inline_actions = None


@admin.register(Article)
class ArticleAdmin(UnPublishActionsMixin,
                   ViewAction,
                   InlineActionsModelAdminMixin,
                   admin.ModelAdmin):
    list_display = ('title', 'status', 'author')
