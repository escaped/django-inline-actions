from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _

from inline_actions.actions import DefaultActionsMixin, ViewAction
from inline_actions.admin import InlineActionsMixin, InlineActionsModelAdminMixin

from .models import Article, Author, AuthorProxy


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


class TogglePublishActionsMixin(object):

    def get_inline_actions(self, request, obj=None):
        actions = super(TogglePublishActionsMixin, self).get_inline_actions(
            request=request, obj=obj)
        actions.append('toggle_publish')
        return actions

    def toggle_publish(self, request, obj, parent_obj=None):
        if obj.status == Article.DRAFT:
            obj.status = Article.PUBLISHED
        else:
            obj.status = Article.DRAFT

        obj.save()
        status = 'unpublished' if obj.status == Article.DRAFT else 'published'
        messages.info(request, _("Article {}.".format(status)))

    def get_toggle_publish_label(self, obj):
        label = 'publish' if obj.status == Article.DRAFT else 'unpublish'
        return 'Toggle {}'.format(label)

    def get_toggle_publish_css(self, obj):
        return (
            'button object-tools' if obj.status == Article.DRAFT else 'default')


class ArticleInline(DefaultActionsMixin,
                    UnPublishActionsMixin,
                    TogglePublishActionsMixin,
                    InlineActionsMixin,
                    admin.TabularInline):
    model = Article
    fields = ('title', 'status',)
    readonly_fields = ('title', 'status',)

    def has_add_permission(self, request):
        return False


class ArticleNoopInline(InlineActionsMixin, admin.TabularInline):
    model = Article
    fields = ('title', 'status',)
    readonly_fields = ('title', 'status',)

    def get_inline_actions(self, request, obj=None):
        actions = super(ArticleNoopInline, self).get_inline_actions(
            request=request, obj=obj)
        actions.append('noop_action')
        return actions

    def noop_action(self, request, obj, parent_obj=None):
        pass


@admin.register(AuthorProxy)
class AuthorMultipleInlinesAdmin(InlineActionsModelAdminMixin,
                                 admin.ModelAdmin):
    inlines = [ArticleInline, ArticleNoopInline]
    list_display = ('name',)
    inline_actions = None


@admin.register(Author)
class AuthorAdmin(InlineActionsModelAdminMixin,
                  admin.ModelAdmin):
    inlines = [ArticleInline]
    list_display = ('name',)
    inline_actions = None


@admin.register(Article)
class ArticleAdmin(UnPublishActionsMixin,
                   TogglePublishActionsMixin,
                   ViewAction,
                   InlineActionsModelAdminMixin,
                   admin.ModelAdmin):
    list_display = ('title', 'status', 'author')
