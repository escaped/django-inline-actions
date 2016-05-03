from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _

from inline_actions.actions import DefaultActionsMixin
from inline_actions.admin import (InlineActionsMixin,
                                  InlineActionsModelAdminMixin)

from .models import Article, Author


class ArticleInline(DefaultActionsMixin,
                    InlineActionsMixin,
                    admin.TabularInline):
    model = Article
    fields = ('title', 'status',)
    readonly_fields = ('title', 'status',)

    def has_add_permission(self, request):
        return False

    def get_actions(self, request, obj=None):
        actions = super(ArticleInline, self).get_actions(request, obj)
        if obj:
            if obj.status == Article.DRAFT:
                actions.append('publish')
            elif obj.status == Article.PUBLISHED:
                actions.append('unpublish')
        return actions

    def publish(self, request, obj, inline_obj):
        inline_obj.status = Article.PUBLISHED
        inline_obj.save()
        messages.info(request, _("Article published."))
    publish.short_description = _("Publish")

    def unpublish(self, request, obj, inline_obj):
        inline_obj.status = Article.DRAFT
        inline_obj.save()
        messages.info(request, _("Article unpublished."))
    unpublish.short_description = _("Unpublish")


@admin.register(Author)
class AuthorAdmin(InlineActionsModelAdminMixin,
                  admin.ModelAdmin):
    inlines = [ArticleInline]
    list_display = ('name',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author')
