import pytest
from django.contrib.admin.sites import AdminSite
from django.urls import reverse

from test_proj.blog.models import Article


@pytest.fixture
def admin_site():
    return AdminSite()


def test_for_mediafiles(admin_client, author):
    """Test weather the css is added to page."""
    url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(url)
    xpath_to_css = './/head/link[contains(@href, "inline_actions.css")]'
    assert len(changeview.lxml.xpath(xpath_to_css)) == 1


def test_actions_available(admin_client, author):
    """Test weather the action column is rendered."""
    url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(url)
    path = (
        './/div[@id="article_set-group"]//table'
        '//thead//th[starts-with(text(), "Actions")]'
    )
    assert len(changeview.lxml.xpath(path)) == 1

    url = reverse('admin:blog_author_add')
    addview = admin_client.get(url)
    assert len(addview.lxml.xpath(path)) == 1


@pytest.mark.django_db
def test_non_existing_action(admin_site, article):
    """Test for appropriate exception, when `action` is not found."""
    from test_proj.blog.admin import ArticleAdmin

    ArticleAdmin.inline_actions = ['non_existing']
    fake_request = {}

    admin = ArticleAdmin(article, admin_site)
    admin._request = fake_request

    with pytest.raises(RuntimeError):
        admin.render_inline_actions(article)

    # reset
    ArticleAdmin.inline_actions = []


@pytest.mark.django_db
def test_wrong_action_type(admin_client, article):
    """Test for appropriate exception, when the action is not callable."""
    from inline_actions.admin import ActionNotCallable
    from test_proj.blog.admin import ArticleAdmin

    admin = ArticleAdmin(article, admin_site)
    admin.inline_actions = ['property_action']
    admin.property_action = 'test'

    fake_request = {}

    with pytest.raises(ActionNotCallable):
        admin._execute_action(fake_request, admin, 'property_action', article)


def test_actions_methods_called(admin_client, mocker, article):
    """Test is all required methods are called."""
    from inline_actions.admin import InlineActionsMixin

    mocker.spy(InlineActionsMixin, 'render_inline_actions')
    mocker.spy(InlineActionsMixin, 'get_inline_actions')
    author = article.author

    url = reverse('admin:blog_author_change', args=(author.pk,))
    admin_client.get(url)

    assert InlineActionsMixin.render_inline_actions.call_count > 0
    assert InlineActionsMixin.get_inline_actions.call_count > 0


@pytest.mark.parametrize("action", ['view_action', 'publish', 'delete_action'])
def test_actions_rendered(admin_client, article, action):
    """Test wether all action buttons are rendered."""
    author = article.author

    url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(url)

    input_name = '_action__articleinline__inline__{}__blog__article__{}'.format(
        action,
        article.pk,
    )
    assert input_name in dict(changeview.form.fields)


def test_publish_action(admin_client, mocker, article):
    """Test dynamically added actions using `get_actions()`"""
    from ..admin import UnPublishActionsMixin

    mocker.spy(UnPublishActionsMixin, 'get_inline_actions')
    mocker.spy(UnPublishActionsMixin, 'publish')
    mocker.spy(UnPublishActionsMixin, 'unpublish')
    author = article.author
    assert article.status == Article.DRAFT

    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    publish_input_name = (
        '_action__articleinline__inline__publish__blog__article__{}'.format(
            article.pk,
        )
    )
    unpublish_input_name = (
        '_action__articleinline__inline__unpublish__blog__article__{}'.format(
            article.pk,
        )
    )

    # open changeform
    changeview = admin_client.get(author_url)
    assert UnPublishActionsMixin.get_inline_actions.call_count > 0
    assert publish_input_name in dict(changeview.form.fields)

    # execute and test publish action
    changeview = changeview.form.submit(name=publish_input_name).follow()
    # not available in django 1.7
    # article.refresh_from_db()
    article = Article.objects.get(pk=article.pk)
    assert publish_input_name not in dict(changeview.form.fields)
    assert unpublish_input_name in dict(changeview.form.fields)
    assert UnPublishActionsMixin.publish.call_count == 1
    assert article.status == Article.PUBLISHED

    # execute and test unpublish action
    changeview = changeview.form.submit(name=unpublish_input_name).follow()
    # article.refresh_from_db()
    article = Article.objects.get(pk=article.pk)
    assert publish_input_name in dict(changeview.form.fields)
    assert unpublish_input_name not in dict(changeview.form.fields)
    assert UnPublishActionsMixin.unpublish.call_count == 1
    assert article.status == Article.DRAFT


def test_view_action(admin_client, mocker, article):
    """Test view action."""
    from inline_actions.actions import ViewAction

    mocker.spy(ViewAction, 'view_action')
    author = article.author

    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    # execute and test view action
    input_name = (
        '_action__articleinline__inline__view_action__blog__article__{}'.format(
            article.pk,
        )
    )
    response = changeview.form.submit(name=input_name).follow()
    assert ViewAction.view_action.call_count == 1
    article_url = reverse('admin:blog_article_change', args=(article.pk,))
    assert response.request.path == article_url


def test_delete_action_without_permission(admin_client, mocker, article):
    """Delete action should not be visible without permission."""
    from ..admin import ArticleInline

    mocker.patch.object(ArticleInline, 'has_delete_permission', return_value=False)
    author = article.author

    # mock delete_permission
    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    input_name = (
        '_action__articleinline__inline__delete_action__blog__article__{}'.format(
            article.pk,
        )
    )
    assert input_name not in dict(changeview.form.fields)


def test_delete_action(admin_client, mocker, article):
    """Test delete action."""
    from inline_actions.actions import DeleteAction

    mocker.spy(DeleteAction, 'delete_action')
    author = article.author

    # mock delete_permission
    author_url = reverse('admin:blog_author_change', args=(author.pk,))
    changeview = admin_client.get(author_url)

    # execute and test delete action
    input_name = (
        '_action__articleinline__inline__delete_action__blog__article__{}'.format(
            article.pk,
        )
    )
    response = changeview.form.submit(name=input_name).follow()
    assert DeleteAction.delete_action.call_count == 1
    assert response.request.path == author_url
    with pytest.raises(Article.DoesNotExist):
        Article.objects.get(pk=article.pk)


def test_skip_rendering_actions_for_unsaved_objects(admin_client, mocker, article):
    from test_proj.blog.admin import ArticleAdmin

    unsaved_article = Article()
    admin = ArticleAdmin(unsaved_article, admin_site)

    assert admin.render_inline_actions(unsaved_article) == ''


@pytest.mark.django_db
def test_missing_render_inline_actions_from_readonly_fields(
    rf, admin_user, admin_site, article
):
    """
    Make sure that customization does not break the app.
    """
    from test_proj.blog import admin

    class ArticleAdmin(admin.InlineActionsModelAdminMixin, admin.admin.ModelAdmin):
        list_display = ('name',)
        inline_actions = None

        def get_readonly_fields(self, *args, **kwargs):
            """
            Do some fancy logic to return a list of fields, which does not include `render_inline_actions`.
            """
            return []

    request = rf.get(f'/admin/blog/articles/{article.id}/')
    request.user = admin_user

    admin = ArticleAdmin(Article, admin_site)

    # even though `render_inline_actions` is not part of the fields,
    # it should not fail :)
    admin.changeform_view(request)
