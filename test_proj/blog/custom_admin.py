from django.contrib import admin

from inline_actions.actions import DefaultActionsMixin, ViewAction
from inline_actions.admin import InlineActionsMixin, InlineActionsModelAdminMixin

from .admin import (
    ChangeTitleActionsMixin,
    TogglePublishActionsMixin,
    UnPublishActionsMixin,
)
from .models import Article, AuthorProxy


class CustomAdminSite(admin.AdminSite):
    site_header = "Custom admin"
    site_title = "Custom Admin Portal"
    index_title = "Welcome to Custom Administration"


custom_admin = CustomAdminSite(name="custom_admin")


class ArticleInline(
    DefaultActionsMixin,
    UnPublishActionsMixin,
    TogglePublishActionsMixin,
    InlineActionsMixin,
    admin.TabularInline,
):
    model = Article
    fields = (
        'title',
        'status',
    )
    readonly_fields = (
        'title',
        'status',
    )

    def has_add_permission(self, request, obj=None):
        return False


class ArticleNoopInline(InlineActionsMixin, admin.TabularInline):
    model = Article
    fields = (
        'title',
        'status',
    )
    readonly_fields = (
        'title',
        'status',
    )

    def get_inline_actions(self, request, obj=None):
        actions = super(ArticleNoopInline, self).get_inline_actions(
            request=request, obj=obj
        )
        actions.append('noop_action')
        return actions

    def noop_action(self, request, obj, parent_obj=None):
        pass


@admin.register(AuthorProxy, site=custom_admin)
class AuthorMultipleInlinesAdmin(InlineActionsModelAdminMixin, admin.ModelAdmin):
    inlines = [ArticleInline, ArticleNoopInline]
    list_display = ('name',)
    inline_actions = None


@admin.register(Article, site=custom_admin)
class ArticleAdmin(
    UnPublishActionsMixin,
    TogglePublishActionsMixin,
    ChangeTitleActionsMixin,
    ViewAction,
    InlineActionsModelAdminMixin,
    admin.ModelAdmin,
):
    list_display = ('title', 'status', 'author')
